#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
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

import mapscript

import logging

from urllib import unquote

from eoxserver.services.mapserver import (
    MapServerOperationHandler, gdalconst_to_imagemode
)
from eoxserver.services.exceptions import InvalidRequestException

class WCSCommonHandler(MapServerOperationHandler):
    def getMapServerLayer(self, coverage):
        layer = super(WCSCommonHandler, self).getMapServerLayer(coverage)

        extent = coverage.getExtent()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wcs_resolution", "%.10f %.10f" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID())) # TODO: What about additional SRSs?
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent())
        
        return layer

def get_output_format(format_param, coverage):
    FORMAT_SETTINGS = {
        "image/tiff": {
            "driver": "GDAL/GTiff",
            "mimetype": "image/tiff",
            "extension": "tif"
        },
        "image/jp2": {
            "driver": "GDAL/JPEG2000",
            "mimetype": "image/jp2",
            "extension": "jp2"
        },
        "application/x-netcdf": {
            "driver": "GDAL/netCDF",
            "mimetype": "application/x-netcdf",
            "extension": "nc"
        },
        "application/x-hdf": {
            "driver": "GDAL/HDF4Image",
            "mimetype": "application/x-hdf",
            "extension": "hdf"
        }
    }
    
    mime_type, format_options = parse_format_param(format_param)
    
    if mime_type in FORMAT_SETTINGS:
        settings = FORMAT_SETTINGS[mime_type]
    else:
        raise InvalidRequestException(
            "Unsupported format '%s'. Known formats: %s" % (
                mime_type,
                ", ".join(FORMAT_SETTINGS.keys())
            ),
            "InvalidParameterValue",
            "format"
        )
    
    output_format = mapscript.outputFormatObj(settings["driver"], "custom")
    output_format.mimetype = settings["mimetype"]
    output_format.extension = settings["extension"]
    
    rangetype = coverage.getRangeType()
    
    output_format.imagemode = gdalconst_to_imagemode(rangetype.data_type)
    
    for format_option in format_options:
        key, value = format_option.split("=")
        
        output_format.setOption(str(key), str(value))
    
    return output_format

def parse_format_param(format_param):
    parts = unquote(format_param).split(";")
    
    mime_type = parts[0]
    
    format_options = parts[1:]

    return (mime_type, format_options)
