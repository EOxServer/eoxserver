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

from eoxserver.core.decoders import kvp, xml
from eoxserver.services.ows.wps.util import get_processes
from eoxserver.services.ows.wps.v10.encoders import WPS10CapabilitiesXMLEncoder
from eoxserver.services.ows.wps.v10.util import nsmap


class WPS10GetCapabilitiesHandler(object):
    """ WPS 1.0 GetCapabilities service handler. """

    service = "WPS"
    versions = ("1.0.0",)
    request = "GetCapabilities"
    methods = ['GET', 'POST']

    def handle(self, request):
        """ Handle HTTP request. """
        encoder = WPS10CapabilitiesXMLEncoder()
        return encoder.serialize(encoder.encode_capabilities(get_processes()))


class WPS10GetCapabilitiesKVPDecoder(kvp.Decoder):
    """ WPS 1.0 GetCapabilities HTTP/GET KVP request decoder. """
    #pylint: disable=too-few-public-methods
    #acceptversions = kvp.Parameter(type=typelist(str, ","), num="?")
    language = kvp.Parameter(num="?")


class WPS10GetCapabilitiesXMLDecoder(xml.Decoder):
    """ WPS 1.0 DescribeProcess HTTP/POST XML request decoder. """
    #pylint: disable=too-few-public-methods
    #acceptversions = xml.Parameter("/ows:AcceptVersions/ows:Version/text()", num="*")
    language = xml.Parameter("/ows:AcceptLanguages/ows:Language/text()", num="*")
    namespaces = nsmap
