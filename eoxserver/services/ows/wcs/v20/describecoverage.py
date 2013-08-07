from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import nsmap
from eoxserver.services.ows.wcs.v20.encoders import (
    WCS20CoverageDescriptionXMLEncoder
)
from eoxserver.services.ows.wcs.encoders import WCS20EOAPEncoder
from eoxserver.core.util.xmltools import DOMElementToXML



class WCS20DescribeCoverageHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    implements(OWSPostServiceHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = "DescribeCoverage"


    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20DescribeCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20DescribeCoverageXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        coverage_ids = decoder.coverage_ids

        if len(coverage_ids) == 0:
            raise

        coverages = []
        for coverage_id in coverage_ids:
            try:
                coverages.append(
                    models.Coverage.objects.get(identifier__exact=coverage_id)
                )
            except models.Coverage.DoesNotExist:
                raise NoSuchCoverage(coveage_id)

        #encoder = WCS20CoverageDescriptionXMLEncoder()
        #return encoder.encode(coverages)

        # TODO: remove this at some point
        encoder = WCS20EOAPEncoder()
        return DOMElementToXML(encoder.encodeCoverageDescriptions(coverages)), "text/xml"


class WCS20DescribeCoverageKVPDecoder(kvp.Decoder):
    coverage_ids = kvp.Parameter("coverageid", type=typelist(str, ","), num=1)


class WCS20DescribeCoverageXMLDecoder(xml.Decoder):
    coverage_ids = xml.Parameter("/wcs:CoverageId/text()", num="+")
    namespaces = nsmap
