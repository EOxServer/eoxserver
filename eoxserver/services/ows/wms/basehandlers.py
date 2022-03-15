# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

"""\
This module contains a set of handler base classes which shall help to
implement a specific handler. Interface methods need to be overridden in order
to work, default methods can be overidden.
"""

from itertools import chain
import math
import re

from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse

from eoxserver.core.decoders import kvp, typelist, InvalidParameterException
from eoxserver.core.config import get_eoxserver_config
from eoxserver.render.map.renderer import (
    get_map_renderer,  # get_feature_info_renderer
)
from eoxserver.render.map.objects import Map
from eoxserver.resources.coverages import crss
from eoxserver.resources.coverages import models
from eoxserver.services.ows.wms.util import (
    parse_bbox, parse_time, int_or_str
)
from eoxserver.services.ows.wms.parsing import parse_render_variables
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wms.exceptions import InvalidCRS
from eoxserver.services.ecql import (
    parse, to_filter, get_field_mapping_for_model
)
from eoxserver.services import filters
from eoxserver.services.ows.wms.layermapper import LayerMapper
from eoxserver.services import views


class WMSBaseGetCapabilitiesHandler(object):
    """ Base for WMS capabilities handlers.
    """

    service = "WMS"
    request = "GetCapabilities"

    methods = ["GET"]

    def get_decoder(self, request):
        return WMSBaseGetCapbilitiesDecoder(request.GET)

    def handle(self, request):
        decoder = self.get_decoder(request)
        qs = models.EOObject.objects.all()

        cql_text = decoder.cql
        if cql_text:
            mapping, mapping_choices = filters.get_field_mapping_for_model(
                qs.model
            )
            ast = parse(cql_text)
            filter_expressions = to_filter(ast, mapping, mapping_choices)
            qs = qs.filter(filter_expressions)

            eo_objects = qs.select_subclasses()

        else:
            # lookup Collections, Products and Coverages
            eo_objects = chain(
                models.Collection.objects.exclude(
                    service_visibility__service='wms',
                    service_visibility__visibility=False
                ),
                models.Product.objects.filter(
                    service_visibility__service='wms',
                    service_visibility__visibility=True
                ),
                models.Coverage.objects.filter(
                    service_visibility__service='wms',
                    service_visibility__visibility=True
                )
            )

        map_renderer = get_map_renderer()
        raster_styles = map_renderer.get_raster_styles()
        geometry_styles = map_renderer.get_geometry_styles()

        layer_mapper = LayerMapper(map_renderer.get_supported_layer_types())
        layer_descriptions = [
            layer_mapper.get_layer_description(
                eo_object, raster_styles, geometry_styles
            )
            for eo_object in eo_objects
        ]

        encoder = self.get_encoder()
        conf = CapabilitiesConfigReader(get_eoxserver_config())
        return encoder.serialize(
            encoder.encode_capabilities(
                conf, request.build_absolute_uri(reverse(views.ows)),
                crss.getSupportedCRS_WMS(format_function=crss.asShortCode),
                map_renderer.get_supported_formats(), [],
                layer_descriptions
            ),
            pretty_print=settings.DEBUG
        ), encoder.content_type


class WMSBaseGetMapHandler(object):
    methods = ['GET']
    service = "WMS"
    request = "GetMap"

    def handle(self, request):
        decoder = self.get_decoder(request)

        minx, miny, maxx, maxy = decoder.bbox
        time = decoder.time
        crs = decoder.srs
        layer_names = decoder.layers

        width = decoder.width
        height = decoder.height

        # calculate the zoomlevel
        zoom = calculate_zoom((minx, miny, maxx, maxy), width, height, crs)

        if not layer_names:
            raise InvalidParameterException("No layers specified", "layers")

        srid = crss.parseEPSGCode(
            crs, (crss.fromShortCode, crss.fromURN, crss.fromURL)
        )
        if srid is None:
            raise InvalidCRS(crs, "crs")

        field_mapping, mapping_choices = get_field_mapping_for_model(
            models.Product
        )

        filter_expressions = filters.bbox(
            filters.attribute('footprint', field_mapping),
            minx, miny, maxx, maxy, crs, bboverlaps=False
        )

        if time:
            filter_expressions &= filters.time_interval(time)

        cql = getattr(decoder, 'cql', None)
        if cql:
            cql_filters = to_filter(
                parse(cql), field_mapping, mapping_choices
            )
            filter_expressions &= cql_filters

        # TODO: multiple sorts per layer?
        sort_by = getattr(decoder, 'sort_by', None)
        if sort_by:
            sort_by = (field_mapping.get(sort_by[0], sort_by[0]), sort_by[1])

        styles = decoder.styles

        if styles:
            styles = styles.split(',')
        else:
            styles = [None] * len(layer_names)

        dimensions = {
            "time": time,
            "elevation": decoder.elevation,
            "ranges": decoder.dim_range,
            "bands": decoder.dim_bands,
            "wavelengths": decoder.dim_wavelengths,
        }

        map_renderer = get_map_renderer()

        layer_mapper = LayerMapper(map_renderer.get_supported_layer_types())

        layers = []
        for layer_name, style in zip(layer_names, styles):
            name, suffix = layer_mapper.split_layer_suffix_name(layer_name)
            layer = layer_mapper.lookup_layer(
                name, suffix, style,
                filter_expressions, sort_by, zoom=zoom,
                variables=decoder.variables,
                **dimensions
            )
            layers.append(layer)

        map_ = Map(
            width=decoder.width, height=decoder.height, format=decoder.format,
            bbox=(minx, miny, maxx, maxy), crs=crs,
            bgcolor=decoder.bgcolor, transparent=decoder.transparent,
            layers=layers,
        )

        result_bytes, content_type, filename = map_renderer.render_map(map_)

        response = HttpResponse(result_bytes, content_type=content_type)
        if filename:
            response['Content-Disposition'] = \
                'inline; filename="%s"' % filename

        return response


class WMSBaseGetFeatureInfoHandler(object):
    methods = ['GET']
    service = "WMS"
    request = "GetFeatureInfo"

    def handle(self, request):
        decoder = self.get_decoder(request)

        minx, miny, maxx, maxy = decoder.bbox
        x = decoder.x
        y = decoder.y
        time = decoder.time
        crs = decoder.srs
        layer_names = decoder.layers

        width = decoder.width
        height = decoder.height

        # calculate the zoomlevel
        zoom = calculate_zoom((minx, miny, maxx, maxy), width, height, crs)

        if not layer_names:
            raise InvalidParameterException("No layers specified", "layers")

        srid = crss.parseEPSGCode(
            crs, (crss.fromShortCode, crss.fromURN, crss.fromURL)
        )
        if srid is None:
            raise InvalidCRS(crs, "crs")

        field_mapping, mapping_choices = get_field_mapping_for_model(
            models.Product
        )

        # calculate resolution
        # TODO: dateline
        resx = (maxx - minx) / width
        resy = (maxy - miny) / height

        p_minx = x * resx
        p_miny = y * resy
        p_maxx = (x + 1) * resx
        p_maxy = (y + 1) * resy

        filter_expressions = filters.bbox(
            filters.attribute('footprint', field_mapping),
            p_minx, p_miny, p_maxx, p_maxy, crs, bboverlaps=False
        )

        if time:
            filter_expressions &= filters.time_interval(time)

        cql = getattr(decoder, 'cql', None)
        if cql:
            cql_filters = to_filter(
                parse(cql), field_mapping, mapping_choices
            )
            filter_expressions &= cql_filters

        # TODO: multiple sorts per layer?
        sort_by = getattr(decoder, 'sort_by', None)
        if sort_by:
            sort_by = (field_mapping.get(sort_by[0], sort_by[0]), sort_by[1])

        styles = decoder.styles

        if styles:
            styles = styles.split(',')
        else:
            styles = [None] * len(layer_names)

        dimensions = {
            "time": time,
            "elevation": decoder.elevation,
            "ranges": decoder.dim_range,
            "bands": decoder.dim_bands,
            "wavelengths": decoder.dim_wavelengths,
        }

        feature_info_renderer = get_feature_info_renderer()

        layer_mapper = LayerMapper(feature_info_renderer.get_supported_layer_types())

        layers = []
        for layer_name, style in zip(layer_names, styles):
            name, suffix = layer_mapper.split_layer_suffix_name(layer_name)
            layer = layer_mapper.lookup_layer(
                name, suffix, style,
                filter_expressions, sort_by, zoom=zoom, **dimensions
            )
            layers.append(layer)

        map_ = Map(
            width=decoder.width, height=decoder.height, format=decoder.format,
            bbox=(minx, miny, maxx, maxy), crs=crs,
            bgcolor=decoder.bgcolor, transparent=decoder.transparent,
            layers=layers
        )

        result_bytes, content_type, filename = \
            feature_info_renderer.render_feature_info(map_)

        response = HttpResponse(result_bytes, content_type=content_type)
        if filename:
            response['Content-Disposition'] = \
                'inline; filename="%s"' % filename

        return response


class WMSBaseGetCapbilitiesDecoder(kvp.Decoder):
    cql = kvp.Parameter(num="?")


def parse_transparent(value):
    value = value.upper()
    if value == 'TRUE':
        return True
    elif value == 'FALSE':
        return False
    raise ValueError("Invalid value for 'transparent' parameter.")


def parse_ranges(value):
    ranges_separator = getattr(settings, 'EOXS_WMS_DIM_RANGES_SEPARATOR', r',')
    range_separator = getattr(settings, 'EOXS_WMS_DIM_RANGE_SEPARATOR', r'\s+')
    return [
        [
            float(v)
            for v in re.split(range_separator, rng.strip())
        ]
        for rng in re.split(ranges_separator, value)
    ]


def parse_sort_by(value):
    items = value.strip().split()
    assert items[1] in ['A', 'D']
    return (items[0], 'ASC' if items[1] == 'A' else 'DESC')


class WMSBaseGetMapDecoder(kvp.Decoder):
    layers = kvp.Parameter(type=typelist(str, ","), num=1)
    styles = kvp.Parameter(num="?")
    width = kvp.Parameter(num=1)
    height = kvp.Parameter(num=1)
    format = kvp.Parameter(num=1)
    bgcolor = kvp.Parameter(num='?')
    transparent = kvp.Parameter(num='?', default=False, type=parse_transparent)

    bbox = kvp.Parameter('bbox', type=parse_bbox, num=1)
    srs = kvp.Parameter(num=1)

    time = kvp.Parameter(type=parse_time, num="?")
    elevation = kvp.Parameter(type=float, num="?")
    dim_bands = kvp.Parameter(type=typelist(int_or_str, ","), num="?")
    dim_wavelengths = kvp.Parameter(type=typelist(float, ","), num="?")
    dim_range = kvp.Parameter(type=parse_ranges, num="?")

    cql = kvp.Parameter(num="?")
    variables = kvp.Parameter(type=parse_render_variables, num="?")

    sort_by = kvp.Parameter('sortBy', type=parse_sort_by, num="?")


def calculate_zoom(bbox, width, height, crs):
    # TODO: make this work for other CRSs
    lon_diff = bbox[2] - bbox[0]
    lat_diff = bbox[3] - bbox[1]

    max_diff = max(lon_diff, lat_diff)
    if max_diff < (360 / pow(2, 20)):
        return 21
    else:
        zoom = int(-1 * (math.log(max_diff, 2) - (math.log(360, 2))))
        if zoom < 1:
            zoom = 1
        return zoom
