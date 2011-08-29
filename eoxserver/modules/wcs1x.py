#-----------------------------------------------------------------------
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

import os.path

import logging

from eoxserver.modules.wcs.common import EOxSWCSCommonHandler
from eoxserver.lib.interfaces import EOxSCoverageInterfaceFactory
from eoxserver.lib.ows import EOxSOWSCommonServiceHandler, EOxSOWSCommonVersionHandler
from eoxserver.lib.ogc import EOxSOGCExceptionHandler
from eoxserver.lib.util import DOMElementToXML
from eoxserver.lib.exceptions import EOxSInternalError, EOxSInvalidRequestException

class EOxSWCSServiceHandler(EOxSOWSCommonServiceHandler):
    SERVICE = "WCS"
    ABSTRACT = False

class EOxSWCS10VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WCS"
    VERSIONS = ("1.0", "1.0.0")
    ABSTRACT = False
    
    def _handleException(self, req, exception):
        return EOxSOGCExceptionHandler().handleException(req, exception)

class EOxSWCS11VersionHandler(EOxSOWSCommonVersionHandler):
    SERVICE = "WCS"
    VERSIONS = ("1.1", "1.1.0")
    ABSTRACT = False

class EOxSWCS1XOperationHandler(EOxSWCSCommonHandler):
    SERVICE = "WCS"
    VERSIONS = ("1.0", "1.0.0", "1.1", "1.1.0")
    OPERATIONS = ("getcapabilities", "describecoverage", "getcoverage")
    ABSTRACT = False
    
    def createCoverages(self, ms_req):
        for coverage in EOxSCoverageInterfaceFactory.getVisibleCoverageInterfaces():
            if coverage.getType() in ("file", "eo.rect_dataset", "eo.rect_mosaic"):
                ms_req.coverages.append(coverage)

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(EOxSWCS1XOperationHandler, self).getMapServerLayer(coverage, **kwargs)
        
        if coverage.getType() in ("file", "eo.rect_dataset"):

            datasets = coverage.getDatasets()
            
            if len(datasets) == 0:
                raise EOxSInvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
            elif len(datasets) == 1:
                layer.data = os.path.abspath(datasets[0].getFilename())
            else:
                raise EOxSInternalError("A single file or EO dataset should never return more than one dataset.")
            
            layer.setProjection("+init=epsg:%d" % coverage.getGrid().srid)

        elif coverage.getType() == "eo.rect_mosaic":
            
            layer.tileindex = os.path.abspath(coverage.getShapeFilePath())
            layer.tileitem = "location"
            
            grid = coverage.getGrid()
            
            layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % grid.getExtent2D())
            layer.setMetaData("wcs_resolution", "%.10f %.10f" % (grid.offsets[0][0], grid.offsets[1][1]))
            layer.setMetaData("wcs_size", "%d %d" % (grid.high[0] - grid.low[0] + 1, grid.high[1] - grid.low[1] + 1))
            layer.setMetaData("wcs_nativeformat", "GTiff")
            layer.setMetaData("wcs_bandcount", "3")
        
        return layer
