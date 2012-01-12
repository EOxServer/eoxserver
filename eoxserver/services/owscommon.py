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

import logging

from eoxserver.core.system import System
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.core.exceptions import (
    ConfigError, ImplementationNotFound, ImplementationDisabled
)
from eoxserver.core.util.xmltools import XMLEncoder
from eoxserver.services.interfaces import (
    RequestHandlerInterface, ExceptionHandlerInterface,
    ExceptionEncoderInterface
)
from eoxserver.services.base import (
    BaseRequestHandler, BaseExceptionHandler
)
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import (
    InvalidRequestException, VersionNegotiationException
)

class OWSCommonHandler(BaseRequestHandler):
    REGISTRY_CONF = {
        "name": "OWS Common base handler",
        "impl_id": "services.owscommon.OWSCommon",
        "registry_values": {}
    }
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/2.0": "http://schemas.opengis.net/ows/2.0/owsAll.xsd"
        }
        return OWSCommonExceptionHandler(schemas).handleException(req, exception)

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        service = req.getParamValue("service")
        if service is None:
            raise InvalidRequestException(
                "Mandatory 'service' parameter missing.",
                "MissingParameterValue",
                "service"
            )

        try:
            handler = System.getRegistry().findAndBind(
                intf_id = "services.interfaces.ServiceHandler",
                params = {"services.interfaces.service": service.lower()}
            )
        except ImplementationNotFound:
            raise InvalidRequestException(
                "Service '%s' not supported." % service,
                "InvalidParameterValue",
                "service"
            )
        except ImplementationDisabled:
            raise InvalidRequestException(
                "Service '%s' disabled." % service,
                "InvalidParameterValue",
                "service"
            )

        return handler.handle(req)

OWSCommonHandlerImplementation = RequestHandlerInterface.implement(OWSCommonHandler)

class OWSCommonServiceHandler(BaseRequestHandler):
    SERVICE = ""
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "acceptversions": {"xml_location": "/{http://www.opengis.net/ows/2.0}AcceptVersions/{http://www.opengis.net/ows/2.0}Version", "xml_type": "string[]", "kvp_key": "acceptversions", "kvp_type": "stringlist"}
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/2.0": "http://schemas.opengis.net/ows/2.0/owsAll.xsd"
        }
        return OWSCommonExceptionHandler(schemas).handleException(req, exception)

    def _normalizeVersion(self, input_version):
        if input_version is not None:
            version_numbers = input_version.split(".")
            
            for version_number in version_numbers:
                try:
                    int(version_number)
                except:
                    raise InvalidRequestException(
                        "'%s' is not a valid OWS version identifier." % input_version,
                        "InvalidParameterValue",
                        "version"
                    )
            
            if len(version_numbers) > 3:
                raise InvalidRequestException(
                    "'%s' is not a valid OWS version identifier." % input_version,
                    "InvalidParameterValue",
                    "version"
                )
            elif len(version_numbers) == 3:
                return input_version
            elif len(version_numbers) == 2:
                return "%s.0" % input_version
            elif len(version_numbers) == 1:
                return "%s.0.0" % input_version
    
    def _versionSupported(self, version):
        versions = System.getRegistry().getRegistryValues(
            intf_id = "services.interfaces.VersionHandler",
            registry_key = "services.interfaces.version",
            filter = {"services.interfaces.service": self.SERVICE}
        )
        
        logging.debug("OWSCommonServiceHandler._versionSupported(): versions: %s" % str(versions))
        
        return version in versions
        
    def _convertVersionNumber(self, version):
        version_list = [int(i) for i in version.split(".")]
        version_value = 0
        for i in range(0, min(3, len(version_list))):
            version_value = version_value + version_list[i] * (100**(2-i))
            
        return version_value

    def _getHighestVersion(self, lower_than=None):
        versions = System.getRegistry().getRegistryValues(
            intf_id = "services.interfaces.VersionHandler",
            registry_key = "services.interfaces.version",
            filter = {"services.interfaces.service": self.SERVICE}
        )
        
        max_version = ""
        
        for version in versions:
            if max_version:
                if lower_than and self._convertVersionNumber(version) < self._convertVersionNumber(lower_than) or not lower_than:
                    if self._convertVersionNumber(version) > self._convertVersionNumber(max_version):
                        max_version = version
            else:
                max_version = version
        
        return max_version
    
    def _getLowestVersion(self):
        versions = System.getRegistry().getRegistryValues(
            intf_id = "services.interfaces.VersionHandler",
            registry_key = "services.interfaces.version",
            filter = {"services.interfaces.service": self.SERVICE}
        )
        
        min_version = ""
        
        for version in versions:
            if min_version:
                if self._convertVersionNumber(version) < self._convertVersionNumber(min_version):
                    min_version = version
            else:
                min_version = version
        
        return min_version

    def _negotiateVersionOldStyle(self, input_version):
        if input_version is None:
            return self._getHighestVersion()
        else:
            nversion = self._normalizeVersion(input_version)
            
            if self._versionSupported(nversion):
                return nversion
            else:
                highest_version = self._getHighestVersion(lower_than=nversion)
                
                if highest_version is not None:
                    return highest_version
                else:
                    return self._getLowestVersion()

    def _negotiateVersionOWSCommon(self, accept_versions):
        for accept_version in accept_versions:
            if self._versionSupported(accept_version):
                return accept_version
        
        raise VersionNegotiationException("Version negotiation failed! Highest supported version: %s; Lowest supported version: %s" % (self._getHighestVersion(), self._getLowestVersion()))
    
    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        input_version = req.getParamValue("version")
        operation = req.getParamValue("operation")
        
        if operation is None:
            raise InvalidRequestException(
                "Missing 'request' parameter",
                "MissingParameterValue",
                "request"
            )
        elif operation.lower() == "getcapabilities":
            accept_versions = req.getParamValue("acceptversions")
            
            if accept_versions:
                version = self._negotiateVersionOWSCommon(accept_versions)
            else:
                version = self._negotiateVersionOldStyle(input_version)
        else:
            if input_version is None:
                raise InvalidRequestException(
                    "Missing mandatory 'version' parameter",
                    "MissingParameterValue",
                    "version"
                )
            else:
                version = input_version
        
        req.setVersion(version)
        
        try:
            handler = System.getRegistry().findAndBind(
                intf_id = "services.interfaces.VersionHandler",
                params = {
                    "services.interfaces.service": self.SERVICE,
                    "services.interfaces.version": version
                }
            )
        except ImplementationNotFound:
            raise InvalidRequestException(
                "Service '%s', version '%s' not supported." % (self.SERVICE, version),
                "InvalidParameterValue",
                "version"
            )

        return handler.handle(req)

class OWSCommonVersionHandler(BaseRequestHandler):
    SERVICE = ""
    VERSION = ""
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        schemas = {
            "http://www.opengis.net/ows/2.0": "http://schemas.opengis.net/ows/2.0/owsAll.xsd"
        }
        return OWSCommonExceptionHandler(schemas).handleException(req, exception)

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        version = req.getVersion()
        operation = req.getParamValue("operation")
        if operation is None:
            raise InvalidRequestException(
                "Mandatory 'request' parameter missing.",
                "MissingParameterValue",
                "request"
            )
        
        try:
            handler = System.getRegistry().findAndBind(
                intf_id = "services.interfaces.OperationHandler",
                params = {
                    "services.interfaces.service": self.SERVICE,
                    "services.interfaces.version": version,
                    "services.interfaces.operation": operation.lower()
                }
            )
        except ImplementationNotFound:
            raise InvalidRequestException(
                "Service '%s', version '%s' does not support operation '%s'." % (
                    self.SERVICE, version, operation
                ),
                "OperationNotSupported",
                operation
            )
        else:
            return handler.handle(req)

class OWSCommonExceptionHandler(BaseExceptionHandler):
    REGISTRY_CONF = {
        "name": "OWS Common Exception Handler",
        "impl_id": "services.owscommon.OWSCommonExceptionHandler", 
        "registry_values": {
            "services.interfaces.exception_scheme": "owscommon_2.0"
        }
    }
    
    OWS_COMMON_HTTP_STATUS_CODES = {
        "_default": 400,
        "OperationNotSupported": 501,
        "OptionNotSupported": 501,
        "NoApplicableCode": 500
    }
    
    def __init__(self, *args):
        super(OWSCommonExceptionHandler, self).__init__(*args)
        self.additional_http_status_codes = {}
    
    def setHTTPStatusCodes(self, additional_http_status_codes):
        self.additional_http_status_codes = additional_http_status_codes
        
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException) and \
           not isinstance(exception, VersionNegotiationException):
            raise
        
    def _getEncoder(self):
        return OWSCommonExceptionEncoder(self.schemas)
    
    def _getHTTPStatus(self, exception):
        if isinstance(exception, InvalidRequestException):
            exception_code = exception.error_code
            
            if exception_code in self.OWS_COMMON_HTTP_STATUS_CODES:
                return self.OWS_COMMON_HTTP_STATUS_CODES[exception_code]
            elif exception_code in self.additional_http_status_codes:
                return self.additional_http_status_codes[exception_code]
            else:
                return self.OWS_COMMON_HTTP_STATUS_CODES["_default"]
        elif isinstance(exception, VersionNegotiationException):
            return 400
        else:
            return 500

    def _getContentType(self, exception):
        return "text/xml"

OWSCommonExceptionHandlerImplementation = ExceptionHandlerInterface.implement(OWSCommonExceptionHandler)

class OWSCommonExceptionEncoder(XMLEncoder):
    REGISTRY_CONF = {
        "name": "OWS Common 2.0 Exception Report Encoder",
        "impl_id": "services.owscommon.OWSCommonExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "owscommon_2.0"
        }
    }
    
    def _initializeNamespaces(self):
        return {
            "ows": "http://www.opengis.net/ows/2.0",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def encodeExceptionReport(self, exception_text, exception_code, locator=None):
        if locator is None:
            element = self._makeElement("ows", "ExceptionReport", [
                ("", "@version", "2.0.0"),
                ("", "@xml:lang", "en"),
                ("ows", "Exception", [
                    ("", "@exceptionCode", exception_code),
                    ("ows", "ExceptionText", exception_text)
                ])
            ])
        else:
            element = self._makeElement("ows", "ExceptionReport", [
                ("", "@version", "2.0.0"),
                ("", "@xml:lang", "en"),
                ("ows", "Exception", [
                    ("", "@exceptionCode", exception_code),
                    ("", "@locator", locator),
                    ("ows", "ExceptionText", exception_text)
                ])
            ])
        
        if self.schemas is not None:
            schemas_location = " ".join(["%s %s"%(ns, location) for ns, location in self.schemas.iteritems()])
            element.setAttributeNS(self.ns_dict["xsi"], "%s:%s" % ("xsi", "schemaLocation"), schemas_location)
        
        return element
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code, exception.locator)
    
    def encodeVersionNegotiationException(self, exception):
        return self.encodeExceptionReport(exception.msg, "VersionNegotiationFailed")

    def encodeException(self, exception):
        return self.encodeExceptionReport("Internal Server Error", "NoApplicableCode")

OWSCommonExceptionEncoderImplementation = ExceptionEncoderInterface.implement(OWSCommonExceptionEncoder)

class OWSCommonConfigReader(object):
    REGISTRY_CONF = {
        "name": "OWS Common Config Reader",
        "impl_id": "services.owscommon.OWSCommonConfigReader",
        "registry_values": {}
    }
    
    def validate(self, config):
        if config.getInstanceConfigValue("services.owscommon", "http_service_url") is None:
            raise ConfigError("Missing mandatory 'http_service_url' parameter")
    
    def getHTTPServiceURL(self):
        return System.getConfig().getInstanceConfigValue("services.owscommon", "http_service_url")

OWSCommonConfigReaderImplementation = ConfigReaderInterface.implement(OWSCommonConfigReader)
