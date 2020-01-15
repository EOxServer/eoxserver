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

from lxml.builder import ElementMaker
try:
    from django.core.urlresolvers import reverse
except ImportError:
    from django.urls import reverse
from django.shortcuts import get_object_or_404

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.xmltools import (
    XMLEncoder, NameSpace, NameSpaceMap
)
from eoxserver.resources.coverages import models
from eoxserver.services.opensearch.formats import get_formats
from eoxserver.services.opensearch.extensions import get_extensions
from eoxserver.services.opensearch.config import OpenSearchConfigReader


class OpenSearch11DescriptionEncoder(XMLEncoder):
    content_type = "application/opensearchdescription+xml"

    def __init__(self, search_extensions):
        ns_os = NameSpace("http://a9.com/-/spec/opensearch/1.1/", None)
        self.ns_param = ns_param = NameSpace(
            "http://a9.com/-/spec/opensearch/extensions/parameters/1.0/",
            "parameters"
        )
        ns_atom = NameSpace("http://www.w3.org/2005/Atom", "atom")
        nsmap = NameSpaceMap(ns_os, ns_param, ns_atom)
        for search_extension in search_extensions:
            nsmap.add(search_extension.namespace)
        self.OS = ElementMaker(namespace=ns_os.uri, nsmap=nsmap)
        self.PARAM = ElementMaker(namespace=ns_param.uri, nsmap=nsmap)
        self.ATOM = ElementMaker(namespace=ns_atom.uri, nsmap=nsmap)
        self.search_extensions = search_extensions

    def encode_description(self, request, collection, result_formats):
        """ Encode an OpenSearch 1.1 description document.
        """
        OS = self.OS
        description = OS("OpenSearchDescription",
            OS("ShortName",
                collection.identifier if collection is not None else ""
            ),
            OS("Description")
        )
        for method in ("GET", "POST"):
            description.extend([
                self.encode_url(
                    request, collection, result_format, method
                )
                for result_format in result_formats
            ])
        description.extend([
            OS("Contact"),
            OS("Tags", "CEOS-OS-BP-V1.1/L1"),
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

    def encode_url(self, request, collection, result_format, method):
        """ Encode a single opensearch URL, either for a specific collection, or
            the whole service.
        """
        if collection is not None:
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

        conf = OpenSearchConfigReader(get_eoxserver_config())
        search_url = request.build_absolute_uri(search_url)

        default_parameters = (
            dict(name="q", type="searchTerms", profiles=[
            ]),
            dict(name="count", type="count", min=0, max=conf.max_count),
            dict(name="startIndex", type="startIndex", min=0),
        )

        parameters = list(chain(default_parameters, *[
            [
                dict(parameter, **{"namespace": search_extension.namespace})
                for parameter in search_extension.get_schema(
                    collection,
                    models.Collection if collection is None else models.Product
                )
            ] for search_extension in self.search_extensions
        ]))

        query_template = "&".join(
            "%s={%s%s%s%s}" % (
                parameter["name"],
                parameter["namespace"].prefix
                if "namespace" in parameter else "",
                ":" if "namespace" in parameter else "",
                parameter["type"],
                "?" if parameter.get("optional", True) else ""
            )
            for parameter in parameters
        )

        url = self.OS("Url", *[
                self.encode_parameter(parameter, parameter.get("namespace"))
                for parameter in parameters
            ],
            type=result_format.mimetype,
            template="%s?%s" % (search_url, query_template)
            if method == "GET" else search_url,
            rel="results" if collection is not None else "collection", ** {
                self.ns_param("method"): method,
                self.ns_param("enctype"): "application/x-www-form-urlencoded",
                "indexOffset": "0"
            }
        )

        return url

    def encode_parameter(self, parameter, namespace):
        options = parameter.pop("options", [])
        profiles = parameter.pop("profiles", [])

        attributes = {"name": parameter["name"]}
        if namespace:
            attributes["value"] = "{%s:%s}" % (
                namespace.prefix, parameter.pop("type")
            )
        else:
            attributes["value"] = "{%s}" % parameter.pop("type")

        if 'min' in parameter:
            attributes['minInclusive'] = str(parameter['min'])

        if 'max' in parameter:
            attributes['maxInclusive'] = str(parameter['max'])

        pattern = parameter.get("pattern")
        if pattern:
            attributes["pattern"] = pattern

        return self.PARAM("Parameter", *[
            self.PARAM("Option", value=option, label=option)
            for option in options
        ] + [
            self.ATOM("link",
                rel="profile", href=profile["href"], title=profile["title"]
            )
            for profile in profiles
        ], minimum="0" if parameter.get("optional", True) else "1", maximum="1",
            **attributes
        )


class OpenSearch11DescriptionHandler(object):
    def handle(self, request, collection_id=None):
        collection = None
        if collection_id:
            collection = get_object_or_404(models.Collection,
                identifier=collection_id
            )

        encoder = OpenSearch11DescriptionEncoder([
            extension() for extension in get_extensions()
        ])
        return (
            encoder.serialize(
                encoder.encode_description(
                    request, collection, [format_() for format_ in get_formats()]
                )
            ),
            encoder.content_type
        )
