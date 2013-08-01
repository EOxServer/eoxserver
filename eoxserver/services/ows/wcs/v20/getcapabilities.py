from lxml import etree

from django.contrib.contenttypes.models import ContentType

from eoxserver.core import Component, implements

from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.resources.coverages import models
from eoxserver.services.interfaces import OWSServiceHandlerInterface
from eoxserver.services.ows.wcs.v20.util import (
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_eowcs, 
    nsmap,
    OWS, GML, WCS, CRS, EOWCS,
)


class WCS20GetCapabilitiesHandler(Component):
    implements(OWSServiceHandlerInterface)

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

        sections = []
        if decoder.section_included("ServiceIdentification"):
            sections.append(
                OWS("ServiceIdentification",
                    OWS("Title", "title"),
                    OWS("Abstract", "abstract"),
                    OWS("Keywords", 
                        OWS("Keyword", "keyword")
                    ),
                    OWS("ServiceType", "OGC WCS", codeSpace="OGC"),
                    OWS("ServiceTypeVersion", "2.0.1"),
                    OWS("Profile", "profile"),
                    OWS("Fees", "None"),
                    OWS("AccessConstraints", "None")
                )
            )

        if decoder.section_included("ServiceProvider"):
            sections.append(
                OWS("ServiceProvider",
                    OWS("ProviderName", ""),
                    OWS("ProviderSite", ""),
                    OWS("ServiceContact",
                        OWS("IndividualName", ""),
                        OWS("PositionName", ""),
                        OWS("ContactInfo",
                            OWS("Phone",
                                OWS("Voice", ""),
                                OWS("Facsimile", "")
                            )
                        ),
                        OWS("Address",
                            OWS("DeliveryPoint", ""),
                            OWS("City", ""),
                            OWS("AdministrativeArea", ""),
                            OWS("PostalCode", ""),
                            OWS("Country", ""),
                            OWS("ElectronicMailAddress", "")
                        ),
                        OWS("OnlineResource", ""),
                        OWS("HoursOfService", ""),
                        OWS("ContactInstructions", "")
                    ),
                    OWS("Role", "")
                )
            )

        if decoder.section_included("OperationsMetadata"):
            sections.append(
                OWS("OperationsMetadata",
                    OWS("Operation",
                        OWS("DCP",
                            OWS("HTTP",
                                OWS("Get", **{
                                        ns_xlink("href"): "",
                                        ns_xlink("type"): "simple"
                                }),
                                OWS("Get",
                                    OWS("Constraint", 
                                        OWS("AllowedValues", 
                                            OWS("Value", "XML")
                                        ), name="PostEncoding"
                                    ), **{
                                        ns_xlink("href"): "",
                                        ns_xlink("type"): "simple"
                                    }
                                ),
                            ),
                        ), name="GetCapabilities"
                    ),
                )
            )
    
        if decoder.section_included("ServiceMetadata"):
            sections.append(
                WCS("ServiceMetadata",
                    WCS("formatSupported"),
                    WCS("Extension",
                        WCS(ns_crs("crsSupported"), "")
                    )
                )
            )

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


class WCS20GetCapabilitiesDecoder(object):
    """ Mix-in for WCS 2.0 GetCapabilities request decoders.
    """
    def section_included(self, *sections):
        if not self.sections:
            return True

        for section in sections:
            section = section.upper()
            if "ALL" in self.sections or section in self.sections:
                return True

        return False


class WCS20GetCapabilitiesKVPDecoder(kvp.Decoder, WCS20GetCapabilitiesDecoder):
    sections =          kvp.Parameter("sections", type=typelist(upper, ","), num="?")
    update_sequence =   kvp.Parameter("updatesequence", num="?")
    accept_formats =    kvp.Parameter("acceptversions", type=typelist(str, ","), num="?")
    accept_formats =    kvp.Parameter("acceptformats", type=typelist(str, ","), num="?")
    accept_languages =  kvp.Parameter("acceptlanguages", type=typelist(str, ","), num="?")


class WCS20GetCapabilitiesXMLDecoder(kvp.Decoder, WCS20GetCapabilitiesDecoder):
    sections =          xml.Parameter("/ows:Sections/ows:Section/text()", num="*")
    update_sequence =   xml.Parameter("/@updateSequence", num="?")
    accept_formats =    xml.Parameter("/ows:AcceptVersions/ows:Version/text()", num="*")
    accept_formats =    xml.Parameter("/ows:AcceptFormats/ows:OutputFormat/text()", num="*")
    accept_languages =  xml.Parameter("/ows:AcceptLanguages/ows:Language/text()", num="*")

    namespaces = nsmap