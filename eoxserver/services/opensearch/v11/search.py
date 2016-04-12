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

from eoxserver.core import Component, ExtensionPoint
from eoxserver.core.decoders import kvp
from eoxserver.core.util.xmltools import NameSpaceMap
from eoxserver.resources.coverages import models
from eoxserver.services.opensearch.interfaces import (
    SearchExtensionInterface, ResultFormatInterface
)


class SearchContext(namedtuple("SearchContext", [
        "total_count", "start_index", "page_size", "count",
        "parameters", "namespaces"
        ])):

    @property
    def page_count(self):
        return self.total_count // (self.page_size or self.count)

    @property
    def current_page(self):
        return self.start_index // (self.page_size or self.count)


class OpenSearch11SearchHandler(Component):
    search_extensions = ExtensionPoint(SearchExtensionInterface)
    result_formats = ExtensionPoint(ResultFormatInterface)

    def handle(self, request, collection_id=None, format_name=None):
        decoder = OpenSearch11BaseDecoder(request.GET)

        if collection_id:
            qs = models.Collection.objects.get(
                identifier=collection_id
            ).eo_objects.all()
        else:
            qs = models.Collection.objects.all()

        if decoder.search_terms:
            # TODO: search descriptions, summary etc once available
            qs = qs.filter(identifier__icontains=decoder.search_terms)

        namespaces = NameSpaceMap()
        all_parameters = {}
        for search_extension in self.search_extensions:
            # get all search extension related parameters and translate the name
            # to the actual parameter name
            params = dict(
                (parameter["type"], request.GET[parameter["name"]])
                for parameter in search_extension.get_schema()
                if parameter["name"] in request.GET
            )
            qs = search_extension.filter(qs, params)
            namespaces.add(search_extension.namespace)
            all_parameters[search_extension.namespace.prefix] = params

        total_count = len(qs)

        if decoder.start_index and not decoder.count:
            qs = qs[decoder.start_index:]
        elif decoder.start_index and decoder.count:
            qs = qs[decoder.start_index:decoder.start_index+decoder.count]
        elif decoder.count:
            qs = qs[:decoder.count]

        try:
            result_format = next(
                result_format
                for result_format in self.result_formats
                if result_format.name == format_name
            )
        except StopIteration:
            raise Http404("No such result format '%s'." % format_name)

        search_context = SearchContext(
            total_count, decoder.start_index, decoder.count, len(qs),
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
    count = kvp.Parameter("count", pos_int, num="?", default=None)
    output_encoding = kvp.Parameter("outputEncoding", num="?", default="UTF-8")
