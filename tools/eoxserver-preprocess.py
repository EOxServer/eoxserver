#!/usr/bin/python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-------------------------------------------------------------------------------

import sys
import re
import argparse
import traceback
import textwrap
from os.path import splitext
import logging

from eoxserver.core.util.timetools import getDateTime
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.processing.preprocessing.util import  check_file_existence
from eoxserver.processing.preprocessing import (
    WMSPreProcessor, RGBA, ORIG_BANDS, NativeMetadataFormatEncoder
)
from eoxserver.processing.preprocessing.format import (
    get_format_selection, GeoTIFFFormatSelection
)
from eoxserver.processing.preprocessing.georeference import (
    Extent, GCPList
)


def main(args):
    # create a parser instance
    parser = argparse.ArgumentParser(add_help=True, fromfile_prefix_chars='@',
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.description = textwrap.dedent("""\
    Takes <infile> raster data and pre-processes it into 
    <outfiles_basename>.tif, a GeoTIFF converted to RGB using default internal 
    tiling, internal overviews, no compression, and 0 as no-data value, and 
    <outfiles_basename>.xml, a EOxServer simple XML EO metadata file.

    The outfiles are ready to be used with the eoxs_register command of an 
    EOxServer instance.

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !!!Caution, you will loose data quality!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    The data quality of <outfiles_basename>.tif is most likely different from 
    <infile> because of the pre-processing applied. Reasons include 
    re-projection, compression, conversion to RGB, indexing, etc.
    
    Examples:
    
    # basic usage with no creation of metadata
    eoxserver-preprocess.py --no-metadata input.tif
    
    # basic usage with creation of metadata with specific basename
    eoxserver-preprocess.py --coverage-id=a --begin-time=2008-03-01T13:00:00Z \\ 
                            --end-time=2008-03-01T13:00:00Z input.tif output
                            
    # with RGBA band selection
    eoxserver-preprocess.py --bands 1:0:255,2:0:255,3:0:100,4 --rgba \\
                            --no-metadata input.tif

    # with DEFLATE compression and color index from a palette file
    eoxserver-preprocess.py  --compression=DEFLATE --zlevel=2 --indexed \\ 
                             --pct palette.vrt --no-metadata input.tif
    
    # (re-)setting the extent of the file
    eoxserver-preprocess.py --extent 0,0,10,10,4326 --no-metadata input.tif
    
    # Using GCPs
    eoxserver-preprocess.py --no-metadata --gcp 0,0,10,10 --gcp 2560,0,50,10 \\
                            --gcp 0,1920,10,50 --gcp 2560,1920,50,50 \\ 
                            --georef-crs 4326 input.tif
                            
    # reading arguments from a file (1 line per argument), with overrides
    eoxserver-preprocess.py @args.txt --crs=3035 --no-tiling input.tif
    """)
    
    #===========================================================================
    # Metadata parsing group
    #===========================================================================
    
    # TODO: won't work with mutual exclusive groups. Bug in Argparse?
    #md_g = parser.add_mutually_exclusive_group(required=True)
    
    #md_g.add_argument("--no-metadata", dest="generate_metadata",
    #                  action="store_false",
    #                  help="Explicitly turn off the creation of a metadata " 
    #                       "file.")
    
    #md_g_data = md_g.add_argument_group()
    
    #md_g_data.add_argument("--begin-time", dest="begin_time", 
    #                       type=_parse_datetime,
    #                       help="The ISO 8601 timestamp of the begin time.")
    #md_g_data.add_argument("--end-time", dest="end_time",
    #                       type=_parse_datetime,
    #                       help="The ISO 8601 timestamp of the end time.")
    #md_g_data.add_argument("--coverage-id", dest="coverage_id",
    #                       type=_parse_coverage_id, 
    #                       help="The ID of the coverage, must be a valid "
    #                            "NCName.")
    
    # should be mutually exclusive
    parser.add_argument("--no-metadata", dest="generate_metadata",
                        action="store_false",
                        help="Explicitly turn off the creation of a metadata " 
                             "file.")
    parser.add_argument("--begin-time", dest="begin_time", type=_parse_datetime,
                        help="The ISO 8601 timestamp of the begin time.")
    parser.add_argument("--end-time", dest="end_time", type=_parse_datetime,
                        help="The ISO 8601 timestamp of the end time.")
    parser.add_argument("--coverage-id", dest="coverage_id",
                        type=_parse_coverage_id, 
                        help="The ID of the coverage, must be a valid NCName.")
    
    #===========================================================================
    # Georeference group
    #===========================================================================
    
    georef_g = parser.add_mutually_exclusive_group()
    georef_g.add_argument("--extent", dest="extent", type=_parse_extent,
                          help="The extent of the dataset, as a 4-tuple of "
                               "floats.")
    #georef_g.add_argument("--footprint", dest="footprint", 
    #                      type=_parse_footprint,
    #                      help="The footprint of the dataset, as a Polygon WKT.")
    georef_g.add_argument("--gcp", dest="gcps", type=_parse_gcp,
                          action="append",
                          help="A Ground Control Point in the format: "
                               "'pixel,line,easting,northing[,elevation]'.")
    
    parser.add_argument("--georef-crs", dest="georef_crs")
    
    #===========================================================================
    # Arbitraries
    #===========================================================================
    
    parser.add_argument("--crs", dest="crs", type=int, 
                        help="The desired output CRS ID of the dataset.")
    parser.add_argument("--no-tiling", dest="tiling", action="store_false",
                        default=True, 
                        help="Explicitly turn of the tiling of the output "
                             "dataset.")
    parser.add_argument("--no-overviews", dest="overviews",
                        action="store_false", default=True,
                        help="Explicitly turn of the creation of overview "
                             "images of the output dataset.")
    
    #===========================================================================
    # Bands group
    #===========================================================================
    
    bands_g = parser.add_mutually_exclusive_group()
    
    bands_g.add_argument("--rgba", dest="bandmode", action="store_const",
                         const=RGBA,
                         help="Convert the image to RGBA, using the first four "
                              "bands.")
    bands_g.add_argument("--orig-bands", dest="bandmode", action="store_const",
                         const=ORIG_BANDS,
                         help="Explicitly keep all original bands.")
    
    parser.add_argument("--bands", dest="bands", type=_parse_bands, 
                        help="A comma separated list of bands with optional "
                             "subsets in the form: 'no[:low:high]'. Either "
                             "three bands, or four when --rgba is requested.")

    parser.add_argument("--footprint-alpha", dest="footprint_alpha",
                        action="store_true", default=False,
                        help="A comma separated list of bands with optional "
                             "subsets in the form: 'no[:low:high]'. Either "
                             "three bands, or four when --rgba is requested.")
    
    parser.add_argument("--compression", dest="compression",
                        choices=GeoTIFFFormatSelection.SUPPORTED_COMPRESSIONS,
                        help="The desired compression technique.")
    parser.add_argument("--jpeg-quality", dest="jpeg_quality", type=int,
                        help="The JPEG algorithm quality when JPEG compression "
                             "is requested. Default is 75.")
    parser.add_argument("--zlevel", dest="zlevel", type=int,
                        help="The zlevel quality setting when DEFLATE "
                             "compression is requested.")
    
    indexed_group = parser.add_argument_group()
    
    # TODO: pct depends on indexed
    
    parser.add_argument("--indexed", dest="color_index", action="store_true",
                        help="Create a paletted (indexed) image.")
    parser.add_argument("--pct", dest="palette_file",
                        help="Use the given file as color palette. If not "
                             "given, a new palette will be calculated.")
    
    parser.add_argument("--no-data-value", dest="no_data_value", 
                        type=_parse_nodata_values,
                        help="Either one, or a list of no-data values.")
    
    parser.add_argument("--co", dest="creation_options", type=int, 
                        action="append",
                        help="Additional GDAL dataset creation options. "
                             "See http://www.gdal.org/frmt_gtiff.html")
    
    parser.add_argument("--traceback", action="store_true", default=False)
    
    parser.add_argument("--force", "-f", dest="force", action="store_true",
                        default=False,
                        help="Override files, if they already exist.")

    parser.add_argument("--verbosity", "-v", dest="verbosity", type=int,
                        default=1,
                        help="Set the verbosity (0, 1, 2). Default is 1.")
    
    parser.add_argument("input_filename", metavar="infile", nargs=1,
                        help="The input raster file to be processed.")
    parser.add_argument("output_basename", metavar="outfiles_basename",
                        nargs="?", 
                        help="The base name of the outputfile(s) to be "
                             "generated.")
    
    values = vars(parser.parse_args(args))
    
    
    # check metadata values
    if "generate_metadata" in values and ("begin_time" in values 
                                          or "end_time" in values
                                          or "coverage_id" in values):
        parser.error("--no-metadata is mutually exclusive with --begin-time, "
                     "--end-time and --coverage-id.")

    elif "generate_metadata" not in values and not ("begin_time" in values 
                                                    and "end_time" in values
                                                    and "coverage_id" in values):
        parser.error("Enter the full metadata with --begin-time, --end-time "
                     "and --coverage-id.")
    
    # hack to flatten the list
    values["input_filename"] = values["input_filename"][0]
    
    georef_crs = values.pop("georef_crs", None)
    
    if "extent" in values:
        values["geo_reference"] = Extent(*values.pop("extent"), srid=georef_crs or 4326)
    
    if "gcps" in values:
        values["geo_reference"] = GCPList(values.pop("gcps"), georef_crs or 4326)
    
    if "palette_file" in values and not "color_index" in values:
        parser.error("--pct can only be used with --indexed")
    
    # Extract format and execution specific values
    format_values = _extract(values, ("tiling", "compression", "jpeg_quality", 
                                      "zlevel", "creation_options"))
    exec_values = _extract(values, ("input_filename", "geo_reference",
                                    "generate_metadata"))
    other_values = _extract(values, ("traceback", ))
    metadata_values = _extract(values, ("coverage_id", "begin_time",
                                         "end_time"))

    force = values.pop("force", True)
    verbosity = values.pop("verbosity")
    output_basename = values.pop("output_basename", None)
    input_filename = exec_values.get("input_filename")

    # setup logging
    if verbosity > 0:
        if verbosity == 1: level = logging.WARN
        elif verbosity == 2: level = logging.INFO
        elif verbosity >= 3: level = logging.DEBUG
        logging.basicConfig(format="%(levelname)s: %(message)s", stream=sys.stderr,
                            level=level)
        

    try:
        # create a format selection
        format_selection = get_format_selection("GTiff", **format_values)


        # TODO: make 'tif' dependant on format selection
        # check files exist
        if not output_basename:
            output_filename = splitext(input_filename)[0] + "_proc" + format_selection.extension
            output_md_filename = splitext(input_filename)[0] + "_proc.xml"
        
        else:
            output_filename = output_basename + format_selection.extension
            output_md_filename = output_basename + ".xml"

        if not force:
            check_file_existence(output_filename)

        exec_values["output_filename"] = output_filename

        # create and run the preprocessor
        preprocessor = WMSPreProcessor(format_selection, **values)
        result = preprocessor.process(**exec_values)

        if exec_values.get("generate_metadata", True):
            if not force:
                check_file_existence(output_md_filename)

            encoder = NativeMetadataFormatEncoder()
            xml = DOMElementToXML(encoder.encodeMetadata(metadata_values["coverage_id"],
                                                         metadata_values["begin_time"],
                                                         metadata_values["end_time"],
                                                         result.footprint_raw))
            
            with open(output_md_filename, "w+") as f:
                f.write(xml)
        
    except Exception as e:
        # error wrapping
        if other_values["traceback"]:
            traceback.print_exc()
        sys.stderr.write("%s: %s\n" % (type(e).__name__, str(e)))


def _parse_datetime(input_str):
    """ Helper callback function to check if a given datetime is correct.
    """
    
    try:
        getDateTime(input_str)
    except:
        raise argparse.ArgumentTypeError("Wrong datetime format. Use ISO 8601.")
        
    return input_str
    


def _parse_coverage_id(input_str):
    """ Helper callback function to check if a given coverage ID is a valid 
        NCName.
    """
    
    if not re.match(r'^[a-zA-z_][a-zA-Z0-9_.-]*$', input_str):
        raise argparse.ArgumentTypeError("The given coverage ID '%s' is not a "
                                         "valid NCName." % input_str)
    
    return input_str


def _parse_extent(input_str):
    """ Helper callback function to parse an extent.
    """
    
    parts = input_str.split(",")
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Wrong format of extent.")
    
    return map(float, parts)


def _parse_footprint(input_str):
    """ Helper callback function to parse a footprint.
    """
    # TODO: implement
    pass


def _parse_gcp(input_str):
    """ Helper callback function to parse one GCP in the form 
        "pixel,line,easting,northing[,elevation]" and transform it into a list 
        like [x,y[,z],pixel,line]
    """
    
    parts = input_str.split(",")
    
    if not (len(parts) != 4 or len(parts) != 5):
        raise argparse.ArgumentTypeError("Wrong number of arguments for GCP.")
    
    try:
        gcps = [float(part) for part in parts]
        return gcps[2:] + gcps[:2]
    except ValueError:
        raise argparse.ArgumentTypeError("Wrong format of GCP.")


def _parse_bands(input_str):
    """ Helper callback function to parse a list of selected bands given from 
        the user.
    """
    
    result = []
    
    def parse_minmax(subparts, index):
        try:
            if subparts[index] in ("min", "max"):
                return subparts[index]
            else:
                return float(subparts[index])
        except IndexError:
            return None
        except ValueError:
            raise argparse.ArgumentTypeError("Wrong format of band subset.")
    
    for part in input_str.split(","):
        subparts = part.split(":")
        
        if len(subparts) < 1 or len(subparts) > 3:
            raise argparse.ArgumentTypeError("Wrong format of band.")
        
        number = int(subparts[0])
        dmin = parse_minmax(subparts, 1)
        dmax = parse_minmax(subparts, 2)
        result.append((number, dmin, dmax))
    
    return result


def _parse_nodata_values(input_str):
    """ Helper callback function to parse no-data values. 
    """
    
    return [int(part) for part in input_str.split(",")]


def _parse_creation_options(input_str):
    """ Helper callback function to parse additional dataset creation options. 
    """
    
    return input_str.split("=")


def _extract(dct, keys):
    """ Helper function to extract a list of keys from a dict and return these
        in a new dict.
    """
    tmp = {}
    for key in keys:
        try:
            tmp[key] = dct.pop(key)
        except KeyError:
            pass
    return tmp


if __name__ == "__main__":
    main(sys.argv[1:])
