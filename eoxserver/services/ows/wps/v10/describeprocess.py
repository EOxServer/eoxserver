#-------------------------------------------------------------------------------
# $Id$
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


from eoxserver.core import Component, ExtensionPoint, implements
from eoxserver.core.decoders import kvp, xml, typelist
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface, VersionNegotiationInterface
)
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.exceptions import NoSuchProcessException
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ProcessDescriptionsXMLEncoder
)
from eoxserver.services.ows.wps.v10.util import nsmap


class WPS10DescribeProcessHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    service = "WPS"
    versions = ("1.0.0",)
    request = "DescribeProcess"

    processes = ExtensionPoint(ProcessInterface)


    def get_decoder(self, request):
        if request.method == "GET":
            return WPS10DescribeProcessKVPDecoder(request.GET)
        else:
            return WPS10DescribeProcessXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        identifiers = set(decoder.identifiers)

        used_processes = []
        for process in self.processes:
            if process.identifier in identifiers:
                identifiers.remove(process.identifier)
                used_processes.append(process)

        if len(identifiers):
            raise NoSuchProcessException(identifiers)

        encoder = WPS10ProcessDescriptionsXMLEncoder()
        return encoder.serialize(
            encoder.encode_process_descriptions(used_processes)
        ), encoder.content_type


class WPS10DescribeProcessKVPDecoder(kvp.Decoder):
    identifiers = kvp.Parameter("identifier", type=typelist(str, ","))


class WPS10DescribeProcessXMLDecoder(xml.Decoder):
    identifiers = xml.Parameter("ows:Identifier/text()", num="+")

    namespaces = nsmap






##########################################################################
from datetime import datetime
from eoxserver.services.ows.wps.parameters import LiteralData, ComplexData

class TestProcess(Component):
    implements(ProcessInterface)

    identifier = "id"
    title = "title"
    description = "description"
    metadata = ["a", "b"]
    profiles = ["p", "q"]

    inputs = {
        "X": int,
        "Y": datetime,
        "Z": LiteralData(
            "MyZIdenifier", description="myAbstract", 
            type=float, default=1., allowed_values=[1., 2., 3.]
        ),
        "V": LiteralData(
            "MyVIdenifier", description="VVV", 
            type=float, default=1., values_reference="http://foo.bar/value"
        )
    }

    outputs = {
        "X": int, 
        "Y": float,
        "Z": LiteralData(
            "MyZIdenifier", description="myAbstract", type=float,
            uoms=("metres", "feet")
        )
    }