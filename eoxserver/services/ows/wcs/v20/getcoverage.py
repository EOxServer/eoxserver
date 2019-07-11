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

from itertools import chain

from eoxserver.core.decoders import xml, kvp, typelist
from eoxserver.services.subset import Subsets
from eoxserver.services.ows.wcs.basehandlers import WCSGetCoverageHandlerBase
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, parse_subset_kvp, parse_subset_xml, parse_range_subset_kvp,
    parse_range_subset_xml, parse_interpolation,
    parse_scaleaxis_kvp, parse_scalesize_kvp, parse_scaleextent_kvp,
    parse_scaleaxis_xml, parse_scalesize_xml, parse_scaleextent_xml,
)
from eoxserver.services.ows.wcs.v20.parameters import WCS20CoverageRenderParams
from eoxserver.services.ows.wcs.v20.encodings import get_encoding_extensions
from eoxserver.services.exceptions import InvalidRequestException


class WCS20GetCoverageHandler(WCSGetCoverageHandlerBase):
    versions = ("2.0.0", "2.0.1")
    methods = ['GET', 'POST']

    def get_decoder(self, request):
        if request.method == "GET":
            return WCS20GetCoverageKVPDecoder(request.GET)
        elif request.method == "POST":
            return WCS20GetCoverageXMLDecoder(request.body)

    def get_subsets(self, decoder):
        return Subsets(decoder.subsets, crs=decoder.subsettingcrs)

    def get_params(self, coverage, decoder, request):
        subsets = Subsets(decoder.subsets, crs=decoder.subsettingcrs)
        encoding_params = None
        for encoding_extension in get_encoding_extensions():
            if encoding_extension.supports(decoder.format, {}):
                encoding_params = encoding_extension.get_encoding_params(
                    request
                )

        scalefactor = decoder.scalefactor
        scales = list(
            chain(decoder.scaleaxes, decoder.scalesize, decoder.scaleextent)
        )

        # check scales validity: ScaleFactor and any other scale
        if scalefactor and scales:
            raise InvalidRequestException(
                "ScaleFactor and any other scale operation are mutually "
                "exclusive.", locator="scalefactor"
            )

        # check scales validity: Axis uniqueness
        axes = set()
        for scale in scales:
            if scale.axis in axes:
                raise InvalidRequestException(
                    "Axis '%s' is scaled multiple times." % scale.axis,
                    locator=scale.axis
                )
            axes.add(scale.axis)

        return WCS20CoverageRenderParams(
            coverage, subsets, decoder.rangesubset, decoder.format,
            decoder.outputcrs, decoder.mediatype, decoder.interpolation,
            scalefactor, scales, encoding_params or {}, request
        )


class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    scalefactor = kvp.Parameter("scalefactor", type=float, num="?")
    scaleaxes   = kvp.Parameter("scaleaxes", type=typelist(parse_scaleaxis_kvp, ","), default=(), num="?")
    scalesize   = kvp.Parameter("scalesize", type=typelist(parse_scalesize_kvp, ","), default=(), num="?")
    scaleextent = kvp.Parameter("scaleextent", type=typelist(parse_scaleextent_kvp, ","), default=(), num="?")
    rangesubset = kvp.Parameter("rangesubset", type=parse_range_subset_kvp, num="?")
    format      = kvp.Parameter("format", num="?")
    subsettingcrs = kvp.Parameter("subsettingcrs", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")
    mediatype   = kvp.Parameter("mediatype", num="?")
    interpolation = kvp.Parameter("interpolation", type=parse_interpolation, num="?")


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*", locator="subset")
    scalefactor = xml.Parameter("wcs:Extension/scal:ScaleByFactor/scal:scaleFactor/text()", type=float, num="?", locator="scalefactor")
    scaleaxes   = xml.Parameter("wcs:Extension/scal:ScaleByAxesFactor/scal:ScaleAxis", type=parse_scaleaxis_xml, num="*", default=(), locator="scaleaxes")
    scalesize   = xml.Parameter("wcs:Extension/scal:ScaleToSize/scal:TargetAxisSize", type=parse_scalesize_xml, num="*", default=(), locator="scalesize")
    scaleextent = xml.Parameter("wcs:Extension/scal:ScaleToExtent/scal:TargetAxisExtent", type=parse_scaleextent_xml, num="*", default=(), locator="scaleextent")
    rangesubset = xml.Parameter("wcs:Extension/rsub:RangeSubset", type=parse_range_subset_xml, num="?", locator="rangesubset")
    format      = xml.Parameter("wcs:format/text()", num="?", locator="format")
    subsettingcrs = xml.Parameter("wcs:Extension/crs:subsettingCrs/text()", num="?", locator="subsettingcrs")
    outputcrs   = xml.Parameter("wcs:Extension/crs:outputCrs/text()", num="?", locator="outputcrs")
    mediatype   = xml.Parameter("wcs:mediaType/text()", num="?", locator="mediatype")
    interpolation = xml.Parameter("wcs:Extension/int:Interpolation/int:globalInterpolation/text()", type=parse_interpolation, num="?", locator="interpolation")

    namespaces = nsmap
