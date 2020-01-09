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


from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.basehandlers import WCSGetCoverageHandlerBase
from eoxserver.services.ows.wcs.v11.util import nsmap
from eoxserver.services.ows.wcs.v11.parameters import WCS11CoverageRenderParams


class WCS11GetCoverageHandler(WCSGetCoverageHandlerBase, Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    versions = ("1.1.0", "1.1.1", "1.1.2")
    methods = ['GET', 'POST']

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS11GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS11GetCoverageXMLDecoder(request.body)


    def get_params(self, coverage, decoder, request):
        return WCS11CoverageRenderParams(
            coverage, decoder.boundingbox, decoder.format, decoder.gridcs, 
            decoder.gridbasecrs, decoder.gridtype, decoder.gridorigin, 
            decoder.gridoffsets
        )


def parse_bbox_kvp(string):
    minx, miny, maxx, maxy, crs = string.split(",")
    minx, miny, maxx, maxy = map(float, (minx, miny, maxx, maxy))
    return minx, miny, maxx, maxy, crs


def parse_bbox_xml(node):
    try:
        lower_corner = node.xpath("ows:LowerCorner/text()", namespaces=nsmap)[0]
        upper_corner = node.xpath("ows:UpperCorner/text()", namespaces=nsmap)[0]
        ll = list(map(float, lower_corner.split(" ")))
        ur = list(map(float, upper_corner.split(" ")))
    except (IndexError, ValueError):
        raise ValueError("Invalid bounding box.")
    crs = node.attrib["crs"]
    return ll[0], ll[1], ur[0], ur[1], crs


def parse_origin_kvp(string):
    x, y = map(float, string.split(","))
    return x, y


def parse_origin_xml(string):
    x, y = map(float, string.split(" "))
    return x, y


def parse_offsets_kvp(string):
    x, y = map(float, string.split(","))
    return x, y


def parse_offsets_xml(string):
    x, y = map(float, string.split(" "))
    return x, y


class WCS11GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("identifier", num=1)
    boundingbox = kvp.Parameter(type=parse_bbox_kvp, num=1)
    format = kvp.Parameter(num=1)
    gridcs = kvp.Parameter(num="?")
    gridbasecrs = kvp.Parameter(num="?")
    gridtype = kvp.Parameter(num="?")
    gridorigin = kvp.Parameter(type=parse_origin_kvp, num="?")
    gridoffsets = kvp.Parameter(type=parse_offsets_kvp, num="?")


class WCS11GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("ows:Identifier/text()", type=str, num=1)
    boundingbox = xml.Parameter("wcs:DomainSubset/ows:BoundingBox", type=parse_bbox_xml, num=1)
    format = xml.Parameter("wcs:Output/@format", num=1)
    gridcs = xml.Parameter("wcs:Output/wcs:GridCRS/wcs:GridCS/text()", num="?")
    gridbasecrs = xml.Parameter("wcs:Output/wcs:GridCRS/wcs:GridBaseCRS/text()", num="?")
    gridtype = xml.Parameter("wcs:Output/wcs:GridCRS/wcs:GridType/text()", num="?")
    gridorigin = xml.Parameter("wcs:Output/wcs:GridCRS/wcs:GridOrigin/text()", type=parse_origin_xml, num="?")
    gridoffsets = xml.Parameter("wcs:Output/wcs:GridCRS/wcs:GridOffsets/text()", type=parse_offsets_xml, num="?")

    # TODO
    #interpolation = xml.Parameter("wcs:RangeSubset/wcs:InterpolationType/text()", num="?")
    #fields = xml.Parameter("wcs:RangeSubset/ows:Identifier/text()", num="*")

    namespaces = nsmap
