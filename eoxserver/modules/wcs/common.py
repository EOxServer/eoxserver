#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import logging

import os.path

from eoxserver.lib.handlers import EOxSMapServerOperationHandler

from eoxserver.contrib import mapscript

class EOxSWCSCommonHandler(EOxSMapServerOperationHandler):
    ABSTRACT = True

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWCSCommonHandler, self).getMapServerLayer(coverage, **kwargs)
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getGrid().srid)) # TODO: What about additional SRSs?
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getGrid().getExtent2D())
        
        return layer
