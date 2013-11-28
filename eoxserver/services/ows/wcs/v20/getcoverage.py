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


from eoxserver.core import Component, implements
from eoxserver.core.decoders import xml, kvp, typelist
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wcs.basehandlers import WCSGetCoverageHandlerBase
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, parse_subset_kvp, parse_subset_xml, parse_size_kvp, 
    parse_resolution_kvp, Slice, Trim
)
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams


class WCS20GetCoverageHandler(WCSGetCoverageHandlerBase, Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    versions = ("2.0.0", "2.0.1")

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCoverageXMLDecoder(request.body)

    def get_params(self, coverage, decoder):
        return WCS20CoverageRenderParams(
            coverage, decoder.subsets, decoder.sizes, decoder.resolutions,
            decoder.rangesubset, decoder.format, decoder.outputcrs, 
            decoder.mediatype, decoder.interpolation, decoder.mask
        )


class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    sizes       = kvp.Parameter("size", type=parse_size_kvp, num="*")
    resolutions = kvp.Parameter("resolution", type=parse_resolution_kvp, num="*")
    rangesubset = kvp.Parameter("rangesubset", type=typelist(str, ","), num="?")
    format      = kvp.Parameter("format", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")
    mediatype   = kvp.Parameter("mediatype", num="?")
    interpolation = kvp.Parameter("interpolation", num="?")

    mask = None


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*")

    sizes       = xml.Parameter("TODO", type=parse_size_kvp, num="*")
    resolutions = xml.Parameter("TODO", type=parse_size_kvp, num="*")
    interpolation = xml.Parameter("TODO", type=parse_size_kvp, num="?")

    rangesubset = xml.Parameter("rangesubset", type=typelist(str, ","), num="?")

    format      = xml.Parameter("wcs:format/text()", num="?", locator="format")
    # TODO:!!!
    outputcrs   = xml.Parameter("TODO", num="?", locator="outputcrs")
    mediatype   = xml.Parameter("wcs:mediaType/text()", num="?", locator="mediatype")
    
    mask = None

    namespaces = nsmap

