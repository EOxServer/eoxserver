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

from eoxserver.core.decoders import kvp, xml, upper, typelist
from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap
from eoxserver.core.util.multiparttools import get_multipart_related_root
from eoxserver.services.ows.version import parse_version_string

DEFAULT_CONTENT_TYPE = "application/xml"

ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
ns_ows10 = NameSpace("http://www.opengis.net/ows/1.0", "ows10")
ns_ows11 = NameSpace("http://www.opengis.net/ows/1.1", "ows11")
ns_ows20 = NameSpace("http://www.opengis.net/ows/2.0", "ows20")

nsmap = NameSpaceMap(ns_ows10, ns_ows11, ns_ows20)


def get_decoder(request):
    """ Convenience function to return the right OWS Common request deocder for
        the given `django.http.HttpRequest`.
    """
    if request.method == "GET":
        return OWSCommonKVPDecoder(request.GET)
    if request.method == "POST":
        return _decode_post_request(request.body, request.headers)
    raise ValueError(f"Unexpected request method {request.method}!")


def _decode_post_request(body, headers, level=0):
    content_type = headers.get("Content-Type")
    mime_type, _, _ = (content_type or DEFAULT_CONTENT_TYPE).partition(";")
    if mime_type in ("application/xml", "text/xml"):
        return OWSCommonXMLDecoder(body)
    if level == 0 and mime_type == "multipart/related":
        body, headers = get_multipart_related_root(body, headers)
        return _decode_post_request(body.tobytes(), headers, level + 1)
    raise ValueError(f"Unsupported {mime_type} request format!")


class OWSCommonKVPDecoder(kvp.Decoder):
    service         = kvp.Parameter("service", type=upper, num="?")
    version         = kvp.Parameter("version", type=parse_version_string, num="?")
    request         = kvp.Parameter("request", type=upper)
    acceptversions  = kvp.Parameter(type=typelist(parse_version_string, ","), num="?")


class OWSCommonXMLDecoder(xml.Decoder):
    service         = xml.Parameter("@service", type=upper, num="?")
    version         = xml.Parameter("@version", type=parse_version_string, num="?")
    request         = xml.Parameter("local-name()", type=upper)
    acceptversions  = xml.Parameter(
        "ows10:AcceptVersions/ows10:Version/text() "
        "| ows11:AcceptVersions/ows11:Version/text() "
        "| ows20:AcceptVersions/ows20:Version/text()",
        type=parse_version_string, num="*"
    )

    namespaces = nsmap
