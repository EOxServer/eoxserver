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

from itertools import chain

from lxml.etree import CDATA
from lxml.builder import ElementMaker
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.utils.http import urlencode

from eoxserver.core.util.xmltools import etree, NameSpace, NameSpaceMap, typemap
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.opensearch.formats.base import (
    BaseFeedResultFormat, ns_opensearch, ns_dc, ns_atom, ns_media, ns_owc,
    ns_eoxs
)
from eoxserver.resources.coverages import models


# namespace declarations
ns_georss = NameSpace("http://www.georss.org/georss", "georss")
ns_gml = NameSpace("http://www.opengis.net/gml", "gml")

# namespace map
nsmap = NameSpaceMap(
    ns_georss, ns_gml, ns_opensearch, ns_dc, ns_atom, ns_media, ns_owc,
    ns_eoxs
)

# Element factories
GEORSS = ElementMaker(namespace=ns_georss.uri, nsmap=nsmap)
GML = ElementMaker(namespace=ns_gml.uri, nsmap=nsmap)
RSS = ElementMaker(typemap=typemap)


class RSSResultFormat(BaseFeedResultFormat):
    """ RSS result format.
    """

    mimetype = "application/rss+xml"
    name = "rss"

    def encode(self, request, collection_id, queryset, search_context):
        # prepare RSS factory with additional namespaces from search context
        namespaces = dict(nsmap)
        namespaces.update(search_context.namespaces)
        RSS = ElementMaker(namespace=None, nsmap=namespaces)

        tree = RSS("rss",
            RSS("channel",
                RSS("title", "%s Search" % collection_id),
                RSS("link", request.build_absolute_uri()),
                RSS("description"),
                *chain(
                    self.encode_opensearch_elements(search_context),
                    self.encode_feed_links(request, search_context), [
                        self.encode_item(
                            request, collection_id, item, search_context
                        )
                        for item in queryset
                    ]
                )
            ),
            version="2.0"
        )
        return etree.tostring(tree, pretty_print=True)

    def encode_item(self, request, collection_id, item, search_context):
        link_url = request.build_absolute_uri(
            "%s?%s" % (
                reverse("ows"), urlencode(dict(
                    service="WCS",
                    version="2.0.1",
                    request="DescribeCoverage",
                    coverageId=item.identifier,
                ))
            )
        )

        rss_item = RSS("item",
            RSS("title", item.identifier),
            RSS("description", CDATA(item.identifier)),
            RSS("link", link_url),
        )

        if "geo" in search_context.parameters:
            rss_item.append(RSS("guid", request.build_absolute_uri()))
        else:
            rss_item.append(RSS("guid", item.identifier, isPermaLink="false"))

        rss_item.extend(self.encode_item_links(request, collection_id, item))

        # TODO: remove this for the general dc:date?
        if item.begin_time and item.end_time:
            rss_item.append(
                GML("TimePeriod",
                    GML("beginPosition", isoformat(item.begin_time)),
                    GML("endPosition", isoformat(item.end_time)),
                    **{ns_gml("id"): item.identifier}
                )
            )

        rss_item.extend(self.encode_spatio_temporal(item))
        if isinstance(item, models.Product):
            rss_item.extend(self.encode_coverage_ids(item.coverages.all()))
        return rss_item
