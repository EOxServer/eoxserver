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

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.core.util.iteratortools import pairwise_iterative
from eoxserver.contrib import mapserver as ms
from eoxserver.render.map.objects import (
    CoverageLayer, BrowseLayer, OutlinedBrowseLayer,
    MaskLayer, MaskedBrowseLayer, OutlinesLayer
)
from eoxserver.render.mapserver.config import (
    DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES,
)
from eoxserver.render.colors import BASE_COLORS, COLOR_SCALES, OFFSITE_COLORS
from eoxserver.resources.coverages import crss


class BaseMapServerLayerFactory(object):
    handled_layer_types = []

    @classmethod
    def supports(self, layer_type):
        return layer_type in self.handled_layer_types

    def create(self, map_obj, layer):
        pass

    def destroy(self, map_obj, layer):
        pass


class CoverageLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [CoverageLayer]

    def create(self, map_obj, layer):
        coverage = layer.coverage
        layer_obj = _create_raster_layer_obj(
            map_obj, coverage.extent, coverage.grid.spatial_reference
        )

        fields = coverage.range_type

        if layer.bands:
            assert len(layer.bands) in (1, 3, 4)
            try:
                fields = [
                    next(field for field in fields if field.identifier == band)
                    for band in layer.bands
                ]
            except StopIteration:
                raise Exception('Invalid layers.')
        elif layer.wavelengths:
            assert len(layer.bands) in (1, 3, 4)
            try:
                fields = [
                    next(
                        field
                        for field in fields if field.wavelength == wavelength
                    )
                    for wavelength in layer.wavelengths
                ]
            except StopIteration:
                raise Exception('Invalid wavelengths.')

        locations = [
            coverage.get_location_for_field(field)
            for field in fields
        ]

        # layer_obj.setProcessingKey("SCALE", "AUTO")
        layer_obj.setProcessingKey("CLOSE_CONNECTION", "CLOSE")

        # TODO: apply subsets in time/elevation dims

        if len(set(locations)) > 1:
            # TODO: create VRT
            raise Exception("Too many files")

        else:
            layer_obj.data = locations[0].path

        if len(fields) == 1 and layer.style:
            field = fields[0]

            if layer.range:
                range_ = layer.range
            elif len(field.allowed_values) == 1:
                range_ = field.allowed_values[0]
            else:
                # TODO: from datatype
                range_ = (0, 255)

            _create_raster_style(
                layer.style, layer_obj, range_[0], range_[1], [
                    nil_value[0] for nil_value in field.nil_values
                ]
            )


class BrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [BrowseLayer]

    def create(self, map_obj, layer):
        group_name = layer.name
        for browse in layer.browses:
            # TODO: create raster layer for each browse
            layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent, browse.spatial_reference
            )
            layer_obj.group = group_name
            layer_obj.data = browse.filename


class OutlinedBrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinedBrowseLayer]

    def create(self, map_obj, layer):
        group_name = layer.name
        for browse in layer.browses:
            # create the browse layer itself
            browse_layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent, browse.spatial_reference
            )
            browse_layer_obj.group = group_name
            browse_layer_obj.data = browse.filename

            # create the outlines layer
            outlines_layer_obj = _create_polygon_layer(map_obj)
            shape_obj = ms.shapeObj.fromWKT(browse.footprint.wkt)
            outlines_layer_obj.addFeature(shape_obj)

            class_obj = _create_geometry_class(layer.style or 'red')
            outlines_layer_obj.insertClass(class_obj)


class MaskLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskLayer]

    def create(self, map_obj, layer):
        layer_obj = _create_polygon_layer(map_obj)
        for mask in layer.masks:
            mask_geom = mask.geometry if mask.geometry else mask.load_geometry()
            shape_obj = ms.shapeObj.fromWKT(mask_geom.wkt)
            layer_obj.addFeature(shape_obj)

        layer_obj.insertClass(
            _create_geometry_class(layer.style or 'red', fill=True)
        )


class MaskedBrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskedBrowseLayer]

    def create(self, map_obj, layer):
        group_name = layer.name
        for masked_browse in layer.masked_browses:
            browse = masked_browse.browse
            mask = masked_browse.mask
            mask_name = 'mask__%d' % id(masked_browse)

            # create mapserver layers for the mask
            mask_layer_obj = _create_polygon_layer(map_obj)
            mask_layer_obj.status = ms.MS_OFF
            mask_layer_obj.insertClass(
                _create_geometry_class("black", "white", fill=True)
            )

            mask_geom = mask.geometry if mask.geometry else mask.load_geometry()

            outline = browse.footprint
            outline = outline - mask_geom

            shape_obj = ms.shapeObj.fromWKT(outline.wkt)
            mask_layer_obj.addFeature(shape_obj)

            mask_layer_obj.name = mask_name

            # set up the mapserver layers required for the browses
            browse_layer_obj = _create_raster_layer_obj(
                map_obj, browse.extent,
                browse.spatial_reference
            )
            browse_layer_obj.group = group_name
            browse_layer_obj.data = browse.filename
            browse_layer_obj.mask = mask_name


class OutlinesLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinesLayer]

    def create(self, map_obj, layer):
        layer_obj = _create_polygon_layer(map_obj)
        for footprint in layer.footprints:
            shape_obj = ms.shapeObj.fromWKT(footprint.wkt)
            layer_obj.addFeature(shape_obj)

        class_obj = _create_geometry_class(layer.style or 'red')
        layer_obj.insertClass(class_obj)


# ------------------------------------------------------------------------------
# utils
# ------------------------------------------------------------------------------


def _create_raster_layer_obj(map_obj, extent, sr):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_RASTER
    layer_obj.status = ms.MS_ON

    if extent:
        layer_obj.setMetaData("wms_extent", "%f %f %f %f" % extent)
        layer_obj.setExtent(*extent)

    if sr.srid is not None:
        short_epsg = "EPSG:%d" % sr.srid
        layer_obj.setMetaData("ows_srs", short_epsg)
        layer_obj.setMetaData("wms_srs", short_epsg)

    layer_obj.setProjection(sr.proj)

    return layer_obj


def _create_polygon_layer(map_obj):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_POLYGON
    layer_obj.status = ms.MS_ON

    layer_obj.offsite = ms.colorObj(0, 0, 0)

    srid = 4326
    layer_obj.setProjection(crss.asProj4Str(srid))
    layer_obj.setMetaData("ows_srs", crss.asShortCode(srid))
    layer_obj.setMetaData("wms_srs", crss.asShortCode(srid))

    layer_obj.dump = True

    return layer_obj


def _create_geometry_class(color_name, background_color_name=None, fill=False):
    cls_obj = ms.classObj()
    style_obj = ms.styleObj()

    try:
        color = ms.colorObj(*BASE_COLORS[color_name])
    except KeyError:
        raise  # TODO

    style_obj.outlinecolor = color

    if fill:
        style_obj.color = color

    if background_color_name:
        style_obj.backgroundcolor = ms.colorObj(
            *BASE_COLORS[background_color_name]
        )

    cls_obj.insertStyle(style_obj)
    cls_obj.group = color_name
    return cls_obj


def _create_raster_style(name, layer, minvalue=0, maxvalue=255, nil_values=None):
    colors = COLOR_SCALES[name]

    if nil_values:
        offsite = ms.colorObj(*OFFSITE_COLORS.get(name, (0, 0, 0)))
        layer.offsite = offsite

        for nil_value in nil_values:
            cls = ms.classObj()
            cls.setExpression("([pixel] = %s)" % nil_value)
            cls.group = name

            style = ms.styleObj()
            style.color = offsite
            style.opacity = 0
            style.rangeitem = ""
            cls.insertStyle(style)
            layer.insertClass(cls)

    # Create style for values below range
    cls = ms.classObj()
    cls.setExpression("([pixel] <= %s)" % (minvalue))
    cls.group = name
    style = ms.styleObj()
    style.color = ms.colorObj(*colors[0][1])
    cls.insertStyle(style)
    layer.insertClass(cls)

    interval = (maxvalue - minvalue)
    for prev_item, next_item in pairwise_iterative(colors):
        prev_perc, prev_color = prev_item
        next_perc, next_color = next_item

        cls = ms.classObj()
        cls.setExpression("([pixel] >= %s AND [pixel] < %s)" % (
            (minvalue + prev_perc * interval), (minvalue + next_perc * interval)
        ))
        cls.group = name

        style = ms.styleObj()
        style.mincolor = ms.colorObj(*prev_color)
        style.maxcolor = ms.colorObj(*next_color)
        style.minvalue = minvalue + prev_perc * interval
        style.maxvalue = minvalue + next_perc * interval
        style.rangeitem = ""
        cls.insertStyle(style)
        layer.insertClass(cls)

    # Create style for values above range
    cls = ms.classObj()
    cls.setExpression("([pixel] > %s)" % (maxvalue))
    cls.group = name
    style = ms.styleObj()
    style.color = ms.colorObj(*colors[-1][1])
    cls.insertStyle(style)
    layer.insertClass(cls)
    layer.classgroup = name

# ------------------------------------------------------------------------------
# Layer factories
# ------------------------------------------------------------------------------


LAYER_FACTORIES = None


def _setup_factories():
    global LAYER_FACTORIES

    specifiers = getattr(
        settings, 'EOXS_MAPSERVER_LAYER_FACTORIES',
        DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES
    )
    LAYER_FACTORIES = [
        import_string(specifier)
        for specifier in specifiers
    ]


def get_layer_factories():
    if LAYER_FACTORIES is None:
        _setup_factories()
    return LAYER_FACTORIES
