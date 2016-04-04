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
from django.http import QueryDict

from eoxserver.core import implements, Component
from eoxserver.core.util.xmltools import etree, NameSpace, NameSpaceMap
from eoxserver.services.opensearch.interfaces import ResultFormatInterface


# namespace declarations
ns_atom = NameSpace("http://www.w3.org/2005/Atom", "atom")
ns_opensearch = NameSpace("http://a9.com/-/spec/opensearch/1.1/", "opensearch")

# namespace map
nsmap = NameSpaceMap(ns_atom, ns_opensearch)

# Element factories
RSS = ElementMaker(namespace=None, nsmap=nsmap)
ATOM = ElementMaker(namespace=ns_atom.uri, nsmap=nsmap)
OS = ElementMaker(namespace=ns_opensearch.uri, nsmap=nsmap)


class RSSResultFormat(Component):
    """ RSS result format.
    """

    implements(ResultFormatInterface)

    mimetype = "application/rss+xml"
    name = "rss"

    def encode(self, request, collection_id, queryset, start_index, total_count):
        tree = RSS("rss",
            RSS("channel",
                RSS("title", "%s Search" % collection_id),
                RSS("link", request.build_absolute_uri()),
                RSS("description"),
                OS("totalResults", str(total_count)),
                OS("startIndex", str(start_index or 0)),
                OS("itemsPerPage", str(len(queryset))),
                ATOM("link",
                    rel="search", type="application/opensearchdescription+xml",
                    href=request.build_absolute_uri(
                        reverse("opensearch:description")
                    )
                ),
                ATOM("link",
                    rel="self", type="application/rss+xml",
                    href="%s?%s" % (
                        request.build_absolute_uri(), request.GET.urlencode()
                    )
                ),
                # OS("Query", role="request", ), # TODO: params
                *[
                    self.encode_item(request, item) for item in queryset
                ]
            ),
            version="2.0"
        )
        return etree.tostring(tree, pretty_print=True)

    def encode_item(self, request, item):
        qdict = QueryDict(
            "service=WCS&version=2.0.1&request=DescribeCoverage", mutable=True
        )
        qdict["coverageId"] = item.identifier
        link_url = request.build_absolute_uri(
            "%s?%s" % (reverse("ows"), qdict.urlencode())
        )

        return RSS("item",
            RSS("title", item.identifier),
            # RSS("description", ), # TODO
            RSS("link", link_url),
            RSS("guid", item.identifier, isPermaLink="false")
        )
