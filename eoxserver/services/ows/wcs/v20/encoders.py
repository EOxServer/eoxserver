#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from itertools import chain
from lxml import etree

from django.contrib.gis.geos import Polygon
from django.utils.timezone import now

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.timetools import isoformat
from eoxserver.backends.access import retrieve
from eoxserver.contrib.osr import SpatialReference
from eoxserver.resources.coverages.models import (
    RectifiedStitchedMosaic, ReferenceableDataset
)
from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss, models
from eoxserver.services.gml.v32.encoders import GML32Encoder, EOP20Encoder
from eoxserver.services.ows.component import ServiceComponent, env
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.common.v20.encoders import OWS20Encoder
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, ns_xlink, ns_gml, ns_wcs, ns_eowcs,
    OWS, GML, GMLCOV, WCS, CRS, EOWCS, SWE, INT, SUPPORTED_INTERPOLATIONS
)
from eoxserver.services.urls import get_http_service_url

PROFILES = [
    "spec/WCS_application-profile_earth-observation/1.0/conf/eowcs",
    "spec/WCS_application-profile_earth-observation/1.0/conf/eowcs_get-kvp",
    "spec/WCS_service-extension_crs/1.0/conf/crs",
    "spec/WCS/2.0/conf/core",
    "spec/WCS_protocol-binding_get-kvp/1.0/conf/get-kvp",
    "spec/WCS_protocol-binding_post-xml/1.0/conf/post-xml",
    "spec/GMLCOV/1.0/conf/gml-coverage",
    "spec/GMLCOV/1.0/conf/multipart",
    "spec/GMLCOV/1.0/conf/special-format",
    "spec/GMLCOV_geotiff-coverages/1.0/conf/geotiff-coverage",
    "spec/WCS_geotiff-coverages/1.0/conf/geotiff-coverage",
    "spec/WCS_service-model_crs-predefined/1.0/conf/crs-predefined",
    "spec/WCS_service-extension_interpolation/1.0/conf/interpolation",
    "spec/WCS_service-extension_range-subsetting/1.0/conf/record-subsetting",
    "spec/WCS_service-extension_scaling/1.0/conf/scaling",
]


class WCS20CapabilitiesXMLEncoder(OWS20Encoder):
    def encode_service_identification(self, conf):
        # get a list of versions in descending order from all active
        # GetCapabilities handlers.
        component = ServiceComponent(env)
        handlers = component.query_service_handlers(
            service="WCS", request="GetCapabilities"
        )
        versions = sorted(
            set(chain(*[handler.versions for handler in handlers])),
            reverse=True
        )

        elem = OWS("ServiceIdentification",
            OWS("Title", conf.title),
            OWS("Abstract", conf.abstract),
            OWS("Keywords", *[
                OWS("Keyword", keyword) for keyword in conf.keywords
            ]),
            OWS("ServiceType", "OGC WCS", codeSpace="OGC")
        )

        elem.extend(
            OWS("ServiceTypeVersion", version) for version in versions
        )

        elem.extend(
            OWS("Profile", "http://www.opengis.net/%s" % profile)
            for profile in PROFILES
        )

        elem.extend((
            OWS("Fees", conf.fees),
            OWS("AccessConstraints", conf.access_constraints)
        ))
        return elem

    def encode_service_provider(self, conf):
        return OWS("ServiceProvider",
            OWS("ProviderName", conf.provider_name),
            self.encode_reference("ProviderSite", conf.provider_site),
            OWS("ServiceContact",
                OWS("IndividualName", conf.individual_name),
                OWS("PositionName", conf.position_name),
                OWS("ContactInfo",
                    OWS("Phone",
                        OWS("Voice", conf.phone_voice),
                        OWS("Facsimile", conf.phone_facsimile)
                    ),
                    OWS("Address",
                        OWS("DeliveryPoint", conf.delivery_point),
                        OWS("City", conf.city),
                        OWS("AdministrativeArea", conf.administrative_area),
                        OWS("PostalCode", conf.postal_code),
                        OWS("Country", conf.country),
                        OWS(
                            "ElectronicMailAddress",
                            conf.electronic_mail_address
                        )
                    ),
                    self.encode_reference(
                        "OnlineResource", conf.onlineresource
                    ),
                    OWS("HoursOfService", conf.hours_of_service),
                    OWS("ContactInstructions", conf.contact_instructions)
                ),
                OWS("Role", conf.role)
            )
        )

    def encode_operations_metadata(self, request):
        component = ServiceComponent(env)
        versions = ("2.0.0", "2.0.1")
        get_handlers = component.query_service_handlers(
            service="WCS", versions=versions, method="GET"
        )
        post_handlers = component.query_service_handlers(
            service="WCS", versions=versions, method="POST"
        )
        all_handlers = sorted(
            set(get_handlers + post_handlers),
            key=lambda h: (getattr(h, "index", 10000), h.request)
        )

        http_service_url = get_http_service_url(request)

        operations = []
        for handler in all_handlers:
            methods = []
            if handler in get_handlers:
                methods.append(
                    self.encode_reference("Get", http_service_url)
                )
            if handler in post_handlers:
                post = self.encode_reference("Post", http_service_url)
                post.append(
                    OWS("Constraint",
                        OWS("AllowedValues",
                            OWS("Value", "XML")
                        ), name="PostEncoding"
                    )
                )
                methods.append(post)

            operations.append(
                OWS("Operation",
                    OWS("DCP",
                        OWS("HTTP", *methods)
                    ),
                    # apply default values as constraints
                    *[
                        OWS("Constraint",
                            OWS("NoValues"),
                            OWS("DefaultValue", str(default)),
                            name=name
                        ) for name, default
                        in getattr(handler, "constraints", {}).items()
                    ],
                    name=handler.request
                )
            )

        return OWS("OperationsMetadata", *operations)

    def encode_service_metadata(self):
        service_metadata = WCS("ServiceMetadata")

        # get the list of enabled formats from the format registry
        formats = filter(
            lambda f: f, getFormatRegistry().getSupportedFormatsWCS()
        )
        service_metadata.extend(
            map(lambda f: WCS("formatSupported", f.mimeType), formats)
        )

        # get a list of supported CRSs from the CRS registry
        supported_crss = crss.getSupportedCRS_WCS(
            format_function=crss.asURL
        )
        extension = WCS("Extension")
        service_metadata.append(extension)
        crs_metadata = CRS("CrsMetadata")
        extension.append(crs_metadata)
        crs_metadata.extend(
            map(lambda c: CRS("crsSupported", c), supported_crss)
        )

        base_url = "http://www.opengis.net/def/interpolation/OGC/1/"

        extension.append(
            INT("InterpolationMetadata", *[
                INT("InterpolationSupported",
                    base_url + supported_interpolation
                ) for supported_interpolation in SUPPORTED_INTERPOLATIONS
            ])
        )
        return service_metadata

    def encode_contents(self, coverages_qs, dataset_series_qs):
        contents = []

        if coverages_qs:
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

        if dataset_series_qs:
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
                            OWS("UpperCorner", "%f %f" % (maxy, maxx)),
                        ),
                        EOWCS("DatasetSeriesId", dataset_series.identifier),
                        GML("TimePeriod",
                            GML(
                                "beginPosition",
                                isoformat(dataset_series.begin_time)
                            ),
                            GML(
                                "endPosition",
                                isoformat(dataset_series.end_time)
                            ),
                            **{
                                ns_gml("id"): dataset_series.identifier
                                + "_timeperiod"
                            }
                        )
                    )
                )

            contents.append(WCS("Extension", *dataset_series_set))

        return WCS("Contents", *contents)

    def encode_capabilities(self, sections, coverages_qs=None,
                            dataset_series_qs=None, request=None):
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        all_sections = "all" in sections
        caps = []
        if all_sections or "serviceidentification" in sections:
            caps.append(self.encode_service_identification(conf))

        if all_sections or "serviceprovider" in sections:
            caps.append(self.encode_service_provider(conf))

        if all_sections or "operationsmetadata" in sections:
            caps.append(self.encode_operations_metadata(request))

        if all_sections or "servicemetadata" in sections:
            caps.append(self.encode_service_metadata())

        inc_contents = all_sections or "contents" in sections
        inc_coverage_summary = inc_contents or "coveragesummary" in sections
        inc_dataset_series_summary = (
            inc_contents or "datasetseriessummary" in sections
        )

        if inc_contents or inc_coverage_summary or inc_dataset_series_summary:
            caps.append(
                self.encode_contents(
                    coverages_qs if inc_coverage_summary else None,
                    dataset_series_qs if inc_dataset_series_summary else None
                )
            )

        return WCS(
            "Capabilities", *caps, version="2.0.1",
            updateSequence=conf.update_sequence
        )

    def get_schema_locations(self):
        return nsmap.schema_locations


class GMLCOV10Encoder(GML32Encoder):
    def __init__(self, *args, **kwargs):
        self._cache = {}

    def get_gml_id(self, identifier):
        if identifier[0].isdigit():
            return "gmlid_%s" % identifier
        return identifier

    def encode_grid_envelope(self, low_x, low_y, high_x, high_y):
        return GML("GridEnvelope",
            GML("low", "%d %d" % (low_x, low_y)),
            GML("high", "%d %d" % (high_x, high_y))
        )

    def encode_rectified_grid(self, size, extent, sr, grid_name):
        size_x, size_y = size
        minx, miny, maxx, maxy = extent
        srs_name = sr.url

        swap = crss.getAxesSwapper(sr.srid)
        frmt = "%.3f %.3f" if sr.IsProjected() else "%.8f %.8f"
        labels = ("x", "y") if sr.IsProjected() else ("long", "lat")

        axis_labels = " ".join(swap(*labels))
        origin = frmt % swap(minx, maxy)
        x_offsets = frmt % swap((maxx - minx) / float(size_x), 0)
        y_offsets = frmt % swap(0, (miny - maxy) / float(size_y))

        return GML("RectifiedGrid",
            GML("limits",
                self.encode_grid_envelope(0, 0, size_x - 1, size_y - 1)
            ),
            GML("axisLabels", axis_labels),
            GML("origin",
                GML("Point",
                    GML("pos", origin),
                    **{
                        ns_gml("id"): self.get_gml_id("%s_origin" % grid_name),
                        "srsName": srs_name
                    }
                )
            ),
            GML("offsetVector", x_offsets, srsName=srs_name),
            GML("offsetVector", y_offsets, srsName=srs_name),
            **{
                ns_gml("id"): self.get_gml_id(grid_name),
                "dimension": "2"
            }
        )

    def encode_referenceable_grid(self, size, sr, grid_name):
        size_x, size_y = size
        swap = crss.getAxesSwapper(sr.srid)
        labels = ("x", "y") if sr.IsProjected() else ("long", "lat")
        axis_labels = " ".join(swap(*labels))

        return GML("ReferenceableGrid",
            GML("limits",
                self.encode_grid_envelope(0, 0, size_x - 1, size_y - 1)
            ),
            GML("axisLabels", axis_labels),
            **{
                ns_gml("id"): self.get_gml_id(grid_name),
                "dimension": "2"
            }
        )

    def encode_domain_set(self, coverage, srid=None, size=None, extent=None,
                          rectified=True):
        grid_name = "%s_grid" % coverage.identifier
        srs = SpatialReference(srid) if srid is not None else None

        if rectified:
            return GML("domainSet",
                self.encode_rectified_grid(
                    size or coverage.size, extent or coverage.extent,
                    srs or coverage.spatial_reference, grid_name
                )
            )
        else:
            return GML("domainSet",
                self.encode_referenceable_grid(
                    size or coverage.size, srs or coverage.spatial_reference,
                    grid_name
                )
            )

    def encode_bounded_by(self, extent, sr=None):
        minx, miny, maxx, maxy = extent
        sr = sr or SpatialReference(4326)
        swap = crss.getAxesSwapper(sr.srid)
        labels = ("x", "y") if sr.IsProjected() else ("long", "lat")
        axis_labels = " ".join(swap(*labels))
        axis_units = "m m" if sr.IsProjected() else "deg deg"
        frmt = "%.3f %.3f" if sr.IsProjected() else "%.8f %.8f"
        # Make sure values are outside of actual extent
        if sr.IsProjected():
            minx -= 0.0005
            miny -= 0.0005
            maxx += 0.0005
            maxy += 0.0005
        else:
            minx -= 0.000000005
            miny -= 0.000000005
            maxx += 0.000000005
            maxy += 0.000000005

        return GML("boundedBy",
            GML("Envelope",
                GML("lowerCorner", frmt % swap(minx, miny)),
                GML("upperCorner", frmt % swap(maxx, maxy)),
                srsName=sr.url, axisLabels=axis_labels, uomLabels=axis_units,
                srsDimension="2"
            )
        )

    # cached range types and nil value sets
    def get_range_type(self, pk):
        cached_range_types = self._cache.setdefault(models.RangeType, {})
        try:
            return cached_range_types[pk]
        except KeyError:
            cached_range_types[pk] = models.RangeType.objects.get(pk=pk)
            return cached_range_types[pk]

    def get_nil_value_set(self, pk):
        cached_nil_value_set = self._cache.setdefault(models.NilValueSet, {})
        try:
            return cached_nil_value_set[pk]
        except KeyError:
            try:
                cached_nil_value_set[pk] = models.NilValueSet.objects.get(
                    pk=pk
                )
                return cached_nil_value_set[pk]
            except models.NilValueSet.DoesNotExist:
                return ()

    def encode_nil_values(self, nil_value_set):
        return SWE("nilValues",
            SWE("NilValues",
                *[SWE("nilValue", nil_value.raw_value, reason=nil_value.reason
                ) for nil_value in nil_value_set]
            )
        )

    def encode_field(self, band):
        return SWE("field",
            SWE("Quantity",
                SWE("description", band.description),
                self.encode_nil_values(
                    self.get_nil_value_set(band.nil_value_set_id)
                ),
                SWE("uom", code=band.uom),
                SWE("constraint",
                    SWE("AllowedValues",
                        SWE("interval", "%s %s" % band.allowed_values),
                        SWE("significantFigures", str(band.significant_figures))
                    )
                ),
                definition=band.definition
            ),
            name=band.name
        )

    def encode_range_type(self, range_type):
        return GMLCOV("rangeType",
            SWE("DataRecord",
                *[self.encode_field(band) for band in range_type]
            )
        )


class WCS20CoverageDescriptionXMLEncoder(GMLCOV10Encoder):
    def encode_coverage_description(self, coverage):
        if issubclass(coverage.real_type, ReferenceableDataset):
            rectified = False
        else:
            rectified = True

        return WCS("CoverageDescription",
            self.encode_bounded_by(coverage.extent_wgs84),
            WCS("CoverageId", coverage.identifier),
            self.encode_domain_set(coverage, rectified=rectified),
            self.encode_range_type(self.get_range_type(coverage.range_type_id)),
            WCS("ServiceParameters",
                WCS("CoverageSubtype", coverage.real_type.__name__)
            ),
            **{ns_gml("id"): self.get_gml_id(coverage.identifier)}
        )

    def encode_coverage_descriptions(self, coverages):
        return WCS("CoverageDescriptions", *[
            self.encode_coverage_description(coverage)
            for coverage in coverages
        ])

    def get_schema_locations(self):
        return {ns_wcs.uri: ns_wcs.schema_location}


class WCS20EOXMLEncoder(WCS20CoverageDescriptionXMLEncoder, EOP20Encoder,
                        OWS20Encoder):
    def encode_eo_metadata(self, coverage, request=None, subset_polygon=None):
        data_items = list(coverage.data_items.filter(
            semantic="metadata", format="eogml"
        ))
        if len(data_items) >= 1:
            with open(retrieve(data_items[0])) as f:
                earth_observation = etree.parse(f).getroot()

            if subset_polygon:
                try:
                    feature = earth_observation.xpath(
                        "om:featureOfInterest", namespaces=nsmap
                    )[0]
                    feature[0] = self.encode_footprint(
                        coverage.footprint.intersection(subset_polygon),
                        coverage.identifier
                    )
                except IndexError:
                    pass  # no featureOfInterest

        else:
            earth_observation = self.encode_earth_observation(
                coverage, subset_polygon=subset_polygon
            )

        if not request:
            lineage = None

        elif request.method == "GET":
            lineage = EOWCS("lineage",
                EOWCS("referenceGetCoverage",
                    self.encode_reference("Reference",
                        request.build_absolute_uri().replace("&", "&amp;"),
                        False
                    )
                ), GML("timePosition", isoformat(now()))
            )
        elif request.method == "POST":  # TODO: better way to do this
            href = request.build_absolute_uri().replace("&", "&amp;")
            lineage = EOWCS("lineage",
                EOWCS("referenceGetCoverage",
                    OWS("ServiceReference",
                        OWS("RequestMessage",
                            etree.parse(request).getroot()
                        ), **{ns_xlink("href"): href}
                    )
                ), GML("timePosition", isoformat(now()))
            )

        return GMLCOV("metadata",
            GMLCOV("Extension",
                EOWCS("EOMetadata",
                    earth_observation,
                    *[lineage] if lineage is not None else []
                )
            )
        )

    def encode_coverage_description(self, coverage, srid=None, size=None,
                                    extent=None, footprint=None):
        source_mime = None
        band_items = coverage.data_items.filter(semantic__startswith="bands")
        for data_item in band_items:
            if data_item.format:
                source_mime = data_item.format
                break

        if source_mime:
            source_format = getFormatRegistry().getFormatByMIME(source_mime)
            # map the source format to the native one
            native_format = getFormatRegistry().mapSourceToNativeWCS20(
                source_format
            )
        elif issubclass(coverage.real_type, RectifiedStitchedMosaic):
            # use the default format for RectifiedStitchedMosaics
            native_format = getFormatRegistry().getDefaultNativeFormat()
        else:
            # TODO: improve if no native format availabe
            native_format = None

        if extent:
            poly = Polygon.from_bbox(extent)
            poly.srid = srid
            extent = poly.transform(4326).extent
            sr = SpatialReference(4326)
        else:
            extent = coverage.extent
            sr = coverage.spatial_reference

        if issubclass(coverage.real_type, ReferenceableDataset):
            rectified = False
        else:
            rectified = True

        return WCS("CoverageDescription",
            self.encode_bounded_by(extent, sr),
            WCS("CoverageId", coverage.identifier),
            self.encode_eo_metadata(coverage),
            self.encode_domain_set(coverage, srid, size, extent, rectified),
            self.encode_range_type(self.get_range_type(coverage.range_type_id)),
            WCS("ServiceParameters",
                WCS("CoverageSubtype", coverage.real_type.__name__),
                WCS(
                    "nativeFormat",
                    native_format.mimeType if native_format else ""
                )
            ),
            **{ns_gml("id"): self.get_gml_id(coverage.identifier)}
        )

    def encode_range_set(self, reference, mime_type):
        return GML("rangeSet",
            GML("File",
                GML("rangeParameters",
                    **{
                        ns_xlink("arcrole"): "fileReference",
                        ns_xlink("href"): reference,
                        ns_xlink("role"): mime_type
                    }
                ),
                GML("fileReference", reference),
                GML("fileStructure"),
                GML("mimeType", mime_type)
            )
        )

    def calculate_contribution(self, footprint, contributions,
                               subset_polygon=None):
        if subset_polygon:
            footprint = footprint.intersection(subset_polygon)

        for contribution in contributions:
            footprint = footprint.difference(contribution)
        contributions.append(footprint)
        return footprint

    def encode_contributing_datasets(self, coverage, subset_polygon=None):
        eo_objects = coverage.eo_objects
        if subset_polygon:
            if subset_polygon.srid != 4326:
                subset_polygon = subset_polygon.transform(4326, True)

            eo_objects = eo_objects.filter(
                footprint__intersects=subset_polygon
            )

        # iterate over all subsets in reverse order to get the
        eo_objects = eo_objects.order_by("-begin_time")
        actual_contributions = []
        all_contributions = []
        for eo_object in eo_objects:
            contribution = self.calculate_contribution(
                eo_object.footprint, all_contributions, subset_polygon
            )
            if not contribution.empty and contribution.num_geom > 0:
                actual_contributions.append((eo_object, contribution))

        return EOWCS("datasets", *[
            EOWCS("dataset",
                WCS("CoverageId", eo_object.identifier),
                EOWCS("contributingFootprint",
                    self.encode_footprint(
                        contrib, eo_object.identifier
                    )
                )
            )
            for eo_object, contrib in reversed(actual_contributions)
        ])

    def alter_rectified_dataset(self, coverage, request, tree,
                                subset_polygon=None):
        return EOWCS("RectifiedDataset", *(
            tree.getchildren() + [
                self.encode_eo_metadata(coverage, request, subset_polygon)
            ]
        ), **tree.attrib)

    def alter_rectified_stitched_mosaic(self, coverage, request, tree,
                                        subset_polygon=None):
        return EOWCS("RectifiedStitchedMosaic", *(
            tree.getchildren() + [
                self.encode_eo_metadata(coverage, request, subset_polygon),
                self.encode_contributing_datasets(coverage, subset_polygon)
            ]
        ), **tree.attrib)

    def encode_referenceable_dataset(self, coverage, range_type, reference,
                                     mime_type, subset=None):
        # handle subset
        dst_srid = coverage.srid

        if not subset:
            # whole area - no subset
            domain_set = self.encode_domain_set(coverage, rectified=False)
            eo_metadata = self.encode_eo_metadata(coverage)
            extent = coverage.extent
            sr = SpatialReference(dst_srid)

        else:
            # subset is given
            srid, size, extent, footprint = subset
            srid = srid if srid is not None else 4326

            domain_set = self.encode_domain_set(
                coverage, srid, size, extent, False
            )
            eo_metadata = self.encode_eo_metadata(
                coverage, subset_polygon=footprint
            )

            # get the WGS84 extent
            poly = Polygon.from_bbox(extent)
            poly.srid = srid
            if srid != dst_srid:
                poly.transform(dst_srid)
            extent = poly.extent
            sr = SpatialReference(srid)

        return EOWCS("ReferenceableDataset",
            self.encode_bounded_by(extent, sr),
            domain_set,
            self.encode_range_set(reference, mime_type),
            self.encode_range_type(range_type),
            eo_metadata,
            **{
                ns_gml("id"): self.get_gml_id(coverage.identifier)
            }
        )

    def encode_dataset_series_description(self, dataset_series):
        return EOWCS("DatasetSeriesDescription",
            self.encode_bounded_by(dataset_series.extent_wgs84),
            EOWCS("DatasetSeriesId", dataset_series.identifier),
            self.encode_time_period(
                dataset_series.begin_time, dataset_series.end_time,
                "%s_timeperiod" % dataset_series.identifier
            ),
            **{ns_gml("id"): self.get_gml_id(dataset_series.identifier)}
        )

    def encode_dataset_series_descriptions(self, dataset_series_set):
        return EOWCS("DatasetSeriesDescriptions", *[
            self.encode_dataset_series_description(dataset_series)
            for dataset_series in dataset_series_set
        ])

    def encode_eo_coverage_set_description(self, dataset_series_set, coverages,
                                           number_matched=None,
                                           number_returned=None):
        if number_matched is None:
            number_matched = len(coverages) + len(dataset_series_set)
        if number_returned is None:
            number_returned = len(coverages) + len(dataset_series_set)

        root = EOWCS("EOCoverageSetDescription",
            numberMatched=str(number_matched),
            numberReturned=str(number_returned)
        )

        if coverages:
            root.append(self.encode_coverage_descriptions(coverages))
        if dataset_series_set:
            root.append(self.encode_dataset_series_descriptions(
                dataset_series_set
            ))

        return root

    def get_schema_locations(self):
        return {ns_eowcs.uri: ns_eowcs.schema_location}
