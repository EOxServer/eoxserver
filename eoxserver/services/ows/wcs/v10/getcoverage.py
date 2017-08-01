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
from eoxserver.core.decoders import xml, kvp
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.basehandlers import WCSGetCoverageHandlerBase
from eoxserver.services.ows.wcs.v10.parameters import WCS10CoverageRenderParams


class WCS10GetCoverageHandler(WCSGetCoverageHandlerBase, Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    #implements(PostServiceHandlerInterface)

    versions = ("1.0.0",)
    methods = ['GET']

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS10GetCoverageKVPDecoder(request.GET)
        # TODO: implement POST
        elif request.method == "POST":
            #return WCS10GetCoverageXMLDecoder(request.body)
            pass


    def get_params(self, coverage, decoder, request):
        return WCS10CoverageRenderParams(
            coverage, decoder.bbox, decoder.crs, decoder.format, 
            decoder.response_crs, decoder.width, decoder.height,
            decoder.resx, decoder.resy, decoder.interpolation
        )


def parse_bbox_kvp(string):
    return map(float, string.split(","))


class WCS10GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverage", num=1)
    crs         = kvp.Parameter(num=1)
    response_crs = kvp.Parameter(num="?")
    bbox        = kvp.Parameter(type=parse_bbox_kvp)
    width       = kvp.Parameter(type=int, num="?")
    height      = kvp.Parameter(type=int, num="?")
    resx        = kvp.Parameter(type=float, num="?")
    resy        = kvp.Parameter(type=float, num="?")
    format      = kvp.Parameter(num=1)
    interpolation = kvp.Parameter(num="?")
    exceptions  = kvp.Parameter(num="?")
