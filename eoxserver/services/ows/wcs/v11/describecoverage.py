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


from itertools import chain

from eoxserver.core import Component, implements, UniqueExtensionPoint
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.interfaces import (
    WCSCoverageDescriptionRendererInterface
)
from eoxserver.services.exceptions import (
    NoSuchCoverageException, OperationNotSupportedException
)
from eoxserver.services.ows.wcs.v11.util import nsmap


class WCS11DescribeCoverageHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    renderer = UniqueExtensionPoint(WCSCoverageDescriptionRendererInterface)

    service = "WCS" 
    versions = ("1.1.0", "1.1.1", "1.1.2",)
    request = "DescribeCoverage"

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS11DescribeCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS11DescribeCoverageXMLDecoder(request.body)

    def get_renderer(self, coverage_type):
        for renderer in self.renderers:
            if issubclass(coverage_type, renderer.handles):
                return renderer

        raise OperationNotSupportedException(
            "No renderer found for coverage type '%s'." % coverage_type.__name__
        )


    def handle(self, request):
        decoder = self.get_decoder(request)
        
        coverage_ids = set(decoder.identifiers)
        coverages = models.Coverage.objects.filter(identifier__in=coverage_ids)

        # check correct number
        if len(coverages) < len(coverage_ids):
            available_ids = set([coverage.identifier for coverage in coverages])
            raise NoSuchCoverageException(coverage_ids - available_ids)

        request_values = [
            ("service", "WCS"),
            ("version", "1.1.2"),
            ("request", "DescribeCoverage"),
            ("identifier", ",".join(decoder.identifiers)),
        ]

        return self.renderer.render(coverages, request_values)


class WCS11DescribeCoverageKVPDecoder(kvp.Decoder):
    identifiers = kvp.Parameter("identifier", type=typelist(separator=","), num=1)


class WCS11DescribeCoverageXMLDecoder(xml.Decoder):
    identifiers = xml.Parameter("wcs:Identifier/text()", type=typelist(separator=","), num=1)
    namespaces = nsmap
