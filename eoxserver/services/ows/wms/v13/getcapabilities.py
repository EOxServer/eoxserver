

from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.services.component import OWSServiceComponent, env
from eoxserver.services.wms.renderer import WMSCapabilitiesRenderer


class WMS13GetCapabilitiesHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    #implements(OWSPostServiceHandlerInterface) # TODO: ?
    
    service = "WMS"
    versions = ("1.3", "1.3.0",)
    request = "GetCapabilities"

    def get_decoder(self, request):
        pass

    def handle(self, request):
        decoder = self.get_decoder(request)
        if "text/xml" not in decoder.acceptformats:
            raise InvalidRequestException()

        coverages_qs = models.Coverage.objects.order_by("identifier")

        dataset_series_qs = models.DatasetSeries.objects \
            .order_by("identifier") \
            .exclude(
                footprint__isnull=True, begin_time__isnull=True, 
                end_time__isnull=True
            )

        renderer = WMSCapabilitiesRenderer()
        return renderer.render(decoder.sections, coverages_qs, dataset_series_qs)

