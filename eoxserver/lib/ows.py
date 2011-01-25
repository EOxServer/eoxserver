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

from traceback import format_exc
import logging

from django.conf import settings

from eoxserver.lib.handlers import EOxSServiceHandler, EOxSVersionHandler, EOxSRequestHandler, EOxSExceptionHandler, EOxSExceptionEncoder
from eoxserver.lib.registry import EOxSRegistry
from eoxserver.lib.requests import EOxSResponse
from eoxserver.lib.exceptions import EOxSInvalidRequestException, EOxSVersionNegotiationException
from eoxserver.lib.util import EOxSXMLEncoder, DOMElementToXML

class EOxSOWSCommonHandler(EOxSRequestHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        try:
            return EOxSOWSCommonExceptionHandler().handleException(req, exception)
        except Exception, e:
            logging.error(str(req.getParams()))
            logging.error(str(e))
            logging.error(format_exc())
            
            if settings.DEBUG:
                raise
            else:
                return EOxSResponse(
                    content = "Internal Server Error",
                    content_type = "text/plain",
                    headers = {},
                    status = 500
                )

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        service = req.getParamValue("service")
        if service is None:
            raise EOxSInvalidRequestException("Mandatory 'service' parameter missing.", "MissingParameterValue", "service")

        handler = EOxSRegistry.getServiceHandler(service)
        if handler is None:
            raise EOxSInvalidRequestException("Service '%s' not supported." % service, "InvalidParameterValue", "service")
        else:
            return handler.handle(req)

class EOxSOWSCommonServiceHandler(EOxSServiceHandler):
    ABSTRACT = True
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"},
        "acceptversions": {"xml_location": "/ows:AcceptVersions/Version", "xml_type": "string[]", "kvp_key": "acceptversions", "kvp_type": "stringlist"}
    }
    
    def _handleException(self, req, exception):
        return EOxSOWSCommonExceptionHandler().handleException(req, exception)

    def _normalizeVersion(self, input_version):
        if input_version is not None:
            version_numbers = input_version.split(".")
            
            for version_number in version_numbers:
                try:
                    int(version_number)
                except:
                    raise EOxSInvalidRequestException("'%s' is not a valid OWS version identifier." % input_version, "InvalidParameterValue", "version")
            
            if len(version_numbers) > 3:
                raise EOxSInvalidRequestException("'%s' is not a valid OWS version identifier." % input_version, "InvalidParameterValue", "version")
            elif len(version_numbers) == 3:
                return input_version
            elif len(version_numbers) == 2:
                return "%s.0" % input_version
            elif len(version_numbers) == 1:
                return "%s.0.0" % input_version
                
    def _negotiateVersionOldStyle(self, input_version):
        if input_version is None:
            return EOxSRegistry.getHighestVersion(self.SERVICE)
        else:
            nversion = self._normalizeVersion(input_version)
            
            if EOxSRegistry.versionSupported(self.SERVICE, nversion):
                return nversion
            else:
                highest_version = EOxSRegistry.getHighestVersion(self.SERVICE, lower_than=nversion)
                
                if highest_version is not None:
                    return highest_version
                else:
                    return EOxSRegistry.getLowestVersion(self.SERVICE)

    def _negotiateVersionOWSCommon(self, accept_versions):
        for accept_version in accept_versions:
            if EOxSRegistry.versionSupported(self.SERVICE, accept_version):
                return accept_version
        
        raise EOxSVersionNegotiationException("Version negotiation failed! Highest supported version: %s; Lowest supported version: %s" % (EOxSRegistry.getHighestVersion(self.SERVICE), EOxSRegistry.getLowestVersion(self.SERVICE)))
    
    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        input_version = req.getParamValue("version")
        operation = req.getParamValue("operation")
        
        if operation is None:
            raise EOxSInvalidRequestException("Missing 'request' parameter", "MissingParameterValue", "request")
        elif operation.lower() == "getcapabilities":
            accept_versions = req.getParamValue("acceptversions")
            
            if accept_versions is None:
                version = self._negotiateVersionOldStyle(input_version)
            else:
                version = self._negotiateVersionOWSCommon(accept_versions)
        else:
            if input_version is None:
                raise EOxSInvalidRequestException("Missing mandatory 'version' parameter", "MissingParameterValue", "version")
            else:
                version = input_version
        
        req.setVersion(version)
        
        handler = EOxSRegistry.getVersionHandler(self.SERVICE, version)
        if handler is None:
            raise EOxSInvalidRequestException("Service '%s', version '%s' not supported." % (self.SERVICE, version), "InvalidParameterValue", "version")
        else:
            return handler.handle(req)

class EOxSOWSCommonVersionHandler(EOxSVersionHandler):
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@ows:service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@ows:version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def _handleException(self, req, exception):
        return EOxSOWSCommonExceptionHandler().handleException(req, exception)

    def _processRequest(self, req):
        req.setSchema(self.PARAM_SCHEMA)
        
        version = req.getVersion()
        operation = req.getParamValue("operation")
        if operation is None:
            raise EOxSInvalidRequestException("Mandatory 'request' parameter missing.", "MissingParameterValue", "request")
        
        handler = EOxSRegistry.getOperationHandler(self.SERVICE, version, operation)
        if handler is None:
            raise EOxSInvalidRequestException("Service '%s', version '%s' does not support operation '%s'." % (self.SERVICE, version, operation), "OperationNotSupported", operation)
        else:
            return handler.handle(req)

class EOxSOWSCommonExceptionHandler(EOxSExceptionHandler):
    OWS_COMMON_HTTP_STATUS_CODES = {
        "_default": 400,
        "OperationNotSupported": 501,
        "OptionNotSupported": 501,
        "NoApplicableCode": 500
    }
    
    def __init__(self):
        super(EOxSOWSCommonExceptionHandler, self).__init__()
        
        self.additional_http_status_codes = {}
    
    def setHTTPStatusCodes(self, additional_http_status_codes):
        self.additional_http_status_codes = additional_http_status_codes
        
    def _filterExceptions(self, exception):
        if not isinstance(exception, EOxSInvalidRequestException) and \
           not isinstance(exception, EOxSVersionNegotiationException):
            raise
        
    def _getEncoder(self):
        return EOxSOWSCommonExceptionEncoder()
    
    def _getHTTPStatus(self, exception):
        if isinstance(exception, EOxSInvalidRequestException):
            exception_code = exception.error_code
            
            if exception_code in self.OWS_COMMON_HTTP_STATUS_CODES:
                return self.OWS_COMMON_HTTP_STATUS_CODES[exception_code]
            elif exception_code in self.additional_http_status_codes:
                return self.additional_http_status_codes[exception_code]
            else:
                return self.OWS_COMMON_HTTP_STATUS_CODES["_default"]
        elif isinstance(exception, EOxSVersionNegotiationException):
            return 400

    def _getContentType(self, exception):
        return "text/xml"

class EOxSOWSCommonExceptionEncoder(EOxSExceptionEncoder):
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
