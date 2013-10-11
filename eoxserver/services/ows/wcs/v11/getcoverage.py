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

from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.decoders import xml, kvp, typelist, upper, enum
from eoxserver.resources.coverages import models
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.interfaces import WCSCoverageRendererInterface
from eoxserver.services.exceptions import (
    NoSuchCoverageException, OperationNotSupportedException
)
from eoxserver.services.ows.wcs.v11.util import nsmap


class WCS11GetCoverageHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    renderers = ExtensionPoint(WCSCoverageRendererInterface)

    service = "WCS" 
    versions = ("1.1.0", "1.1.1", "1.1.2")
    request = "GetCoverage"

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS11GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS11GetCoverageXMLDecoder(request.body)


    def get_renderer(self, coverage_type):
        for renderer in self.renderers:
            if issubclass(coverage_type, renderer.handles):
                return renderer

        raise OperationNotSupportedException(
            "No renderer found for coverage type '%s'." % coverage_type.__name__
        )


    def handle(self, request):
        decoder = self.get_decoder(request)

        #get parameters
        coverage_id = decoder.identifier
        
        try:
            coverage = models.Coverage.objects.get(identifier=coverage_id)
        except models.Coverage.DoesNotExist:
            raise NoSuchCoverageException((coverage_id,))

        coverage_type = coverage.real_type

        renderer = self.get_renderer(coverage_type)

        # TODO: translate request values from POST 

        return renderer.render(coverage, request.GET.items())


def parse_bounding_box_xml(node):
    try:
        ll = map(float, node.xpath("ows:LowerCorner/text()", nsmap=nsmap)[0].split(" "))
        ur = map(float, node.xpath("ows:UpperCorner/text()", nsmap=nsmap)[0].split(" "))
    except (IndexError, ValueError):
        raise ValueError("Invalid bounding box.")

    crs = node.attr("crs")


class WCS11GetCoverageKVPDecoder(kvp.Decoder):
    identifier = kvp.Parameter(num=1)


class WCS11GetCoverageXMLDecoder(xml.Decoder):
    identifier = xml.Parameter("ows:Identifier/text()", num=1)
    format = xml.Parameter("wcs:Output/@format", num=1)
    grid_crs = xml.Parameter("wcs:Output/wcs:GridCRS/text()", num="?")
    bbox = xml.Parameter("wcs:DomainSubset/ows:BoundingBox") # TODO

    interpolation = xml.Parameter("wcs:RangeSubset/wcs:InterpolationType/text()", num="?")
    fields = xml.Parameter("wcs:RangeSubset/ows:Identifier/text()", num="*")

    namespaces = nsmap
