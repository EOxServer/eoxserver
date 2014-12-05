#-------------------------------------------------------------------------------
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


from eoxserver.core import Component, implements, UniqueExtensionPoint
from eoxserver.core.decoders import kvp, typelist, InvalidParameterException
from eoxserver.resources.coverages import crss
from eoxserver.services.subset import Subsets, Trim
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface
)
from eoxserver.services.ows.wms.util import (
    lookup_layers, parse_bbox, parse_time, int_or_str
)
from eoxserver.services.ows.wms.interfaces import WMSMapRendererInterface
from eoxserver.services.result import to_http_response
from eoxserver.services.ows.wms.exceptions import InvalidCRS


class WMS11GetMapHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)

    renderer = UniqueExtensionPoint(WMSMapRendererInterface)

    service = "WMS"
    versions = ("1.1", "1.1.0", "1.1.1")
    request = "GetMap"

    def handle(self, request):
        decoder = WMS11GetMapDecoder(request.GET)

        bbox = decoder.bbox
        time = decoder.time
        srs = decoder.srs
        layers = decoder.layers

        if not layers:
            raise InvalidParameterException("No layers specified", "layers")

        srid = crss.parseEPSGCode(
            srs, (crss.fromShortCode, crss.fromURN, crss.fromURL)
        )
        if srid is None:
            raise InvalidCRS(srs, "srs")

        # WMS 1.1 knows no swapped axes
        minx, miny, maxx, maxy = bbox

        subsets = Subsets((
            Trim("x", minx, maxx),
            Trim("y", miny, maxy),
        ), crs=srs)
        if time:
            subsets.append(time)

        renderer = self.renderer
        root_group = lookup_layers(layers, subsets, renderer.suffixes)

        result, _ = renderer.render(
            root_group, request.GET.items(),
            width=int(decoder.width), height=int(decoder.height),
            time=decoder.time, bands=decoder.dim_bands, subsets=subsets,
            elevation=decoder.elevation,
            dimensions=dict(
                (key[4:], values) for key, values in decoder.dimensions
            )
        )
        return to_http_response(result)


class WMS11GetMapDecoder(kvp.Decoder):
    layers = kvp.Parameter(type=typelist(str, ","), num=1)
    styles = kvp.Parameter(num="?")
    bbox   = kvp.Parameter(type=parse_bbox, num=1)
    time   = kvp.Parameter(type=parse_time, num="?")
    srs    = kvp.Parameter(num=1)
    width  = kvp.Parameter(num=1)
    height = kvp.Parameter(num=1)
    format = kvp.Parameter(num=1)
    dim_bands = kvp.Parameter(type=typelist(int_or_str, ","), num="?")
    elevation = kvp.Parameter(type=float, num="?")
    dimensions = kvp.MultiParameter(lambda s: s.startswith("dim_"), locator="dimension", num="*")
