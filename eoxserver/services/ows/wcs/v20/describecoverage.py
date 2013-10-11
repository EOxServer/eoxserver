#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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


from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist, upper
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.v20.util import nsmap
from eoxserver.services.ows.wcs.v20.encoders import (
    WCS20CoverageDescriptionXMLEncoder
)
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.core.util.xmltools import DOMElementToXML



class WCS20DescribeCoverageHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = "DescribeCoverage"


    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20DescribeCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20DescribeCoverageXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)
        coverage_ids = decoder.coverage_ids

        if len(coverage_ids) == 0:
            raise

        coverages = []
        for coverage_id in coverage_ids:
            try:
                coverages.append(
                    models.Coverage.objects.get(identifier__exact=coverage_id)
                )
            except models.Coverage.DoesNotExist:
                raise NoSuchCoverage(coveage_id)

        # TODO: remove this at some point and use a renderer plugin

        encoder = WCS20EOXMLEncoder()
        return (
            encoder.serialize(
                encoder.encode_coverage_descriptions(coverages),
                pretty_print=True
            ),
            encoder.content_type
        )


class WCS20DescribeCoverageKVPDecoder(kvp.Decoder):
    coverage_ids = kvp.Parameter("coverageid", type=typelist(str, ","), num=1)


class WCS20DescribeCoverageXMLDecoder(xml.Decoder):
    coverage_ids = xml.Parameter("/wcs:CoverageId/text()", num="+")
    namespaces = nsmap
