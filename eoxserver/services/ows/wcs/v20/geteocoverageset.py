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
    nsmapGetEoCoverageSet, parse_subset_kvp, parse_subset_xml, parse_scaleaxis_kvp,
    parse_scaleaxis_xml, parse_scaleextent_kvp, parse_scaleextent_xml,
    parse_scalesize_kvp, parse_scalesize_xml, parse_interpolation
)
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams
from eoxserver.services.ows.common.config import WCSEOConfigReader
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.exceptions import (
    NoSuchDatasetSeriesOrCoverageException, InvalidRequestException,
    InvalidSubsettingException
)


logger = logging.getLogger(__name__)

DEFAULT_DEFAULT_PACKAGE_FORMAT = 'application/gzip'

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


class TempfileIterator(object):
    def __init__(self, filename, chunksize=2048, delete=True):
        self.filename = filename
        self.chunksize = chunksize
        self.delete = delete

    def close(self):
        if self.delete and os.path.exists(self.filename):
            os.remove(self.filename)

    def __iter__(self):
        with open(self.filename, 'rb') as file_obj:
            while True:
                data = file_obj.read(self.chunksize)
                if not data:
                    break
                yield data
        self.close()


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
        if decoder.apply_subset:
            subsets = Subsets(decoder.subsets, crs=decoder.subsettingcrs)
        else:
            subsets = Subsets([], crs=decoder.subsettingcrs)

        scalefactor = decoder.scalefactor
        scales = list(
            chain(decoder.scaleaxes, decoder.scalesize, decoder.scaleextent)
        )

        # check scales validity: ScaleFactor and any other scale
        if scalefactor and scales:
            raise InvalidRequestException(
                "ScaleFactor and any other scale operation are mutually "
                "exclusive.", locator="scalefactor"
            )

        # check scales validity: Axis uniqueness
        axes = set()
        for scale in scales:
            if scale.axis in axes:
                raise InvalidRequestException(
                    "Axis '%s' is scaled multiple times." % scale.axis,
                    locator=scale.axis
                )
            axes.add(scale.axis)

        return WCS20CoverageRenderParams(
            coverage, subsets, None, decoder.format,
            decoder.outputcrs, decoder.mediatype, decoder.interpolation,
            scalefactor, scales, {}, request
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

    def get_pacakge_writer(self, package_format, params):
        for writer in get_package_writers():
            if writer.supports(package_format, params):
                return writer

        raise InvalidRequestException(
            "Package format '%s' is not supported." % package_format,
            locator="packageFormat"
        )

    @property
    def constraints(self):
        reader = WCSEOConfigReader(get_eoxserver_config())
        return {
            "CountDefault": reader.paging_count_default,
        }

    def handle(self, request):
        decoder = self.get_decoder(request)
        eo_ids = decoder.eo_ids

        package_format = decoder.package_format
        if package_format:
            package_format, format_params = package_format
        else:
            package_format = getattr(
                settings, 'EOXS_DEFAULT_PACKAGE_FORMAT',
                DEFAULT_DEFAULT_PACKAGE_FORMAT
            )
            format_params = {}
        writer = self.get_pacakge_writer(package_format, format_params)

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

        # limit coverages according to the requested or default count
        offset = decoder.start_index
        coverages_qs = all_coverages_qs[offset:offset + count]

        fd, pkg_filename = tempfile.mkstemp()
        tmp = os.fdopen(fd)
        tmp.close()
        package = writer.create_package(
            pkg_filename, package_format, format_params
        )

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

        # TODO: if decoder.mediatype is set to multipart/* add a dataset
        # series description

        mime_type = writer.get_mime_type(
            package, package_format, format_params
        )
        ext = writer.get_file_extension(
            package, package_format, format_params
        )
        writer.cleanup(package)
        response = StreamingHttpResponse(
            TempfileIterator(pkg_filename), mime_type
        )
        response["Content-Disposition"] = 'inline; filename="ows%s"' % ext
        response["Content-Length"] = str(os.path.getsize(pkg_filename))

        return response


def pos_int(value):
    value = int(value)
    if value < 0:
        raise ValueError("Negative values are not allowed.")
    return value


containment_enum = enum(
    ("overlaps", "contains"), False
)


def parse_package_format(string):
    parts = string.split(";")
    params = dict(
        param.strip().split("=", 1) for param in parts[1:]
    )
    return parts[0], params


def parse_apply_subset(value):
    value = value.upper()
    if value == 'TRUE':
        return True
    elif value == 'FALSE':
        return False
    raise ValueError("Invalid value for 'applySubset' parameter.")


class WCS20GetEOCoverageSetKVPDecoder(kvp.Decoder):
    eo_ids      = kvp.Parameter("eoid", type=typelist(str, ","), num=1, locator="eoid")
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    containment = kvp.Parameter(type=containment_enum, num="?")
    count       = kvp.Parameter(type=pos_int, num="?", default=MAXSIZE)
    start_index = kvp.Parameter("startIndex", type=pos_int, num="?", default=0)
    package_format = kvp.Parameter("packageFormat", num="?", type=parse_package_format)
    mediatype   = kvp.Parameter("mediatype", num="?")
    format      = kvp.Parameter("format", num="?")
    apply_subset = kvp.Parameter("applySubset", type=parse_apply_subset, default=True, num="?")
    scalefactor = kvp.Parameter("scalefactor", type=float, num="?")
    scaleaxes   = kvp.Parameter("scaleaxes", type=typelist(parse_scaleaxis_kvp, ","), default=(), num="?")
    scalesize   = kvp.Parameter("scalesize", type=typelist(parse_scalesize_kvp, ","), default=(), num="?")
    scaleextent = kvp.Parameter("scaleextent", type=typelist(parse_scaleextent_kvp, ","), default=(), num="?")
    interpolation = kvp.Parameter("interpolation", type=parse_interpolation, num="?")
    subsettingcrs = kvp.Parameter("subsettingcrs", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")


class WCS20GetEOCoverageSetXMLDecoder(xml.Decoder):
    eo_ids      = xml.Parameter("wcseo11:eoId/text()", num="+", locator="eoid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*")
    containment = xml.Parameter("wcseo11:containment/text()", num="?", type=containment_enum, locator="containment")
    count       = xml.Parameter("@count", type=pos_int, num="?", default=MAXSIZE, locator="count")
    start_index = xml.Parameter("@startIndex", type=pos_int, num="?", default=0, locator="startIndex")
    package_format = xml.Parameter("wcseo11:packageFormat/text()", type=parse_package_format, num="?", locator="packageFormat")
    mediatype   = xml.Parameter("wcseo11:mediaType/text()", num="?", locator="mediatype")
    format      = xml.Parameter("wcseo11:format/text()", num="?", locator="format")
    apply_subset = xml.Parameter("wcseo11:applySubset/text()", type=parse_apply_subset, num="?", locator="format")
    scalefactor = xml.Parameter("wcs:Extension/scal:ScaleByFactor/scal:scaleFactor/text()", type=float, num="?", locator="scalefactor")
    scaleaxes   = xml.Parameter("wcs:Extension/scal:ScaleByAxesFactor/scal:ScaleAxis", type=parse_scaleaxis_xml, num="*", default=(), locator="scaleaxes")
    scalesize   = xml.Parameter("wcs:Extension/scal:ScaleToSize/scal:TargetAxisSize", type=parse_scalesize_xml, num="*", default=(), locator="scalesize")
    scaleextent = xml.Parameter("wcs:Extension/scal:ScaleToExtent/scal:TargetAxisExtent", type=parse_scaleextent_xml, num="*", default=(), locator="scaleextent")
    interpolation = xml.Parameter("wcs:Extension/int:Interpolation/int:globalInterpolation/text()", type=parse_interpolation, num="?", locator="interpolation")
    subsettingcrs = xml.Parameter("wcs:Extension/crs:subsettingCrs/text()", num="?", locator="subsettingcrs")
    outputcrs   = xml.Parameter("wcs:Extension/crs:outputCrs/text()", num="?", locator="outputcrs")

    namespaces = nsmapGetEoCoverageSet
