# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from eoxserver.core.decoders import kvp
from eoxserver.resources.coverages import crss
from eoxserver.services.ows.wms.util import parse_bbox
from eoxserver.services.ows.wms.exceptions import InvalidCRS
from eoxserver.services.ows.wms.basehandlers import (
    WMSBaseGetCapabilitiesHandler, WMSBaseGetMapHandler, WMSBaseGetMapDecoder
)
from eoxserver.services.ows.wms.v13.encoders import WMS13Encoder


class WMS13GetCapabilitiesHandler(WMSBaseGetCapabilitiesHandler):
    versions = ("1.3", "1.3.0")

    def get_encoder(self):
        return WMS13Encoder()


class WMS13GetMapHandler(WMSBaseGetMapHandler):
    service = ("WMS", None)
    versions = ("1.3.0", "1.3")

    def get_decoder(self, request):
        return WMS13GetMapDecoder(request.GET)


class WMS13GetMapDecoder(WMSBaseGetMapDecoder):
    _bbox = kvp.Parameter('bbox', type=parse_bbox, num=1)

    @property
    def bbox(self):
        bbox = self._bbox
        crs = self.crs
        srid = crss.parseEPSGCode(
            self.crs, (crss.fromShortCode, crss.fromURN, crss.fromURL)
        )
        if srid is None:
            raise InvalidCRS(crs, "crs")

        if crss.hasSwappedAxes(srid):
            miny, minx, maxy, maxx = bbox
        else:
            minx, miny, maxx, maxy = bbox

        return (minx, miny, maxx, maxy)

    crs = kvp.Parameter(num=1)

    srs = property(lambda self: self.crs)
