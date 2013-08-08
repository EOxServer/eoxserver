from lxml import etree

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss
from eoxserver.services.ows.wcs.v20.util import (
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_eowcs, 
    OWS, GML, WCS, CRS, EOWCS,
)


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
                    minx, miny, maxx, maxy = dataset_series.footprint.extent

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


class WCS20CoverageDescriptionXMLEncoder(object):
    def encode(self, coverages):
        pass


class WCS20ExceptionXMLEncoder(object):
    def encode(self, message, code, locator):
        # TODO schema location, xml:lang
        root = OWS("ExceptionReport", 
            OWS("Exception", 
                OWS("ExceptionText", message),
                exceptionCode=code, locator=locator
            )
        )
        return etree.tostring(root, pretty_print=True, encoding='iso-8859-1'), "text/xml"
