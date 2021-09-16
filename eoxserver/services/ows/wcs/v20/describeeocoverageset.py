# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------


import logging

from django.db.models import Q
from django.utils.six import MAXSIZE

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, enum
from eoxserver.render.coverage import objects
from eoxserver.resources.coverages import models
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, SectionsMixIn, parse_subset_kvp, parse_subset_xml
)
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.ows.common.config import WCSEOConfigReader
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.exceptions import (
    NoSuchDatasetSeriesOrCoverageException, InvalidSubsettingException
)


logger = logging.getLogger(__name__)


class WCS20DescribeEOCoverageSetHandler(object):
    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    methods = ['GET', 'POST']
    request = "DescribeEOCoverageSet"

    index = 20

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20DescribeEOCoverageSetKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20DescribeEOCoverageSetXMLDecoder(request.body)

    @property
    def constraints(self):
        reader = WCSEOConfigReader(get_eoxserver_config())
        return {
            "CountDefault": reader.paging_count_default
        }

    def handle(self, request):
        decoder = self.get_decoder(request)
        eo_ids = decoder.eo_ids

        containment = decoder.containment
        if not containment:
            containment = "overlaps"

        count_default = self.constraints["CountDefault"]
        count = decoder.count
        if count_default is not None:
            count = min(count, count_default)

        try:
            subsets = Subsets(
                decoder.subsets,
                crs="http://www.opengis.net/def/crs/EPSG/0/4326",
                allowed_types=Trim
            )
        except ValueError as e:
            raise InvalidSubsettingException(str(e))

        # check whether the DatasetSeries and CoverageDescriptions sections are
        # included
        inc_dss_section = decoder.section_included("DatasetSeriesDescriptions")
        inc_cov_section = decoder.section_included("CoverageDescriptions")

        if len(eo_ids) == 0:
            raise

        # fetch the objects directly referenced by EOID
        eo_objects = models.EOObject.objects.filter(
            identifier__in=eo_ids
        ).select_subclasses()

        # check if all EOIDs are available
        available_ids = set(eo_object.identifier for eo_object in eo_objects)
        failed = [
            eo_id for eo_id in eo_ids if eo_id not in available_ids
        ]

        # fail when some objects are not available
        if failed:
            raise NoSuchDatasetSeriesOrCoverageException(failed)

        # split list of objects into Collections, Products and Coverages
        collections = []
        mosaics = []
        products = []
        coverages = []

        for eo_object in eo_objects:
            if isinstance(eo_object, models.Collection):
                collections.append(eo_object)
            elif isinstance(eo_object, models.Mosaic):
                mosaics.append(eo_object)
            elif isinstance(eo_object, models.Product):
                products.append(eo_object)
            elif isinstance(eo_object, models.Coverage):
                coverages.append(eo_object)

        filters = subsets.get_filters(containment=containment)

        # get a QuerySet of all dataset series, directly or indirectly
        # referenced
        all_dataset_series_qs = models.EOObject.objects.filter(
            Q(  # directly referenced Collections
                collection__isnull=False,
                identifier__in=[
                    collection.identifier for collection in collections
                ],
            ) |
            Q(  # directly referenced Products
                product__isnull=False,
                identifier__in=[product.identifier for product in products],
            ) |
            Q(  # Products within Collections
                product__isnull=False,
                product__collections__in=collections,
                **filters
            )
        ).distinct().order_by('identifier')

        if inc_dss_section:
            dataset_series_qs = all_dataset_series_qs[:count]
        else:
            dataset_series_qs = models.EOObject.objects.none()

        # Allow metadata queries on coverage itself or on the
        # parent product if available
        parent_product_filters = []
        for key, value in filters.items():
            prop = key.partition('__')[0]
            parent_product_filters.append(
                Q(**{
                    key: value
                }) | Q(**{
                    '%s__isnull' % prop: True,
                    'coverage__parent_product__%s' % key: value
                })
            )

        # get a QuerySet for all Coverages, directly or indirectly referenced
        all_coverages_qs = models.EOObject.objects.filter(
            *parent_product_filters
        ).filter(
            Q(  # directly referenced Coverages
                identifier__in=[
                    coverage.identifier for coverage in coverages
                ]
            ) |
            Q(  # Coverages within directly referenced Products
                coverage__parent_product__in=products,
            ) |
            Q(  # Coverages within indirectly referenced Products
                coverage__parent_product__collections__in=collections
            ) |
            Q(  # Coverages within directly referenced Collections
                coverage__collections__in=collections
            ) |
            Q(  # Coverages within directly referenced Mosaics
                coverage__mosaics__in=mosaics
            ) |
            Q(  # directly referenced Mosaics
                identifier__in=[
                    mosaic.identifier for mosaic in mosaics
                ]
            ) |
            Q(  # Mosaics within directly referenced Collections
                mosaic__collections__in=collections
            )
        ).distinct().select_subclasses(models.Coverage, models.Mosaic)

        all_coverages_qs = all_coverages_qs.order_by('identifier')

        # check if the CoverageDescriptions section is included. If not, use an
        # empty queryset
        if inc_cov_section:
            coverages_qs = all_coverages_qs
        else:
            coverages_qs = models.Coverage.objects.none()

        # limit coverages according to the number of dataset series
        coverages_qs = coverages_qs[:max(
            0, count - dataset_series_qs.count() - len(mosaics)
        )]

        # compute the number of all items that would match
        number_matched = (
            all_coverages_qs.count() + all_dataset_series_qs.count()
        )

        # create an encoder and encode the result
        encoder = WCS20EOXMLEncoder()
        return (
            encoder.serialize(
                encoder.encode_eo_coverage_set_description(
                    dataset_series_set=[
                        objects.DatasetSeries.from_model(eo_object)
                        for eo_object in dataset_series_qs
                    ],
                    coverages=[
                        objects.from_model(coverage)
                        for coverage in coverages_qs
                    ],
                    number_matched=number_matched
                ), pretty_print=True
            ),
            encoder.content_type
        )


def pos_int(value):
    value = int(value)
    if value < 0:
        raise ValueError("Negative values are not allowed.")
    return value


containment_enum = enum(
    ("overlaps", "contains"), False
)

sections_enum = enum(
    ("DatasetSeriesDescriptions", "CoverageDescriptions", "All"), False
)


class WCS20DescribeEOCoverageSetKVPDecoder(kvp.Decoder, SectionsMixIn):
    eo_ids      = kvp.Parameter("eoid", type=typelist(str, ","), num=1, locator="eoid")
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    containment = kvp.Parameter(type=containment_enum, num="?")
    count       = kvp.Parameter(type=pos_int, num="?", default=MAXSIZE)
    sections    = kvp.Parameter(type=typelist(sections_enum, ","), num="?")


class WCS20DescribeEOCoverageSetXMLDecoder(xml.Decoder, SectionsMixIn):
    eo_ids      = xml.Parameter("wcseo:eoId/text()", num="+", locator="eoid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*")
    containment = xml.Parameter("wcseo:containment/text()", type=containment_enum, locator="containment")
    count       = xml.Parameter("@count", type=pos_int, num="?", default=MAXSIZE, locator="count")
    sections    = xml.Parameter("wcseo:sections/wcseo:section/text()", type=sections_enum, num="*", locator="sections")

    namespaces = nsmap
