import sys
import argparse

from eoxserver.processing.preprocess import (
    WMSPreProcessor, FormatSelection, SUPPORTED_COMPRESSIONS
)
#from eoxserver.resources.coverages.models import NCNameValidator

def main(args):
    parser = argparse.ArgumentParser(add_help=True, argument_default=argparse.SUPPRESS)
    
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
                        action="store_false", default=True)
    parser.add_argument("--begin-time", dest="begin_time") # TODO: try parse time
    parser.add_argument("--end-time", dest="end_time")
    parser.add_argument("--coverage-id", dest="coverage_id",
                        type=_parse_coverage_id)
    
    #===========================================================================
    # Georeference group
    #===========================================================================
    
    georef_group = parser.add_mutually_exclusive_group()
    georef_group.add_argument("--extent", dest="geo_reference", type=_parse_extent)
    georef_group.add_argument("--footprint", dest="geo_reference", type=_parse_footprint)
    georef_group.add_argument("--gcp", dest="geo_reference", type=_parse_gcp, action="append")
    
    #===========================================================================
    # Arbitraries
    #===========================================================================
    
    parser.add_argument("--crs", dest="crs", type=int)
    parser.add_argument("--no-tiling", dest="tiling", action="store_false", default=True)
    parser.add_argument("--no-overviews", dest="overviews", action="store_false", default=True)
    
    #===========================================================================
    # Bands group
    #===========================================================================
    
    bands_group = parser.add_mutually_exclusive_group()
    bands_group.add_argument("--orig-bands", dest="orig_bands", action="store_true")
    bands_group.add_argument("--rgba", dest="rgba", action="store_true")
    bands_group.add_argument("--bands", dest="bands", type=_parse_bands)
    
    parser.add_argument("--compression", dest="compression", choices=SUPPORTED_COMPRESSIONS)
    
    parser.add_argument("--indexed", dest="color_index", action="store_true")
    parser.add_argument("--pct", dest="palette_file")
    
    parser.add_argument("--no-data", dest="no_data_value", type=int)
    
    parser.add_argument("--co", dest="creation_options", type=int)
    
    
    # TODO: config from file
    
    
    parser.add_argument("--force", "-f", dest="force", action="store_true")
    
    # TODO input and output file
    parser.add_argument("input_filename", metavar="infile", nargs=1)
    parser.add_argument("output_filename", metavar="outfiles_basename", nargs="?")
    
    values = vars(parser.parse_args(args))
    
    print values
    
    if "generate_metadata" in values and ("begin_time" in values or "end_time" in values or "coverage_id" in values):
        parser.error("--no-metadata is mutually exclusive with --begin-time, "
                     "--end-time and --coverage-id.")

    elif "generate_metadata" not in values \
        and not ("begin_time" in values and "end_time" in values and "coverage_id" in values):
        parser.error("It is required to pass the full metadata via "
                     "--begin-time, --end-time and --coverage-id.")
    
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
    
    format_values = extract(values, ("tiling", "compression", "jpeg_quality", "zlevel", "creation_options"))
    exec_values = extract(values, ("input_filename", "output_filename", "geo_reference", "generate_metadata"))
    
    format_selection = FormatSelection(**format_values)
    
    preprocessor = WMSPreProcessor(format_selection, **values)
    preprocessor.process(**exec_values)
    

def _parse_coverage_id(input_str):
    NCNameValidator(input_str)
    return input_str

def _parse_extent(input_str):
    pass

def _parse_footprint(input_str):
    pass

def _parse_gcp(input_str):
    pass

def _parse_bands(input_str):
    # TODO: implement
    pass


def _parse_creation_options(input_str):
    pass


if __name__ == "__main__":
    main(sys.argv[1:])
