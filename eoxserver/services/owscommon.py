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

from traceback import format_exc
import logging

from django.conf import settings

from eoxserver.core.system import System
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.core.exceptions import (
    ConfigError, ImplementationNotFound
)
from eoxserver.core.util.xmltools import XMLEncoder, DOMElementToXML
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
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        try:
            return OWSCommonExceptionHandler().handleException(req, exception)
        except Exception, e:
            logging.error(str(req.getParams()))
            logging.error(str(e))
            logging.error(format_exc())
            
            if settings.DEBUG:
                raise
            else:
                return Response(
                    content = "Internal Server Error",
                    content_type = "text/plain",
                    headers = {},
                    status = 500
                )

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
        except ImplementationNotFound, e:
            raise InvalidRequestException(
                "Service '%s' not supported." % service,
                "InvalidParameterValue",
                "service"
            )

        return handler.handle(req)

OWSCommonHandlerImplementation = RequestHandlerInterface.implement(OWSCommonHandler)

class OWSCommonServiceHandler(BaseRequestHandler):
    SERVICE = ""
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "acceptversions": {"xml_location": "/ows:AcceptVersions/Version", "xml_type": "string[]", "kvp_key": "acceptversions", "kvp_type": "stringlist"}
    }
    
    def _handleException(self, req, exception):
        return OWSCommonExceptionHandler().handleException(req, exception)

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
            
            if accept_versions is None:
                version = self._negotiateVersionOldStyle(input_version)
            else:
                version = self._negotiateVersionOWSCommon(accept_versions)
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
        except ImplementationNotFound, e:
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
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        return OWSCommonExceptionHandler().handleException(req, exception)

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
        except ImplementationNotFound, e:
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
    
    def __init__(self):
        super(OWSCommonExceptionHandler, self).__init__()
        
        self.additional_http_status_codes = {}
    
    def setHTTPStatusCodes(self, additional_http_status_codes):
        self.additional_http_status_codes = additional_http_status_codes
        
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException) and \
           not isinstance(exception, VersionNegotiationException):
            raise
        
    def _getEncoder(self):
        return OWSCommonExceptionEncoder()
    
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
        return {"ows": "http://www.opengis.net/ows/2.0"}
    
    def encodeExceptionReport(self, exception_text, exception_code, locator=None):
        if locator is None:
            return self._makeElement("ows", "ExceptionReport", [
                ("", "@version", "2.0.0"),
                ("", "@xml:lang", "en"),
                ("ows", "Exception", [
                    ("", "@exceptionCode", exception_code),
                    ("ows", "ExceptionText", exception_text)
                ])
            ])
        else:
            return self._makeElement("ows", "ExceptionReport", [
                ("", "@version", "2.0.0"),
                ("", "@xml:lang", "en"),
                ("ows", "Exception", [
                    ("", "@exceptionCode", exception_code),
                    ("", "@locator", locator),
                    ("ows", "ExceptionText", exception_text)
                ])
            ])
    
    def encodeInvalidRequestException(self, exception):
        return self.encodeExceptionReport(exception.msg, exception.error_code, exception.locator)
    
    def encodeVersionNegotiationException(self, exception):
        return self.encodeExceptionReport(exception.msg, "VersionNegotiationFailed")

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
