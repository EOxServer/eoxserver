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


from lxml.builder import ElementMaker
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from eoxserver.core import Component, ExtensionPoint
from eoxserver.core.util.xmltools import (
    XMLEncoder, NameSpace, NameSpaceMap
)
from eoxserver.resources.coverages import models
from eoxserver.services.opensearch.interfaces import (
    SearchExtensionInterface, ResultFormatInterface
)


class OpenSearch11DescriptionEncoder(XMLEncoder):
    content_type = "application/opensearchdescription+xml"

    def __init__(self, search_extensions):
        ns_os = NameSpace("http://a9.com/-/spec/opensearch/1.1/", None)
        ns_param = NameSpace(
            "http://a9.com/-/spec/opensearch/extensions/parameters/1.0/",
            "parameters"
        )
        nsmap = NameSpaceMap(ns_os, ns_param)
        for search_extension in search_extensions:
            nsmap.add(search_extension.namespace)
        self.OS = ElementMaker(namespace=ns_os.uri, nsmap=nsmap)
        self.PARAM = ElementMaker(namespace=ns_param.uri, nsmap=nsmap)
        self.search_extensions = search_extensions

    def encode_description(self, request, collection, result_formats):
        OS = self.OS
        description = OS("OpenSearchDescription",
            OS("ShortName", collection.identifier if collection else ""),
            OS("Description")
        )
        description.extend([
            self.encode_url(
                request, collection, result_format
            )
            for result_format in result_formats
        ]),
        description.extend([
            OS("Contact"),
            OS("LongName"),
            OS("Developer"),
            OS("Attribution"),
            OS("SyndicationRight", "open"),
            OS("AdultContent"),
            OS("Language"),
            OS("InputEncoding"),
            OS("OutputEncoding")
        ])
        return description

    def encode_url(self, request, collection, result_format):
        if collection:
            search_url = reverse("opensearch:collection:search",
                kwargs={
                    "collection_id": collection.identifier,
                    "format_name": result_format.name
                }
            )
        else:
            search_url = reverse("opensearch:search",
                kwargs={
                    "format_name": result_format.name
                }
            )

        search_url = request.build_absolute_uri(search_url)

        query_template = "&".join(
            "%s={%s:%s%s}" % (
                parameter["name"], search_extension.namespace.prefix,
                parameter["type"],
                "?" if parameter.get("optional", True) else ""
            )
            for search_extension in self.search_extensions
            for parameter in search_extension.get_schema(collection)
        )

        url = self.OS("Url", *[
                self.encode_parameter(parameter, search_extension.namespace)
                for search_extension in self.search_extensions
                for parameter in search_extension.get_schema(collection)
            ],
            type=result_format.mimetype,
            template=(
                "%s?q={searchTerms?}&count={count?}"
                "&startIndex={startIndex?}&%s" % (search_url, query_template)
            ),
            rel="results" if collection else "collection"
        )

        return url

    def encode_parameter(self, parameter, namespace):
        options = parameter.pop("options", [])
        parameter["value"] = "{%s:%s}" % (
            namespace.prefix, parameter.pop("type")
        )
        return self.PARAM("Parameter", *[
            self.PARAM("Option", value=option, label=option)
            for option in options
        ], **parameter)


class OpenSearch11DescriptionHandler(Component):
    search_extensions = ExtensionPoint(SearchExtensionInterface)
    result_formats = ExtensionPoint(ResultFormatInterface)

    def handle(self, request, collection_id=None):
        collection = None
        if collection_id:
            collection = get_object_or_404(models.Collection,
                identifier=collection_id
            )

        encoder = OpenSearch11DescriptionEncoder(self.search_extensions)
        return (
            encoder.serialize(
                encoder.encode_description(
                    request, collection, self.result_formats
                )
            ),
            encoder.content_type
        )
