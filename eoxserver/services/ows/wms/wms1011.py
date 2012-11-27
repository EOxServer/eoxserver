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

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.base import BaseExceptionHandler
from eoxserver.services.interfaces import (
    ExceptionHandlerInterface, ExceptionEncoderInterface
)
from eoxserver.services.owscommon import OWSCommonVersionHandler
from eoxserver.services.ows.wms.common import WMS1XGetMapHandler

class WMS10VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Version Handler",
        "impl_id": "services.ows.wms1x.WMS10VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.0.0",
        }
    }
    
    SERVICE = "wms"
    VERSION = "1.0.0"

    def _handleException(self, req, exception):
        return WMS10ExceptionHandler().handleException(req, exception)
        
class WMS110VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.0 Version Handler",
        "impl_id": "services.ows.wms1x.WMS110VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.0"
        }
    }
    
    SERVICE = "wms"
    VERSIONS = "1.1.0"

    def _handleException(self, req, exception):
        return WMS11ExceptionHandler().handleException(req, exception)

class WMS111VersionHandler(OWSCommonVersionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1.1 Version Handler",
        "impl_id": "services.ows.wms1x.WMS111VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wms",
            "services.interfaces.version": "1.1.1"
        }
    }
    
    SERVICE = "wms"
    VERSIONS = "1.1.1"

    def _handleException(self, req, exception):
        return WMS11ExceptionHandler().handleException(req, exception)

class WMS10_11GetMapHandler(WMS1XGetMapHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "srs": {"xml_location": "/srs", "xml_type": "string", "kvp_key": "srs", "kvp_type": "string"}, # TODO: check XML location
        "layers": {"xml_location": "/layer", "xml_type": "string[]", "kvp_key": "layers", "kvp_type": "stringlist"}, # TODO: check XML location
        "time": {"xml_location": "/time", "xml_type": "string", "kvp_key": "time", "kvp_type": "string"},
        "bbox": {"xml_location": "/bbox", "xml_type": "floatlist", "kvp_key": "bbox", "kvp_type": "floatlist"}
    }
    
    def getSRSParameterName(self):
        return "srs"
    
    def configureMapObj(self):
        super(WMS10_11GetMapHandler, self).configureMapObj()
        
        self.map.setMetaData("wms_exceptions_format", "application/vnd.ogc.se_xml")
    
    def getMapServerLayer(self, layer):
        ms_layer = super(WMS10_11GetMapHandler, self).getMapServerLayer(layer)
        ms_layer.setMetaData("wms_exceptions_format","application/vnd.ogc.se_xml")
        
        return ms_layer

class WMS10ExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Handler",
        "impl_id": "services.ows.wms1x.WMS10ExceptionHandler",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.0"
        }
    }
    
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException):
            raise
    
    def _getEncoder(self):
        return WMS10ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "text/xml"

WMS10ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(WMS10ExceptionHandler)
        
class WMS10ExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Report Encoder",
        "impl_id": "services.ows.wms1x.WMS10ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.0"
        }
    }
    
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "WMTException", [
            ("", "@version", "1.0.0"),
            ("", "@@", str(exception_text))
        ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code)
    
    def encodeVersionNegotiationException(self, exception):
        return ""

    def encodeException(self, exception):
        return self.encodeExceptionReport("Internal Server Error", "NoApplicableCode")

WMS10ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS10ExceptionEncoder)

class WMS11ExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "WMS 1.1 Exception Handler",
        "impl_id": "services.ows.wms1x.WMS11ExceptionHandler",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.1"
        }
    }
    
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException):
            raise
    
    def _getEncoder(self):
        return WMS11ExceptionEncoder()
        
    def _getContentType(self, exception):
        return "application/vnd.ogc.se_xml"

WMS11ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(WMS11ExceptionHandler)

class WMS11ExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "WMS 1.0 Exception Report Encoder",
        "impl_id": "services.ows.wms1x.WMS11ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "wms_1.1"
        }
    }

    def _initializeNamespaces(self):
        return {
            "ogc": "http://www.opengis.net/ogc",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def encodeExceptionReport(self, exception_text, exception_code):
        return self._makeElement("", "ServiceExceptionReport", [
            ("", "@version", "1.1.1"),
            ("xsi", "schemaLocation", "http://www.opengis.net/ogc http://schemas.opengis.net/wms/1.1.1/OGC-exception.xsd"),
            ("", "ServiceException", [
                ("", "@code", exception_code),
                ("", "@@", exception_text)
            ])
        ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code)
    
    def encodeVersionNegotiationException(self, exception):
        return ""

    def encodeException(self, exception):
        return self.encodeExceptionReport("Internal Server Error", "NoApplicableCode")

WMS11ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(WMS11ExceptionEncoder)

