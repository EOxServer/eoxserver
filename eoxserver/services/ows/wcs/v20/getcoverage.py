from eoxserver.core import Component, implements
from eoxserver.services.interfaces import CoverageRendererInterface
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface,
    CoverageRendererInterface
)
from eoxserver.services.exceptions import NoSuchCoverageException


class WCS20GetCoverageHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    implements(OWSPostServiceHandlerInterface)

    renderers = ExtensionPoint(CoverageRendererInterface)

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCoverageXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        coverage_id = decoder.coverage_id

        try:
            coverage = models.Coverage.objects.get(identifier=coverage_id)
        except models.Coverage.DoesNotExist:
            raise NoSuchCoverageException(coverage_id)

        coverage_type = coverage.real_type

        renderer = self.get_renderer(coverage_type)

        try:
            renderer.render(coverage) # TODO: pass arguments
        except Exception, e:
            # TODO: ?
            raise



    def get_renderer(self, coverage_type):
        for renderer in self.renderers:
            if issubclass(coverage_type, renderer.handles):
                return renderer

        raise "No renderer found for coverage type '%s'." % coverage_type.__name__








class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("/wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("/wcs:DimensionTrim", type=parse_subset_xml, num="*")
    
    namespaces = nsmap
