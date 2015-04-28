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


from copy import deepcopy
from itertools import product
from urllib import urlencode

from lxml.builder import ElementMaker
from django.core.urlresolvers import reverse

from eoxserver.core import Component, ExtensionPoint
from eoxserver.core.util.xmltools import (
    XMLEncoder, NameSpace, NameSpaceMap
)
from eoxserver.resources.coverages import models
from eoxserver.services.opensearch.interfaces import (
    SearchExtensionInterface, ResultFormatInterface
)


ns_os = NameSpace("http://a9.com/-/spec/opensearch/1.1/", None)
nsmap = NameSpaceMap(ns_os)

OS = ElementMaker(namespace=ns_os.uri, nsmap=nsmap)


class OpenSearch11DescriptionEncoder(XMLEncoder):
    content_type = "application/opensearchdescription+xml"

    def encode_description(self, collections, search_extensions, result_formats,
                           request=None):
        description = OS("OpenSearchDescription",
            OS("ShortName"),
            OS("Description")
        )
        description.extend([
            self.encode_url(
                collection, search_extensions, result_format, request
            )
            for collection, result_format
            in product(collections, result_formats)
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

    def encode_url(self, collection, search_extensions, result_format, request):
        search_url = reverse("opensearch_search",
            #kwargs={"collection_id": collection.identifier}
            #args=[collection.identifier]
        )
        if request:
            search_url = request.build_absolute_uri(search_url)

        query_template = "&".join(
            "%s={%s:%s%s}" % (
                name, search_extension.namespace.prefix, parameter[0],
                "?" if parameter[1] else ""
            )
            for search_extension in search_extensions
            for name, parameter in search_extension.schema.items()
        )

        return OS("Url",
            type=result_format.mimetype,
            template="%s?q={searchTerms}&count={count?}"
                "&startIndex={startIndex?}&%s&format=%s" % (
                    search_url, query_template, result_format.name
                )
        )


class OpenSearch11DescriptionHandler(Component):
    search_extensions = ExtensionPoint(SearchExtensionInterface)
    result_formats = ExtensionPoint(ResultFormatInterface)

    def handle(self, request):
        encoder = OpenSearch11DescriptionEncoder()
        collections = models.Collection.objects.all()
        return (
            encoder.serialize(
                encoder.encode_description(
                    collections, self.search_extensions, self.result_formats,
                    request
                )
            ),
            encoder.content_type
        )
