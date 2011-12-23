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

import os.path

import mapscript

import logging

from eoxserver.services.mapserver import MapServerOperationHandler

class WCSCommonHandler(MapServerOperationHandler):
    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCSCommonHandler, self).getMapServerLayer(coverage, **kwargs)

        extent = coverage.getExtent()
        srid = coverage.getSRID()
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
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID())) # TODO: What about additional SRSs?; TODO: getSRID is defined for rectified coverages only
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent()) # TODO: getExtent is defined for rectified coverages only
        
        return layer
