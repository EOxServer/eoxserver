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


class WMS13GetMapHandler(object):
    methods = ['GET']

    service = ("WMS", None)
    versions = ("1.3.0", "1.3")
    request = "GetMap"

    def handle(self, request):
        decoder = WMS13GetMapDecoder(request.GET)

        bbox = decoder.bbox
        time = decoder.time
        crs = decoder.crs
        layers = decoder.layers

        if not layers:
            raise InvalidParameterException("No layers specified", "layers")

        srid = crss.parseEPSGCode(
            crs, (crss.fromShortCode, crss.fromURN, crss.fromURL)
        )
        if srid is None:
            raise InvalidCRS(crs, "crs")

        if crss.hasSwappedAxes(srid):
            miny, minx, maxy, maxx = bbox
        else:
            minx, miny, maxx, maxy = bbox

        subsets = Subsets((
            Trim("x", minx, maxx),
            Trim("y", miny, maxy),
        ), crs=crs)
        if time:
            subsets.append(time)

        # TODO: adjust way to get to renderer

        styles = decoder.styles

        if styles:
            styles = styles.split(',')

        from eoxserver.services.ows.wms.layerquery import LayerQuery

        render_map = LayerQuery().create_map(
            layers=layers, styles=styles, bbox=bbox, crs=crs,
            width=decoder.width, height=decoder.height,
            format=decoder.format, transparent=decoder.transparent,
            bgcolor=decoder.bgcolor,
            time=time,

            range=decoder.dim_range,

            bands=None,
            wavelengths=None,
            elevation=None,
            cql=decoder.cql,
        )


        from eoxserver.render.mapserver.map_renderer import MapserverMapRenderer

        return MapserverMapRenderer().render_map(render_map)

        # root_group = lookup_layers(layers, subsets, renderer.suffixes)

        # result, _ = renderer.render(
        #     root_group, request.GET.items(),
        #     width=int(decoder.width), height=int(decoder.height),
        #     time=decoder.time, bands=decoder.dim_bands, subsets=subsets,
        #     elevation=decoder.elevation,
        #     dimensions=dict(
        #         (key[4:], values) for key, values in decoder.dimensions
        #     )
        # )

        # return to_http_response(result)


def parse_transparent(value):
    value = value.upper()
    if value == 'TRUE':
        return True
    elif value == 'FALSE':
        return False
    raise ValueError("Invalid value for 'transparent' parameter.")


def parse_range(value):
    return map(float, value.split(','))


class WMS13GetMapDecoder(kvp.Decoder):
    layers = kvp.Parameter(type=typelist(str, ","), num=1)
    styles = kvp.Parameter(num="?")
    bbox   = kvp.Parameter(type=parse_bbox, num=1)
    time   = kvp.Parameter(type=parse_time, num="?")
    crs    = kvp.Parameter(num=1)
    width  = kvp.Parameter(num=1)
    height = kvp.Parameter(num=1)
    format = kvp.Parameter(num=1)
    bgcolor = kvp.Parameter(num='?')
    transparent = kvp.Parameter(num='?', default=False, type=parse_transparent)
    dim_bands = kvp.Parameter(type=typelist(int_or_str, ","), num="?")
    dim_range = kvp.Parameter(type=parse_range, num="?")
    elevation = kvp.Parameter(type=float, num="?")
    dimensions = kvp.MultiParameter(lambda s: s.startswith("dim_"), locator="dimension", num="*")

    cql = kvp.Parameter(num="?")
