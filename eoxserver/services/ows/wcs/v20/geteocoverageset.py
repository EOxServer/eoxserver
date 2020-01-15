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


import os
import tempfile
import logging
from itertools import chain
import mimetypes

from django.db.models import Q
from django.http import HttpResponse
try:
    from django.http import StreamingHttpResponse
except:
    StreamingHttpResponse = HttpResponse

from django.utils.six import MAXSIZE
from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml, kvp, typelist, enum
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface,
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, parse_subset_kvp, parse_subset_xml
)
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams
from eoxserver.services.ows.common.config import WCSEOConfigReader
from eoxserver.services.ows.wcs.interfaces import (
    WCSCoverageRendererInterface, PackageWriterInterface
)
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.exceptions import (
    NoSuchDatasetSeriesOrCoverageException, InvalidRequestException,
    InvalidSubsettingException
)


logger = logging.getLogger(__name__)


class WCS20GetEOCoverageSetHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    coverage_renderers = ExtensionPoint(WCSCoverageRendererInterface)
    package_writers = ExtensionPoint(PackageWriterInterface)

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
        for renderer in self.coverage_renderers:
            if renderer.supports(params):
                return renderer

        raise InvalidRequestException(
            "Could not find renderer for coverage '%s'."
        )

    def get_pacakge_writer(self, format, params):
        for writer in self.package_writers:
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

        if len(eo_ids) == 0:
            raise

        # fetch a list of all requested EOObjects
        available_ids = models.EOObject.objects.filter(
            identifier__in=eo_ids
        ).values_list("identifier", flat=True)

        # match the requested EOIDs against the available ones. If any are
        # requested, that are not available, raise and exit.
        failed = [eo_id for eo_id in eo_ids if eo_id not in available_ids]
        if failed:
            raise NoSuchDatasetSeriesOrCoverageException(failed)

        collections_qs = subsets.filter(models.Collection.objects.filter(
            identifier__in=eo_ids
        ), containment="overlaps")

        # create a set of all indirectly referenced containers by iterating
        # recursively. The containment is set to "overlaps", to also include
        # collections that might have been excluded with "contains" but would
        # have matching coverages inserted.

        def recursive_lookup(super_collection, collection_set):
            sub_collections = models.Collection.objects.filter(
                collections__in=[super_collection.pk]
            ).exclude(
                pk__in=map(lambda c: c.pk, collection_set)
            )
            sub_collections = subsets.filter(sub_collections, "overlaps")

            # Add all to the set
            collection_set |= set(sub_collections)

            for sub_collection in sub_collections:
                recursive_lookup(sub_collection, collection_set)

        collection_set = set(collections_qs)
        for collection in set(collection_set):
            recursive_lookup(collection, collection_set)

        collection_pks = map(lambda c: c.pk, collection_set)

        # Get all either directly referenced coverages or coverages that are
        # within referenced containers. Full subsetting is applied here.

        coverages_qs = models.Coverage.objects.filter(
            Q(identifier__in=eo_ids) | Q(collections__in=collection_pks)
        )
        coverages_qs = subsets.filter(coverages_qs, containment=containment)

        # save a reference before limits are applied to obtain the full number
        # of matched coverages.
        coverages_no_limit_qs = coverages_qs

        # compute how many (if any) coverages can be retrieved. This depends on
        # the "count" parameter and default setting. Also, if we already
        # exceeded the count, limit the number of dataset series aswell
        """
        if inc_dss_section:
            num_collections = len(collection_set)
        else:
            num_collections = 0

        if num_collections < count and inc_cov_section:
            coverages_qs = coverages_qs.order_by("identifier")[:count - num_collections]
        elif num_collections == count or not inc_cov_section:
            coverages_qs = []
        else:
            coverages_qs = []
            collection_set = sorted(collection_set, key=lambda c: c.identifier)[:count]
        """

        # get a number of coverages that *would* have been included, but are not
        # because of the count parameter
        # count_all_coverages = coverages_no_limit_qs.count()

        # TODO: if containment is "within" we need to check all collections
        # again
        if containment == "within":
            collection_set = filter(lambda c: subsets.matches(c), collection_set)

        coverages = []
        dataset_series = []

        # finally iterate over everything that has been retrieved and get
        # a list of dataset series and coverages to be encoded into the response
        for eo_object in chain(coverages_qs, collection_set):
            if issubclass(eo_object.real_type, models.Coverage):
                coverages.append(eo_object.cast())

        fd, pkg_filename = tempfile.mkstemp()
        tmp = os.fdopen(fd)
        tmp.close()
        package = writer.create_package(pkg_filename, format, format_params)

        for coverage in coverages:
            params = self.get_params(coverage, decoder, request)
            renderer = self.get_renderer(params)
            result_set = renderer.render(params)
            all_filenames = set()
            for result_item in result_set:
                if not result_item.filename:
                    ext = mimetypes.guess_extension(result_item.content_type)
                    filename = coverage.identifier + ext
                else:
                    filename = result_item.filename
                if filename in all_filenames:
                    continue  # TODO: create new filename
                all_filenames.add(filename)
                location = "%s/%s" % (coverage.identifier, filename)
                writer.add_to_package(
                    package, result_item.data_file, result_item.size, location
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
    with open(filename) as file_obj:
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
