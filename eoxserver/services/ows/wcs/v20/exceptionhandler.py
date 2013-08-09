from eoxserver.core import Component, implements
from eoxserver.services.interfaces import OWSExceptionHandlerInterface
from eoxserver.services.ows.common.v20.encoders import OWS20ExceptionXMLEncoder
from eoxserver.core.decoders import (
    DecodingException, MissingParameterException
)


class WCS20ExceptionHandler(Component):
    implements(OWSExceptionHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = None

    def handle_exception(self, request, exception):
        message = str(exception)
        code = getattr(exception, "code", None)
        locator = getattr(exception, "locator", None)
        status = 400
        
        if code is None:
            if isinstance(exception, MissingParameterException):
                code = "MissingParameterValue"
            elif isinstance(exception, DecodingException):
                code = "InvalidParameterValue"
            else:
                code = "InvalidRequest"

        if code in ("NoSuchCoverage", "InvalidAxisLabel", "InvalidSubsetting"):
            status = 404
        elif code in ("OperationNotSupported", "OptionNotSupported"):
            status = 501

        encoder = OWS20ExceptionXMLEncoder()
        content, content_type = encoder.encode(message, "2.0.1", code, locator)

        return content, content_type, status
