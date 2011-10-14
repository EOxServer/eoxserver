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

import logging

from eoxserver.core.system import System

from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.core.exceptions import InternalError
from eoxserver.contrib import mapscript
from eoxserver.services.interfaces import (
    ServiceHandlerInterface, VersionHandlerInterface,
    OperationHandlerInterface
)
from eoxserver.services.owscommon import (
    OWSCommonServiceHandler, OWSCommonVersionHandler
)
from eoxserver.services.ogc import OGCExceptionHandler
from eoxserver.services.mapserver import (
    gdalconst_to_imagemode, gdalconst_to_imagemode_string
)
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.ows.wcs.common import WCSCommonHandler

class WCSServiceHandler(OWSCommonServiceHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS Service Handler",
        "impl_id": "services.ows.wcs1x.WCSServiceHandler",
        "registry_values": {
            "services.interfaces.service": "wcs"
        }
    }

WCSServiceHandlerImplementation = ServiceHandlerInterface.implement(WCSServiceHandler)

class WCS10VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.0 Version Handler",
        "impl_id": "services.ows.wcs1x.WCS10VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0"
        }
    }
    
    def _handleException(self, req, exception):
        schema_locations = {
            "http://www.opengis.net/ogc": "http://schemas.opengis.net/wcs/1.0.0/OGC-exception.xsd"
        }
        
        return OGCExceptionHandler().handleException(req, exception, schema_locations)

WCS10VersionHandlerImplementation = VersionHandlerInterface.implement(WCS10VersionHandler)

class WCS11VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.1 Version Handler",
        "impl_id": "services.ows.wcs1x.WCS11VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0"
        }
    }

WCS11VersionHandlerImplementation = VersionHandlerInterface.implement(WCS11VersionHandler)
    
class WCS1XOperationHandler(WCSCommonHandler):
    def createCoverages(self, ms_req):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        for coverage in factory.find(filter_exprs=[visible_expr]):
            if coverage.getType() in ("plain", "eo.rect_dataset", "eo.rect_stitched_mosaic"):
                ms_req.coverages.append(coverage)

    def getMapServerLayer(self, coverage, **kwargs):
        layer = super(WCS1XOperationHandler, self).getMapServerLayer(coverage, **kwargs)
        
        layer.setProjection("+init=epsg:%d" % coverage.getSRID())
        
        if coverage.getType() in ("plain", "eo.rect_dataset"):
            datasets = coverage.getDatasets()
            
            if len(datasets) == 0:
                raise InvalidRequestException("Image extent does not intersect with desired region.", "ExtentError", "extent") # TODO: check if this is the right exception report
            elif len(datasets) == 1:
                connector = System.getRegistry().findAndBind(
                    intf_id = "services.mapserver.MapServerDataConnectorInterface",
                    params = {
                        "services.mapserver.data_structure_type": \
                            coverage.getDataStructureType()
                    }
                ) 
                layer = connector.configure(layer, coverage)
            else:
                raise InternalError("A single file or EO dataset should never return more than one dataset.")
            
        elif coverage.getType() == "eo.rect_stitched_mosaic":
            connector = System.getRegistry().findAndBind(
                intf_id = "services.mapserver.MapServerDataConnectorInterface",
                params = {
                    "services.mapserver.data_structure_type": \
                        coverage.getDataStructureType()
                }
            ) 
            layer = connector.configure(layer, coverage)
            
            extent = coverage.getExtent()
            size_x, size_y = coverage.getSize()
            
            layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
            layer.setMetaData("wcs_resolution", "%.10f %.10f" % ((extent[2]-extent[0]) / float(size_x), (extent[3]-extent[1]) / float(size_y)))
            layer.setMetaData("wcs_size", "%d %d" % (size_x, size_y))
            layer.setMetaData("wcs_nativeformat", "GTiff")

        # set up rangetype metadata information
        rangetype = coverage.getRangeType()
        layer.setMetaData("wcs_bandcount", "%d"%len(rangetype.bands))
        layer.setMetaData("wcs_rangeset_name", rangetype.name)
        layer.setMetaData("wcs_rangeset_label", rangetype.name)
        layer.setMetaData("wcs_rangeset_axes", ",".join(band.name for band in rangetype.bands))
        for band in rangetype.bands:
            layer.setMetaData("wcs_%s_label" % band.name, band.name)
            layer.setMetaData("wcs_%s_interval" % band.name, "%d %d" % rangetype.getAllowedValues())

        layer.setMetaData("wcs_nativeformat", "GTiff") # TODO: make this configurable like in the line above

        layer.setMetaData("wcs_formats", "GTiff GTiff_")
        layer.setMetaData(
            "wcs_imagemode", 
            gdalconst_to_imagemode_string(rangetype.data_type)
        )
        
        return layer

class WCS1XDescribeCoverageHandler(WCS1XOperationHandler):
    def createCoverages(self, ms_req):
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        obj_ids = ms_req.getParamValue("coverageids")
        if obj_ids is None:
            key = self.PARAM_SCHEMA["coverageids"]["kvp_key"]
            raise InvalidRequestException("Missing required parameter '%s'." % key, "ParameterError", key)
        
        for coverage_id in obj_ids:
            coverage = factory.get(obj_id=coverage_id)
            
            if coverage.getType() in ("plain", "eo.rect_dataset", "eo.rect_stitched_mosaic"):
                ms_req.coverages.append(coverage)
        
class WCS1XGetCoverageHandler(WCS1XOperationHandler):
    def createCoverages(self, ms_req):
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        obj_id = ms_req.getParamValue("coverageid")
        
        if obj_id is None:
            key = self.PARAM_SCHEMA["coverageid"]["kvp_key"]
            raise InvalidRequestException("Missing required parameter '%s.'" % key, "ParameterError", key)
        
        coverage = factory.get(obj_id=obj_id)
        
        if coverage.getType() in ("plain", "eo.rect_dataset", "eo.rect_stitched_mosaic"):
            ms_req.coverages.append(coverage)
    
    def _setParameter(self, ms_req, key, value):
        if key.lower() == "format" and len(ms_req.coverages[0].getRangeType().bands) > 3:
            raise
            if value.lower() == "image/tiff":
                super(WCS1XOperationHandler, self)._setParameter(ms_req, "format", "GTiff_")
            else:
                raise InvalidRequestException("Format '%s' is not allowed in coverages with more than three bands." % value, "InvalidParameterValue", key)
        else:
            super(WCS1XGetCoverageHandler, self)._setParameter(ms_req, key, value)
            
    def configureMapObj(self, ms_req):
        super(WCS1XOperationHandler, self).configureMapObj(ms_req)
        
        output_format = mapscript.outputFormatObj("GDAL/GTiff", "GTiff_")
        output_format.mimetype = "image/tiff"
        output_format.extension = "tif"
        
        output_format.imagemode = gdalconst_to_imagemode(
            ms_req.coverages[0].getRangeType().data_type
        )
        
        ms_req.map.appendOutputFormat(output_format)
        ms_req.map.setOutputFormat(output_format)
        
        logging.debug("WCS20GetCoverageHandler.configureMapObj: %s" % ms_req.map.imagetype)

class WCS10GetCapabilitiesHandler(WCS1XOperationHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs1x.WCS10GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }
    
WCS10GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS10GetCapabilitiesHandler)

class WCS11GetCapabilitiesHandler(WCS1XOperationHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1 GetCapabilities Handler",
        "impl_id": "services.ows.wcs1x.WCS11GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }
    
WCS11GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS11GetCapabilitiesHandler)

class WCS10DescribeCoverageHandler(WCS1XDescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS10DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverage", "kvp_type": "stringlist"},
    }
    
WCS10DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS10DescribeCoverageHandler)

class WCS11DescribeCoverageHandler(WCS1XDescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS11DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "identifier", "kvp_type": "stringlist"},
    }
    
WCS11DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS11DescribeCoverageHandler)

class WCS10GetCoverageHandler(WCS1XGetCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0 GetCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS10GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getcoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "coverage", "kvp_type": "string"},
    }
    
WCS10GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS10GetCoverageHandler)


class WCS11GetCoverageHandler(WCS1XGetCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1 GetCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS11GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getcoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/2.0}CoverageId", "xml_type": "string", "kvp_key": "identifier", "kvp_type": "string"},
    }
    
WCS11GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS11GetCoverageHandler)
