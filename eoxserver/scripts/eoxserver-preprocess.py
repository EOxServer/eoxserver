#!/usr/bin/python
#-------------------------------------------------------------------------------
# $Id: eoxserver-admin.py 827 2011-11-09 17:46:49Z meissls $
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

from eoxserver.processing.preprocess import (
    WMSPreProcessor, FormatSelection, SUPPORTED_COMPRESSIONS
)
from eoxserver.core.util.timetools import getDateTime


def main(args):
    # create a parser instance
    parser = argparse.ArgumentParser(add_help=True, fromfile_prefix_chars='@',
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.description = ("""\
    Takes <infile> raster data and pre-processes it into <outfiles_basename>.tif, a 
    GeoTIFF converted to RGB using default internal tiling, internal overviews, 
    no compression, and 0 as no-data value, and <outfiles_basename>.xml, a 
    EOxServer simple XML EO metadata file.

    The outfiles are ready to be used with the eoxs_register command of an 
    EOxServer instance.

    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    !!!Caution, you will loose data quality!!!
    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    The data quality of <outfiles_basename>.tif is most likely different from 
    <infile> because of the pre-processing applied. Reasons include 
    re-projection, compression, conversion to RGB, indexing, etc.""")
    
    #===========================================================================
    # Metadata parsing group
    #===========================================================================
    
    # TODO: won't work with mutual exclusive groups. Bug in Argparse?
    #md_group = parser.add_mutually_exclusive_group(required=True)
    #md_group.add_argument("--no-metadata", dest="metadata", action="store_false", default=True)
    #md_group_data = md_group.add_argument_group("metadata")
    #md_group_data.add_argument("--begin-time", dest="begin_time")
    #md_group_data.add_argument("--end-time", dest="end_time")
    #md_group_data.add_argument("--coverage-id", dest="coverage_id")
    
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
    georef_g.add_argument("--extent", dest="geo_reference", type=_parse_extent,
                          help="The extent of the dataset, as a 4-tuple of floats.")
    georef_g.add_argument("--footprint", dest="geo_reference", 
                          type=_parse_footprint,
                          help="The footprint of the dataset, as a Polygon WKT.")
    georef_g.add_argument("--gcp", dest="geo_reference", type=_parse_gcp,
                          action="append",
                          help="A Ground Control Point in the format: "
                               "'pixel,line,easting,northing[,elevation]'.")
    
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
    bands_g.add_argument("--orig-bands", dest="orig_bands", action="store_true",
                         help="Explicitly keep all original bands.")
    bands_g.add_argument("--rgba", dest="rgba", action="store_true",
                         help="Convert the image to RGBA, using the first four "
                              "bands.")
    bands_g.add_argument("--bands", dest="bands", type=_parse_bands, 
                         help="A comma separated list of bands with optional "
                              "subsets in the form: 'no[:low:high]'.")
    
    parser.add_argument("--compression", dest="compression",
                        choices=SUPPORTED_COMPRESSIONS,
                        help="The desired compression technique.")
    parser.add_argument("--jpeg-quality", dest="jpeg_quality", type=int,
                        help="The JPEG algorithm quality when JPEG compression "
                             "is requested. Default is 75.")
    parser.add_argument("--zlevel", dest="zlevel", type=int,
                        help="The zlevel quality setting when DEFLATE "
                             "compression is requested.")
    
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
    
    
    # TODO: config from file
    
    
    parser.add_argument("--force", "-f", dest="force", action="store_true",
                        help="Override files, if they already exist.")
    
    # TODO input and output file
    parser.add_argument("input_filename", metavar="infile", nargs=1,
                        help="The input raster file to be processed.")
    parser.add_argument("output_filename", metavar="outfiles_basename",
                        nargs="?", 
                        help="The base name of the outputfile(s) to be "
                             "generated.")
    
    values = vars(parser.parse_args(args))
    print values
    
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
    
    def extract(dct, keys):
        tmp = {}
        for key in keys:
            try:
                tmp[key] = dct.pop(key)
            except KeyError:
                pass
        return tmp
    
    # Extract format and execution specific values
    format_values = extract(values, ("tiling", "compression", "jpeg_quality", 
                                     "zlevel", "creation_options"))
    exec_values = extract(values, ("input_filename", "output_filename",
                                   "geo_reference", "generate_metadata"))
    
    # create a format selection
    format_selection = FormatSelection(**format_values)
    
    # create and run the preprocessor
    preprocessor = WMSPreProcessor(format_selection, **values)
    preprocessor.process(**exec_values)


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
    if not 5 <= len(parts) <= 4: 
        raise argparse.ArgumentTypeError("Wrong format of extent.")
    
    coords = map(float, parts[:4])
    
    if len(parts) == 5: coords.append(int(parts[4]))
    return coords


def _parse_footprint(input_str):
    # TODO: implement
    pass


def _parse_gcp(input_str):
    # TODO: implement
    pass


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


def _parse_nodata_values(x):
    # TODO: implement 
    pass


def _parse_creation_options(input_str):
    """ Helper callback function to parse additional dataset creation options. 
    """
    
    return input_str.split("=")


if __name__ == "__main__":
    main(sys.argv[1:])
