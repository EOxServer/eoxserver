from lxml import etree

from django.contrib.contenttypes.models import ContentType

from eoxserver.core import Component, implements

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss
from eoxserver.services.component import OWSServiceComponent, env
from eoxserver.services.interfaces import (
    OWSServiceHandlerInterface, 
    OWSGetServiceHandlerInterface, OWSPostServiceHandlerInterface
)
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wcs.v20.util import (
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_eowcs, 
    nsmap,
    OWS, GML, WCS, CRS, EOWCS,
)


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


class WCS20CapabilitiesXMLEncoder(object):
    def encode(self, decoder):
        reader = CapabilitiesConfigReader(get_eoxserver_config())

        sections = []
        if decoder.section_included("ServiceIdentification"):
            sections.append(
                OWS("ServiceIdentification",
                    OWS("Title", reader.title),
                    OWS("Abstract", reader.abstract),
                    OWS("Keywords", 
                        *map(lambda k: OWS("Keyword", k), reader.keywords)
                    ),
                    OWS("ServiceType", "OGC WCS", codeSpace="OGC"),
                    OWS("ServiceTypeVersion", "2.0.1"),
                    OWS("Profile", "profile"), #TODO
                    OWS("Fees", reader.fees),
                    OWS("AccessConstraints", reader.access_constraints)
                )
            )

        if decoder.section_included("ServiceProvider"):
            sections.append(
                OWS("ServiceProvider",
                    OWS("ProviderName", reader.provider_name),
                    OWS("ProviderSite", reader.provider_site),
                    OWS("ServiceContact",
                        OWS("IndividualName", reader.individual_name),
                        OWS("PositionName", reader.position_name),
                        OWS("ContactInfo",
                            OWS("Phone",
                                OWS("Voice", reader.phone_voice),
                                OWS("Facsimile", reader.phone_facsimile)
                            )
                        ),
                        OWS("Address",
                            OWS("DeliveryPoint", reader.delivery_point),
                            OWS("City", reader.city),
                            OWS("AdministrativeArea", reader.administrative_area),
                            OWS("PostalCode", reader.postal_code),
                            OWS("Country", reader.country),
                            OWS("ElectronicMailAddress", reader.electronic_mail_address)
                        ),
                        OWS("OnlineResource", **{
                            ns_xlink("href"): reader.http_service_url, # TODO: here
                            ns_xlink("type"): "simple"
                        }),
                        OWS("HoursOfService", reader.hours_of_service),
                        OWS("ContactInstructions", reader.contact_instructions)
                    ),
                    OWS("Role", reader.role)
                )
            )


        if decoder.section_included("OperationsMetadata"):
            component = OWSServiceComponent(env)
            versions = ("2.0.0", "2.0.1")
            get_handlers = component.query_service_handlers(
                service="WCS", versions=versions, method="GET"
            )
            post_handlers = component.query_service_handlers(
                service="WCS", versions=versions, method="POST"
            )
            all_handlers = sorted(
                set(get_handlers + post_handlers), key=lambda h: h.request
            )

            operations = []
            for handler in all_handlers:
                methods = []
                if handler in get_handlers:
                    methods.append(
                        OWS("Get", **{
                                ns_xlink("href"): reader.http_service_url,
                                ns_xlink("type"): "simple"
                            }
                        )
                    )
                if handler in post_handlers:
                    methods.append(
                        OWS("Post",
                            OWS("Constraint", 
                                OWS("AllowedValues", 
                                    OWS("Value", "XML")
                                ), name="PostEncoding"
                            ), **{
                                ns_xlink("href"): reader.http_service_url,
                                ns_xlink("type"): "simple"
                            }
                        )
                    )

                operations.append(
                    OWS("Operation",
                        OWS("DCP",
                            OWS("HTTP", *methods)
                        ), name=handler.request
                    )
                )

            sections.append(OWS("OperationsMetadata", *operations))


        if decoder.section_included("ServiceMetadata"):
            service_metadata = WCS("ServiceMetadata")

            # get the list of enabled formats from the format registry
            formats = getFormatRegistry().getSupportedFormatsWCS()
            service_metadata.extend(
                map(lambda f: WCS("formatSupported", f.mimeType), formats)
            )

            # get a list of supported CRSs from the CRS registry
            supported_crss = crss.getSupportedCRS_WCS(format_function=crss.asURL)
            extension = WCS("Extension")
            service_metadata.append(extension)
            extension.extend(
                map(lambda c: CRS("crsSupported", c), supported_crss)
            )

            sections.append(service_metadata)


        if decoder.section_included("Contents", "CoverageSummary", "DatasetSeriesSummary"):
            contents = []

            if decoder.section_included("Contents", "CoverageSummary"):
                coverages = []
                coverages_qs = models.Coverage.objects \
                    .order_by("identifier") \
                    .values_list("identifier", "real_content_type")

                for identifier, content_type in coverages_qs:
                    coverage_type = ContentType.objects.get_for_id(content_type).model_class().__name__

                    coverages.append(
                        WCS("CoverageSummary",
                            WCS("CoverageId", identifier),
                            WCS("CoverageSubtype", coverage_type)
                        )
                    )
                contents.extend(coverages)

            if decoder.section_included("Contents", "DatasetSeriesSummary"):
                dataset_series_set = []

                # TODO: bug in Django/GeoDjango when using dates in values_list
                """dataset_series_qs = models.DatasetSeries.objects \
                    .order_by("identifier") \
                    .envelope() \
                    .values_list("identifier", "envelope", "begin_time", "end_time")

                for identifier, envelope, begin_time, end_time in dataset_series_qs:
                    minx, miny, maxx, maxy = envelope.extent
                    dataset_series.append(
                        WCSEO("DatasetSeriesSummary", (
                            OWS("WGS84BoundingBox", (
                                OWS("LowerCorner", "%f %f" % (miny, minx)),
                                OWS("UppperCorner", "%f %f" % (maxy, maxx)),
                            )),
                            WCSEO("DatasetSeriesId", identifier),
                            GML("TimePeriod", (
                                GML("beginPosition", begin_time.isoformat()),
                                GML("endPosition", end_time.isoformat())
                            ), **{ns_gml("id"): identifier + "_timeperiod"})
                        ))
                    )"""
                
                dataset_series_qs = models.DatasetSeries.objects \
                    .order_by("identifier") \
                    .exclude(
                        footprint__isnull=True, begin_time__isnull=True, 
                        end_time__isnull=True
                    )
                
                for dataset_series in dataset_series_qs:
                    # TODO: WGS84BoundingBox is mandatory. But what Boundingbox 
                    # does an empty DatasetSeries have?
                    try:
                        minx, miny, maxx, maxy = dataset_series.footprint.extent
                    except:
                        minx, miny, maxx, maxy = -180, -90, 180, 90

                    dataset_series_set.append(
                        EOWCS("DatasetSeriesSummary",
                            OWS("WGS84BoundingBox",
                                OWS("LowerCorner", "%f %f" % (miny, minx)),
                                OWS("UppperCorner", "%f %f" % (maxy, maxx)),
                            ),
                            EOWCS("DatasetSeriesId", dataset_series.identifier),
                            GML("TimePeriod",
                                GML("beginPosition", dataset_series.begin_time.isoformat()),
                                GML("endPosition", dataset_series.end_time.isoformat()),
                                **{ns_gml("id"): dataset_series.identifier + "_timeperiod"}
                            )
                        )
                    )

                contents.append(WCS("Extension", *dataset_series_set))

            sections.append(WCS("Contents", *contents))

        root = WCS("Capabilities", *sections, version="2.0.1")
        return etree.tostring(root, pretty_print=True, encoding='iso-8859-1'), "text/xml"

