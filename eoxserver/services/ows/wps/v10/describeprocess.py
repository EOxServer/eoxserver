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

from eoxserver.core.decoders import kvp, xml, typelist
from eoxserver.services.ows.wps.util import get_processes
from eoxserver.services.ows.wps.exceptions import NoSuchProcessError
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ProcessDescriptionsXMLEncoder
)
from eoxserver.services.ows.wps.v10.util import nsmap


class WPS10DescribeProcessHandler(object):
    """ WPS 1.0 DescribeProcess service handler. """

    service = "WPS"
    versions = ("1.0.0",)
    request = "DescribeProcess"
    methods = ['GET', 'POST']

    @staticmethod
    def get_decoder(request):
        """ Get the WPS request decoder. """
        if request.method == "GET":
            return WPS10DescribeProcessKVPDecoder(request.GET)
        else:
            return WPS10DescribeProcessXMLDecoder(request.body)


    def handle(self, request):
        """ Handle HTTP request. """
        decoder = self.get_decoder(request)
        identifiers = set(decoder.identifiers)

        used_processes = []
        for process in get_processes():
            process_identifier = (
                getattr(process, 'identifier', None) or type(process).__name__
            )
            if process_identifier in identifiers:
                identifiers.remove(process_identifier)
                used_processes.append(process)

        for identifier in identifiers:
            raise NoSuchProcessError(identifier)

        encoder = WPS10ProcessDescriptionsXMLEncoder()
        return encoder.serialize(
            encoder.encode_process_descriptions(used_processes)
        )


class WPS10DescribeProcessKVPDecoder(kvp.Decoder):
    """ WPS 1.0 DescribeProcess HTTP/GET KVP request decoder. """
    #pylint: disable=too-few-public-methods
    identifiers = kvp.Parameter("identifier", type=typelist(str, ","))


class WPS10DescribeProcessXMLDecoder(xml.Decoder):
    """ WPS 1.0 DescribeProcess HTTP/POST XML request decoder. """
    #pylint: disable=too-few-public-methods
    identifiers = xml.Parameter("ows:Identifier/text()", num="+")
    namespaces = nsmap
