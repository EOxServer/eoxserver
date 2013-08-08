from eoxserver.core import Component, implements
from eoxserver.services.interfaces import OWSExceptionHandlerInterface
from eoxserver.services.ows.wcs.v20.encoders import WCS20ExceptionXMLEncoder

class WCS20ExceptionHandler(Component):
    implements(OWSExceptionHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = None

    def handle_exception(self, request, exception):
        encoder = WCS20ExceptionXMLEncoder()
        # TODO: real code/locator
        return encoder.encode(str(exception), "code", "locator")

