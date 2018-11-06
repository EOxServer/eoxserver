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
from eoxserver.services.ows.wcs.basehandlers import (
    WCSDescribeCoverageHandlerBase
)
from eoxserver.services.ows.wcs.v10.parameters import (
    WCS10CoverageDescriptionRenderParams
)


class WCS10DescribeCoverageHandler(WCSDescribeCoverageHandlerBase, Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    #implements(PostServiceHandlerInterface)

    versions = ("1.0.0",)
    methods = ['GET']

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS10DescribeCoverageKVPDecoder(request.GET)
        # TODO: implement POST
        elif request.method == "POST":
            #return WCS10GetCoverageXMLDecoder(request.body)
            pass


    def get_params(self, coverages, decoder):
        return WCS10CoverageDescriptionRenderParams(coverages)


class WCS10DescribeCoverageKVPDecoder(kvp.Decoder):
    coverage_ids = kvp.Parameter("coverage", type=typelist(str, ","), num=1)
