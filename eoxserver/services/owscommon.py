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
from eoxserver.services.exceptions import (
    InvalidRequestException, VersionNegotiationException
)


logger = logging.getLogger(__name__)

class OWSCommonHandler(BaseRequestHandler):
    """
    This class is the entry point for all incoming OWS requests.
    
    It tries to determine the service the request and directed to and
    invokes the appropriate service handler. An :exc:`~.InvalidRequestException`
    is raised if the service is unknown.
    
    Due to a quirk in WMS where the service parameter is not mandatory, the
    WMS service handler is called in the absence of an explicit service
    parameter.
    """
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

        # WMS hack - allowing WMS operation without service identifier 
        if service is None:
            op = req.getParamValue("operation")
            if op and op.lower() in ( "getmap" , "getfeatureinfo" , "describelayer" , "getlegendgraphic" , "getstyles" ) : 
                service = "WMS"
        # WMS hack - the end 

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
    """
    This is the base class for OWS service handlers. It inherits from
    :class:`~.BaseRequestHandler`.
    
    This handler parses the OWS request parameters for a service version. The
    version parameter is mandatory for all OGC Web Services and operations
    except for the respective "GetCapabilities" calls. So, if the request is
    found to be "GetCapabilities" the version negotiation routines are started
    in order to determine the actual OWS version handler to be called.
    Otherwise the version parameter is read from the request or an
    :exc:`~.InvalidRequestException` is raised if it is absent or relates to
    an unknown or disabled version of the service.
    
    Version negotiation is implemented along the lines of OWS Common 2.0. This
    means, the handler checks for the presence of an AcceptVersions parameter.
    If it is present new-style version negotiation is triggered and old-style
    version negotiation otherwise.
    
    New-style version negotiation will take the first version defined
    in the AcceptVersion parameter that is implemented and raise an exception
    if none of the versions is known. The version parameter is always
    ignored.
    
    Old-style version negotiation will look for the version parameter and
    chose the version indicated if it is implemented. If the version parameter
    is lacking the highest implemented version of the service will be selected.
    If the version parameter is present but refers to a version that is not
    implemented, the highest version lower than that is selected. If that fails,
    too, the lowest implemented version will be selected.
    
    Note that OWS Common 2.0 refers to old-style version negotiation as
    deprecated and includes it only for backwards compatibility. But for
    EOxServer which exhibits OWS versions relying on OWS Common as well as
    versions prior to it, the fallback to old-style version negotiation is
    always required. Binding to older versions would otherwise not be
    possible.
    """
    
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
        
        logger.debug("OWSCommonServiceHandler._versionSupported(): versions: %s" % str(versions))
        
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
    """
    This is the base class for OWS version handlers. It inherits from
    :class:`~.BaseRequestHandler`.
    
    Based on the value of the request parameter, the appropriate operation
    handler is chosen and invoked. An :exc:`~.InvalidRequestException` is
    raised if the operation name is unknown or disabled.
    
    This class implements exception handling behaviour which is
    common across the operations of each OWS version but not among
    different versions of the same service.
    """
    
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
    """
    This exception handler is intended for OWS Common 2.0 based exception
    reports. Said standard defines a framework for exception reports that can
    be extended by individual OWS standards with additional error codes, for
    instance.
    
    This class inherits from :class:`~.BaseExceptionHandler`.
    """
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
        """
        In OWS Common 2.0 the HTTP status codes for exception reports can
        differ depending on the error code. There are several exceptions
        listed in the standard itself, but more can be added by OWS
        standards relying on OWS Common 2.0.
        
        This method allows to configure the exception handler with
        a dictionary of additional codes. The dictionary keys shall contain
        the OWS error codes and the values the corresponding HTTP status
        codes as integers.
        """
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


class OWSCommon11ExceptionHandler(BaseExceptionHandler):
    """
    This exception handler is intended for OWS Common 1.1 based exception
    reports. Said standard defines a framework for exception reports that can
    be extended by individual OWS standards with additional error codes, for
    instance.
    
    This class inherits from :class:`~.BaseExceptionHandler`.
    """
    REGISTRY_CONF = {
        "name": "OWS Common Exception Handler",
        "impl_id": "services.owscommon.OWSCommon11ExceptionHandler", 
        "registry_values": {
            "services.interfaces.exception_scheme": "owscommon_1.1"
        }
    }
    
    def __init__(self, schemas, version):
        super(OWSCommon11ExceptionHandler, self).__init__(schemas)
        self.version = version
        
    def _filterExceptions(self, exception):
        if not isinstance(exception, InvalidRequestException) and \
           not isinstance(exception, VersionNegotiationException):
            raise
        
    def _getEncoder(self):
        return OWSCommon11ExceptionEncoder(self.schemas, self.version)
    
    def _getHTTPStatus(self, exception):
        if isinstance(exception, (InvalidRequestException, VersionNegotiationException)):
            return 400
        else:
            return 500

    def _getContentType(self, exception):
        return "text/xml"

OWSCommon11ExceptionHandlerImplementation = ExceptionHandlerInterface.implement(OWSCommon11ExceptionHandler)


class OWSCommonExceptionEncoder(XMLEncoder):
    """
    Encoder for OWS Common 2.0 compliant exception reports. Implements
    :class:`~.ExceptionEncoderInterface`.
    """
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


class OWSCommon11ExceptionEncoder(XMLEncoder):
    """
    Encoder for OWS Common 1.1 compliant exception reports. Implements
    :class:`~.ExceptionEncoderInterface`.
    """
    REGISTRY_CONF = {
        "name": "OWS Common 1.1 Exception Report Encoder",
        "impl_id": "services.owscommon.OWSCommon11ExceptionEncoder",
        "registry_values": {
            "services.interfaces.exception_scheme": "owscommon_1.1"
        }
    }
    
    def __init__(self, schemas=None, version=None):
        super(OWSCommon11ExceptionEncoder, self).__init__(schemas)
        self.version = version or "1.1.0"
    
    def _initializeNamespaces(self):
        return {
            "ows": "http://www.opengis.net/ows/1.1",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance"
        }
    
    def encodeExceptionReport(self, exception_text, exception_code, locator=None):
        if locator is None:
            element = self._makeElement("ows", "ExceptionReport", [
                ("", "@version", self.version),
                ("", "@xml:lang", "en"),
                ("ows", "Exception", [
                    ("", "@exceptionCode", exception_code),
                    ("ows", "ExceptionText", exception_text)
                ])
            ])
        else:
            element = self._makeElement("ows", "ExceptionReport", [
                ("", "@version", self.version),
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

OWSCommon11ExceptionEncoderImplementation = ExceptionEncoderInterface.implement(OWSCommon11ExceptionEncoder)


class OWSCommonConfigReader(object):
    """
    This class implements the :class:`~.ConfigReaderInterface`. It provides
    convenience functions for reading OWS related settings from the instance
    configuration.
    """
    REGISTRY_CONF = {
        "name": "OWS Common Config Reader",
        "impl_id": "services.owscommon.OWSCommonConfigReader",
        "registry_values": {}
    }
    
    def validate(self, config):
        """
        Raises :exc:`~.ConfigError` if the mandatory ``http_service_url``
        setting is missing in the ``services.owscommon`` section of the
        instance configuration.
        """
        if config.getInstanceConfigValue("services.owscommon", "http_service_url") is None:
            raise ConfigError("Missing mandatory 'http_service_url' parameter")
    
    def getHTTPServiceURL(self):
        """
        Returns the value of the `http_service_url`` in the
        ``services.owscommon`` section. This is used for reporting the
        correct service address in the OWS capabilities.
        """
        return System.getConfig().getInstanceConfigValue("services.owscommon", "http_service_url")

OWSCommonConfigReaderImplementation = ConfigReaderInterface.implement(OWSCommonConfigReader)
