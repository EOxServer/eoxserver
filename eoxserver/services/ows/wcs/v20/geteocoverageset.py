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


import os
import tempfile
import logging
from itertools import chain
import mimetypes

from django.db.models import Q
from django.http import HttpResponse
try:
    from django.http import StreamingHttpResponse
except ImportError:
    StreamingHttpResponse = HttpResponse

from django.utils.six import MAXSIZE
from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, enum
from eoxserver.render.coverage import objects
from eoxserver.resources.coverages import models
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, parse_subset_kvp, parse_subset_xml
)
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams
from eoxserver.services.ows.common.config import WCSEOConfigReader
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.exceptions import (
    NoSuchDatasetSeriesOrCoverageException, InvalidRequestException,
    InvalidSubsettingException
)


logger = logging.getLogger(__name__)


DEFAULT_PACKAGE_WRITERS = [
    'eoxserver.services.ows.wcs.v20.packages.tar.TarPackageWriter',
    'eoxserver.services.ows.wcs.v20.packages.zip.ZipPackageWriter',
]
PACKAGE_WRITERS = None


def _setup_package_writers():
    global PACKAGE_WRITERS
    specifiers = getattr(
        settings, 'EOXS_PACKAGE_WRITERS',
        DEFAULT_PACKAGE_WRITERS
    )
    PACKAGE_WRITERS = [
        import_string(specifier)()
        for specifier in specifiers
    ]


def get_package_writers():
    if PACKAGE_WRITERS is None:
        _setup_package_writers()

    return PACKAGE_WRITERS


class WCS20GetEOCoverageSetHandler(object):
    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    methods = ['GET', 'POST']
    request = "GetEOCoverageSet"

    index = 21

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetEOCoverageSetKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetEOCoverageSetXMLDecoder(request.body)

    def get_params(self, coverage, decoder, request):
        return WCS20CoverageRenderParams(
            coverage, Subsets(decoder.subsets), http_request=request
        )

    def get_renderer(self, params):
        # TODO: fix circular import issue and get renderer from the
        # get_coverage_renderer function
        from eoxserver.services.mapserver.wcs.coverage_renderer import RectifiedCoverageMapServerRenderer
        # from eoxserver.services.ows.wcs.basehandlers import get_coverage_renderers
        renderers = [RectifiedCoverageMapServerRenderer()]
        # for renderer in get_coverage_renderers(params):
        for renderer in renderers:
            if renderer.supports(params):
                return renderer

        raise InvalidRequestException(
            "Could not find renderer for coverage '%s'."
        )

    def get_pacakge_writer(self, format, params):
        for writer in get_package_writers():
            if writer.supports(format, params):
                return writer

        raise InvalidRequestException(
            "Format '%s' is not supported." % format, locator="format"
        )

    @property
    def constraints(self):
        reader = WCSEOConfigReader(get_eoxserver_config())
        return {
            "CountDefault": reader.paging_count_default
        }

    def handle(self, request):
        decoder = self.get_decoder(request)
        eo_ids = decoder.eo_ids

        format, format_params = decoder.format
        writer = self.get_pacakge_writer(format, format_params)

        containment = decoder.containment

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
        )

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
        ).select_subclasses(models.Coverage, models.Mosaic)

        all_coverages_qs = all_coverages_qs.order_by('identifier')

        # limit coverages according to the number of dataset series
        coverages_qs = all_coverages_qs[:max(
            0, count - all_dataset_series_qs.count() - len(mosaics)
        )]

        fd, pkg_filename = tempfile.mkstemp()
        tmp = os.fdopen(fd)
        tmp.close()
        package = writer.create_package(pkg_filename, format, format_params)

        for coverage_model in coverages_qs:
            coverage = objects.from_model(coverage_model)
            params = self.get_params(coverage, decoder, request)
            renderer = self.get_renderer(params)
            result_set = renderer.render(params)
            all_filenames = set()
            for result_item in result_set:
                if not result_item.filename:
                    ext = mimetypes.guess_extension(result_item.content_type)
                    filename = coverage.identifier + ext
                else:
                    filename = result_item.filename.decode()
                if filename in all_filenames:
                    continue  # TODO: create new filename
                all_filenames.add(filename)
                location = "%s/%s" % (coverage.identifier, filename)
                writer.add_to_package(
                    package, result_item.data, result_item.size, location
                )

        mime_type = writer.get_mime_type(package, format, format_params)
        ext = writer.get_file_extension(package, format, format_params)
        writer.cleanup(package)

        response = StreamingHttpResponse(
            tempfile_iterator(pkg_filename), mime_type
        )
        response["Content-Disposition"] = 'inline; filename="ows%s"' % ext
        response["Content-Length"] = str(os.path.getsize(pkg_filename))

        return response


def tempfile_iterator(filename, chunksize=2048, delete=True):
    with open(filename, 'rb') as file_obj:
        while True:
            data = file_obj.read(chunksize)
            if not data:
                break
            yield data

    if delete:
        os.remove(filename)


def pos_int(value):
    value = int(value)
    if value < 0:
        raise ValueError("Negative values are not allowed.")
    return value


containment_enum = enum(
    ("overlaps", "contains"), False
)


def parse_format(string):
    parts = string.split(";")
    params = dict(
        param.strip().split("=", 1) for param in parts[1:]
    )
    return parts[0], params


class WCS20GetEOCoverageSetKVPDecoder(kvp.Decoder):
    eo_ids      = kvp.Parameter("eoid", type=typelist(str, ","), num=1, locator="eoid")
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    containment = kvp.Parameter(type=containment_enum, num="?")
    count       = kvp.Parameter(type=pos_int, num="?", default=MAXSIZE)
    format      = kvp.Parameter(num=1, type=parse_format)


class WCS20GetEOCoverageSetXMLDecoder(xml.Decoder):
    eo_ids      = xml.Parameter("/wcseo:EOID/text()", num="+", locator="eoid")
    subsets     = xml.Parameter("/wcs:DimensionTrim", type=parse_subset_xml, num="*")
    containment = xml.Parameter("/wcseo:containment/text()", type=containment_enum, locator="containment")
    count       = xml.Parameter("/@count", type=pos_int, num="?", default=MAXSIZE, locator="count")
    format      = xml.Parameter("/wcs:format/text()", type=parse_format, num=1, locator="format")

    namespaces = nsmap
