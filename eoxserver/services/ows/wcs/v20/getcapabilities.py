

from django.contrib.contenttypes.models import ContentType

from eoxserver.core import Component, implements

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.services.component import OWSServiceComponent, env
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wcs.v20.util import nsmap
from eoxserver.services.ows.wcs.v20.encoders import WCS20CapabilitiesXMLEncoder


class WCS20GetCapabilitiesHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    implements(OWSPostServiceHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = "GetCapabilities"


    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCapabilitiesKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCapabilitiesXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        if "text/xml" not in decoder.acceptformats:
            raise InvalidRequestException()
        encoder = WCS20CapabilitiesXMLEncoder()
        return encoder.encode(decoder)


class WCS20GetCapabilitiesDecoder(object):
    """ Mix-in for WCS 2.0 GetCapabilities request decoders.
    """

    def section_included(self, *sections):
        """ See if one of the sections is requested.
        """
        if not self.sections:
            return True

        for section in sections:
            section = section.upper()
            if "ALL" in self.sections or section in self.sections:
                return True

        return False


class WCS20GetCapabilitiesKVPDecoder(kvp.Decoder, WCS20GetCapabilitiesDecoder):
    sections            = kvp.Parameter(type=typelist(upper, ","), num="?")
    updatesequence      = kvp.Parameter(num="?")
    acceptversions      = kvp.Parameter(type=typelist(str, ","), num="?")
    acceptformats       = kvp.Parameter(type=typelist(str, ","), num="?", default=["text/xml"])
    acceptlanguages     = kvp.Parameter(type=typelist(str, ","), num="?")


class WCS20GetCapabilitiesXMLDecoder(xml.Decoder, WCS20GetCapabilitiesDecoder):
    sections            = xml.Parameter("/ows:Sections/ows:Section/text()", num="*")
    updatesequence      = xml.Parameter("/@updateSequence", num="?")
    acceptversions      = xml.Parameter("/ows:AcceptVersions/ows:Version/text()", num="*")
    acceptformats       = xml.Parameter("/ows:AcceptFormats/ows:OutputFormat/text()", num="*", default=["text/xml"])
    acceptlanguages     = xml.Parameter("/ows:AcceptLanguages/ows:Language/text()", num="*")

    namespaces = nsmap
