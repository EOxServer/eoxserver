#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@iguassu.cz>
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

import logging
import os.path

import mapscript

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.core.exceptions import InternalError
from eoxserver.services.interfaces import (
    ServiceHandlerInterface, VersionHandlerInterface,
    OperationHandlerInterface
)
from eoxserver.services.owscommon import (
    OWSCommonServiceHandler, OWSCommonVersionHandler, OWSCommon11ExceptionHandler
)
from eoxserver.services.ogc import OGCExceptionHandler
from eoxserver.services.mapserver import (
    gdalconst_to_imagemode, gdalconst_to_imagemode_string
)
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.ows.wcs.common import (
    WCSCommonHandler, getMSOutputFormat,
    getMSOutputFormatsAll, getMSWCSFormatMD,
    getMSWCSSRSMD, getMSWCSNativeFormat,
    getMSWCS10NativeFormat, getMSWCS10FormatMD
)

# following import is needed by WCS-T 
from eoxserver.services.ows.wcst.wcst11AlterCapabilities import wcst11AlterCapabilities11

# format registry 
from eoxserver.resources.coverages.formats import getFormatRegistry

# crs utilities 
from eoxserver.resources.coverages import crss


#==============================================================================
# WCS service handler (required by WCS 2.0 as well ) 

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

#==============================================================================
# WCS 1.x version handlers

class WCS10VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.0.0 Version Handler",
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
        
        return OGCExceptionHandler(schema_locations).handleException(req, exception)

WCS10VersionHandlerImplementation = VersionHandlerInterface.implement(WCS10VersionHandler)

class WCS11VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.1.0 Version Handler",
        "impl_id": "services.ows.wcs1x.WCS11VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0"
        }
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/1.1": "http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd"
        }
        return OWSCommon11ExceptionHandler(schemas, "1.1.0").handleException(req, exception)

WCS11VersionHandlerImplementation = VersionHandlerInterface.implement(WCS11VersionHandler)

class WCS112VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.1.2 Version Handler",
        "impl_id": "services.ows.wcs1x.WCS112VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.2"
        }
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/1.1": "http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd"
        }
        return OWSCommon11ExceptionHandler(schemas, "1.1.2").handleException(req, exception)

WCS112VersionHandlerImplementation = VersionHandlerInterface.implement(WCS112VersionHandler)

#==============================================================================
# WCS 1.x base operation handler  
    
class WCS1XOperationHandler(WCSCommonHandler):
    def createCoverages(self):
        visible_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "attr", "operands": ("visible", "=", True)}
        )
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        #NOTE: currently, we do not support referenceable grid coverages in WCS 1.X
        
        self.coverages = factory.find(
            impl_ids = (
                #"resources.coverages.wrappers.PlainCoverageWrapper",
                "resources.coverages.wrappers.RectifiedDatasetWrapper",
                "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"            
            ),
            filter_exprs=[visible_expr]
        )

    def configureMapObj(self):
        super(WCS1XOperationHandler, self).configureMapObj()

        # set all supported formats 
        for output_format in getMSOutputFormatsAll():
            self.map.appendOutputFormat(output_format)
            
    def getMapServerLayer(self, coverage):
        layer = super(WCS1XOperationHandler, self).getMapServerLayer(coverage)

        # set the detaset projection 
        layer.setProjection( crss.asProj4Str( coverage.getSRID() ))

        # set per-layer supported CRSes 
        layer.setMetaData( 'ows_srs' , getMSWCSSRSMD() ) 
        layer.setMetaData( 'wcs_srs' , getMSWCSSRSMD() ) 

        connector = System.getRegistry().findAndBind(
            intf_id = "services.mapserver.MapServerDataConnectorInterface",
            params = {
                "services.mapserver.data_structure_type": \
                    coverage.getDataStructureType()
            }
        )
        layer = connector.configure(layer, coverage)
        
        #TODO: Check why the following are set for mosaics only.
        if coverage.getType() == "eo.rect_stitched_mosaic":
            extent = coverage.getExtent()
            size_x, size_y = coverage.getSize()
            
            layer.setMetaData("wcs_extent", "%.10g %.10g %.10g %.10g" % extent)
            layer.setMetaData("wcs_resolution", "%.10g %.10g" % ((extent[2]-extent[0]) / float(size_x), (extent[3]-extent[1]) / float(size_y)))
            layer.setMetaData("wcs_size", "%d %d" % (size_x, size_y))

        # set up rangetype metadata information
        rangetype = coverage.getRangeType()
        layer.setMetaData("wcs_bandcount", "%d"%len(rangetype.bands))
        layer.setMetaData("wcs_rangeset_name", rangetype.name)
        layer.setMetaData("wcs_rangeset_label", rangetype.name)
        layer.setMetaData("wcs_rangeset_axes", ",".join(band.name for band in rangetype.bands))
        for band in rangetype.bands:
            layer.setMetaData("wcs_%s_label" % band.name, band.name)
            layer.setMetaData("wcs_%s_interval" % band.name, "%d %d" % rangetype.getAllowedValues())

        layer.setMetaData( "wcs_imagemode", gdalconst_to_imagemode_string(rangetype.data_type) )

        #set the layer's native format 
        layer.setMetaData( 'wcs_nativeformat' , getMSWCSNativeFormat(coverage.getData().getSourceFormat()) ) 

        #set the per-layer supported formats 
        layer.setMetaData( 'wcs_formats' , getMSWCSFormatMD() )
        
        return layer

#==============================================================================
# WCS 1.x common operation handlers 

class WCS1XDescribeCoverageHandler(WCS1XOperationHandler):
    def createCoverages(self):
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        obj_ids = self.req.getParamValue("coverageids")
        if obj_ids is None:
            key = self.PARAM_SCHEMA["coverageids"]["kvp_key"]
            raise InvalidRequestException("Missing required parameter '%s'." % key, "ParameterError", key)
        
        for coverage_id in obj_ids:
            coverage = factory.get(obj_id=coverage_id)

            if ( coverage is None ) or ( coverage.getType() not in ("plain",        
                           "eo.rect_dataset", "eo.rect_stitched_mosaic") ):         
                raise InvalidRequestException("No rectified coverage with id"\
                    " '%s' found."%coverage_id, "NoSuchCoverage", coverage_id)                     

            self.coverages.append(coverage)

class WCS1XGetCoverageHandler(WCS1XOperationHandler):
    def createCoverages(self):
        factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
        
        obj_id = self.req.getParamValue("coverageid")
        
        if obj_id is None:
            key = self.PARAM_SCHEMA["coverageid"]["kvp_key"]
            raise InvalidRequestException("Missing required parameter '%s.'" % key, "ParameterError", key)
        
        coverage = factory.get(obj_id=obj_id)

        if ( coverage is None ) or ( coverage.getType() not in ("plain",        
                       "eo.rect_dataset", "eo.rect_stitched_mosaic") ):         
            raise InvalidRequestException("No rectified coverage with id '%s'"\
                " found."%obj_id, "NoSuchCoverage", obj_id)                     
                                                                                
        self.coverages.append(coverage)
        
    def _setParameter(self, key, value):
        if key.lower() == "format":
            super(WCS1XGetCoverageHandler, self)._setParameter("format", "custom")
        else:
            super(WCS1XGetCoverageHandler, self)._setParameter(key, value)
            
    def configureMapObj(self):
        format_param = self.req.getParamValue("format")
        if not format_param:
            raise InvalidRequestException(
                "Missing mandatory 'format' parameter",
                "MissingParameterValue",
                "format"
            )
        
        output_format = getMSOutputFormat( format_param, self.coverages[0] )
        
        self.map.appendOutputFormat(output_format)
        self.map.setOutputFormat(output_format)
        
        super(WCS1XGetCoverageHandler, self).configureMapObj()

class WCS10GetCapabilitiesHandler(WCS1XOperationHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs1x.WCS10GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }
    
WCS10GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS10GetCapabilitiesHandler)

#==============================================================================
# WCS 1.x specific operation handlers 

class WCS11GetCapabilitiesHandler(WCS1XOperationHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.0 GetCapabilities Handler",
        "impl_id": "services.ows.wcs1x.WCS11GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getcapabilities"
        }
    }

    # GetCapabilities() response altering
    def _processRequest(self, req):

        # call the original method 
        response = WCS1XOperationHandler._processRequest( self , req ) 

        # alter the capabilities response
        response = wcst11AlterCapabilities11( response ) 

        return response 
    
WCS11GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS11GetCapabilitiesHandler)

class WCS112GetCapabilitiesHandler(WCS1XOperationHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.2 GetCapabilities Handler",
        "impl_id": "services.ows.wcs1x.WCS112GetCapabilitiesHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.2",
            "services.interfaces.operation": "getcapabilities"
        }
    }

    # GetCapabilities() response altering
    def _processRequest(self, req):

        # call the original method 
        response = WCS1XOperationHandler._processRequest( self , req ) 

        # alter the capabilities response
        response = wcst11AlterCapabilities11( response ) 

        return response 

WCS112GetCapabilitiesHandlerImplementation = OperationHandlerInterface.implement(WCS112GetCapabilitiesHandler)

class WCS10DescribeCoverageHandler(WCS1XDescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0.0 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS10DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/1.0.0}Coverage", "xml_type": "string[]", "kvp_key": "coverage", "kvp_type": "stringlist"},
    }

    # special WCS 1.0 format handling  
    def getMapServerLayer(self, coverage):
        layer = super(WCS10DescribeCoverageHandler, self).getMapServerLayer(coverage)

        layer.setMetaData( 'wcs_nativeformat' , getMSWCS10NativeFormat(coverage.getData().getSourceFormat()) ) 
        layer.setMetaData( 'wcs_formats', getMSWCS10FormatMD() ) 

        return layer
    
WCS10DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS10DescribeCoverageHandler)

class WCS11DescribeCoverageHandler(WCS1XDescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.0 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS11DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/1.1}Identifier", "xml_type": "string[]", "kvp_key": "identifier", "kvp_type": "stringlist"},
    }
    
WCS11DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS11DescribeCoverageHandler)

class WCS112DescribeCoverageHandler(WCS1XDescribeCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.2 DescribeCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS112DescribeCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.2",
            "services.interfaces.operation": "describecoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageids": {"xml_location": "/{http://www.opengis.net/wcs/1.1}Identifier", "xml_type": "string[]", "kvp_key": "identifier", "kvp_type": "stringlist"},
    }
    
WCS112DescribeCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS112DescribeCoverageHandler)

class WCS10GetCoverageHandler(WCS1XGetCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.0.0 GetCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS10GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.0.0",
            "services.interfaces.operation": "getcoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageid": {"xml_location": "/{http://www.opengis.net/wcs/1.0.0}sourceCoverage", "xml_type": "string", "kvp_key": "coverage", "kvp_type": "string"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/1.0.0}output/{http://www.opengis.net/wcs/1.0.0}format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"}
    }
    
WCS10GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS10GetCoverageHandler)

class WCS11GetCoverageHandler(WCS1XGetCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.0 GetCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS11GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.0",
            "services.interfaces.operation": "getcoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageid": {"xml_location": "/{http://www.opengis.net/ows/1.1}Identifier", "xml_type": "string", "kvp_key": "identifier", "kvp_type": "string"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/1.1}Output/@format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"}
    }
    
WCS11GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS11GetCoverageHandler)

class WCS112GetCoverageHandler(WCS1XGetCoverageHandler):
    REGISTRY_CONF = {
        "name": "WCS 1.1.2 GetCoverage Handler",
        "impl_id": "services.ows.wcs1x.WCS112GetCoverageHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1.2",
            "services.interfaces.operation": "getcoverage"
        }
    }
    
    PARAM_SCHEMA = {
        "coverageid": {"xml_location": "/{http://www.opengis.net/ows/1.1}Identifier", "xml_type": "string", "kvp_key": "identifier", "kvp_type": "string"},
        "format": {"xml_location": "/{http://www.opengis.net/wcs/1.1}Output/@format", "xml_type": "string", "kvp_key": "format", "kvp_type": "string"}
    }
    
WCS112GetCoverageHandlerImplementation = OperationHandlerInterface.implement(WCS112GetCoverageHandler)
