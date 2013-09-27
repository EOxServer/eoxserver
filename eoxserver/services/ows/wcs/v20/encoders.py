#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


from lxml import etree

from eoxserver.core.config import get_eoxserver_config
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss
from eoxserver.services.ows.component import ServiceComponent, env
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wcs.v20.util import (
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_eowcs, 
    OWS, GML, WCS, CRS, EOWCS,
)


class WCS20CapabilitiesXMLEncoder(object):
    def encode(self, sections, coverages_qs=None, dataset_series_qs=None):
        conf = CapabilitiesConfigReader(get_eoxserver_config())


        all_sections = "all" in sections
        caps = []
        if all_sections or "serviceidentification" in sections:
            caps.append(
                OWS("ServiceIdentification",
                    OWS("Title", conf.title),
                    OWS("Abstract", conf.abstract),
                    OWS("Keywords", 
                        *map(lambda k: OWS("Keyword", k), conf.keywords)
                    ),
                    OWS("ServiceType", "OGC WCS", codeSpace="OGC"),
                    OWS("ServiceTypeVersion", "2.0.1"),
                    OWS("Profile", "profile"), #TODO
                    OWS("Fees", conf.fees),
                    OWS("AccessConstraints", conf.access_constraints)
                )
            )

        if all_sections or "serviceprovider" in sections:
            caps.append(
                OWS("ServiceProvider",
                    OWS("ProviderName", conf.provider_name),
                    OWS("ProviderSite", conf.provider_site),
                    OWS("ServiceContact",
                        OWS("IndividualName", conf.individual_name),
                        OWS("PositionName", conf.position_name),
                        OWS("ContactInfo",
                            OWS("Phone",
                                OWS("Voice", conf.phone_voice),
                                OWS("Facsimile", conf.phone_facsimile)
                            )
                        ),
                        OWS("Address",
                            OWS("DeliveryPoint", conf.delivery_point),
                            OWS("City", conf.city),
                            OWS("AdministrativeArea", conf.administrative_area),
                            OWS("PostalCode", conf.postal_code),
                            OWS("Country", conf.country),
                            OWS("ElectronicMailAddress", conf.electronic_mail_address)
                        ),
                        OWS("OnlineResource", **{
                            ns_xlink("href"): conf.http_service_url, # TODO: here
                            ns_xlink("type"): "simple"
                        }),
                        OWS("HoursOfService", conf.hours_of_service),
                        OWS("ContactInstructions", conf.contact_instructions)
                    ),
                    OWS("Role", conf.role)
                )
            )


        if all_sections or "operationsmetadata" in sections:
            component = ServiceComponent(env)
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
                                ns_xlink("href"): conf.http_service_url,
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
                                ns_xlink("href"): conf.http_service_url,
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

            caps.append(OWS("OperationsMetadata", *operations))


        if all_sections or "servicemetadata" in sections:
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

            caps.append(service_metadata)

        inc_contents = all_sections or "contents" in sections
        inc_coverage_summary = inc_contents or "coveragesummary" in sections
        inc_dataset_series_summary = inc_contents or "datasetseriessummary" in sections
        inc_contents = inc_contents or inc_coverage_summary or inc_dataset_series_summary

        if inc_contents:
            contents = []

            if inc_coverage_summary:
                coverages = []

                # reduce data transfer by only selecting required elements
                # TODO: currently runs into a bug
                #coverages_qs = coverages_qs.only(
                #    "identifier", "real_content_type"
                #)

                for coverage in coverages_qs:
                    coverages.append(
                        WCS("CoverageSummary",
                            WCS("CoverageId", coverage.identifier),
                            WCS("CoverageSubtype", coverage.real_type.__name__)
                        )
                    )
                contents.extend(coverages)

            if inc_dataset_series_summary:
                dataset_series_set = []
                
                # reduce data transfer by only selecting required elements
                # TODO: currently runs into a bug
                #dataset_series_qs = dataset_series_qs.only(
                #    "identifier", "begin_time", "end_time", "footprint"
                #)
                
                for dataset_series in dataset_series_qs:
                    minx, miny, maxx, maxy = dataset_series.extent_wgs84

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

            caps.append(WCS("Contents", *contents))

        root = WCS("Capabilities", *caps, version="2.0.1")
        return etree.tostring(root, pretty_print=True, encoding='iso-8859-1'), "text/xml"


class WCS20CoverageDescriptionXMLEncoder(object):
    def encode(self, coverages):
        pass
