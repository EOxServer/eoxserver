#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

from collections import namedtuple

from django.http import Http404
from django.db.models import Q

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import kvp
from eoxserver.core.util.xmltools import NameSpaceMap
from eoxserver.resources.coverages import models
from eoxserver.services.opensearch.config import (
    get_opensearch_record_model, OpenSearchConfigReader,
    get_opensearch_default_ordering,
)
from eoxserver.services.opensearch.formats import get_formats
from eoxserver.services.opensearch.extensions import get_extensions


class SearchContext(namedtuple("SearchContext", [
        "total_count", "start_index", "page_size", "count",
        "parameters", "namespaces"
        ])):

    @property
    def page_count(self):
        divisor = (self.page_size or self.count)
        if divisor == 0:
            return 1

        return self.total_count // divisor

    @property
    def current_page(self):
        divisor = (self.page_size or self.count)
        if divisor == 0:
            return 1

        return self.start_index // divisor


class OpenSearch11SearchHandler(object):
    def handle(self, request, collection_id=None, format_name=None):
        if request.method == "GET":
            request_parameters = request.GET
        elif request.method == "POST":
            request_parameters = request.POST
        else:
            raise Exception("Invalid request method '%s'." % request.method)

        decoder = OpenSearch11BaseDecoder(request_parameters)

        if collection_id:
            # search for products in that collection and coverages not
            # associated with a product but contained in this collection

            ModelClass = get_opensearch_record_model()

            qs = ModelClass.objects.all()
            if ModelClass == models.EOObject:
                qs = qs.filter(
                    Q(product__collections__identifier=collection_id) |
                    Q(
                        coverage__collections__identifier=collection_id,
                        coverage__parent_product__isnull=True
                    )
                ).select_subclasses()
            else:
                qs = qs.filter(collections__identifier=collection_id)

        else:
            qs = models.Collection.objects.all()

        if decoder.search_terms:
            # TODO: search descriptions, summary etc once available
            qs = qs.filter(identifier__icontains=decoder.search_terms)

        namespaces = NameSpaceMap()
        all_parameters = {}
        for search_extension_class in get_extensions():
            # get all search extension related parameters and translate the name
            # to the actual parameter name
            search_extension = search_extension_class()

            params = dict(
                (parameter["type"], request_parameters[parameter["name"]])
                for parameter in search_extension.get_schema(
                    model_class=qs.model
                )
                if parameter["name"] in request_parameters
            )

            qs = search_extension.filter(qs, params)
            namespaces.add(search_extension.namespace)
            all_parameters[search_extension.namespace.prefix] = params

        # apply default ordering (which is None by default)
        default_ordering = get_opensearch_default_ordering()
        if not qs.ordered and default_ordering is not None:
            qs = qs.order_by(default_ordering)

        # use [:] here, otherwise the queryset would be evaluated and return
        # lists upon slicing
        total_count = qs[:].count()

        # read the configuration and determine the count parameter
        conf = OpenSearchConfigReader(get_eoxserver_config())
        requested_count = min(
            decoder.count if decoder.count is not None else conf.default_count,
            conf.max_count
        )

        start_index = decoder.start_index

        # if count  is zero, then return an 'empty' queryset
        if requested_count == 0:
            qs = models.EOObject.objects.none()
        else:
            qs = qs[start_index:start_index+requested_count]

        result_count = qs[:].count()

        # shortcut to eliminate possible very long DB query
        if result_count == 0:
            qs = qs.model.objects.none()

        try:
            result_format = next(
                result_format()
                for result_format in get_formats()
                if result_format.name == format_name
            )
        except StopIteration:
            raise Http404("No such result format '%s'." % format_name)

        search_context = SearchContext(
            total_count, start_index,
            requested_count, result_count,
            all_parameters, namespaces
        )

        return (
            result_format.encode(request, collection_id, qs, search_context),
            result_format.mimetype
        )


def pos_int_zero(raw):
    value = int(raw)
    if value < 0:
        raise ValueError("Value is negative")
    return value


def pos_int(raw):
    value = int(raw)
    if value < 1:
        raise ValueError("Value is negative or zero")
    return value


class OpenSearch11BaseDecoder(kvp.Decoder):
    search_terms = kvp.Parameter("q", num="?")
    start_index = kvp.Parameter("startIndex", pos_int_zero, num="?", default=0)
    count = kvp.Parameter("count", pos_int_zero, num="?", default=None)
    output_encoding = kvp.Parameter("outputEncoding", num="?", default="UTF-8")
