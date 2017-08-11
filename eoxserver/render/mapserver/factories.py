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

from eoxserver.render.map.objects import (
    CoverageLayer, BrowseLayer, MaskLayer, MaskedBrowseLayer, OutlinesLayer
)
from eoxserver.render.mapserver.config import (
    DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES,
)


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
        pass


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
            layer_obj.data = browse.browse_filename


class MaskLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskLayer]

    def create(self, map_obj, layer):
        pass


class MaskedBrowseLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [MaskedBrowseLayer]

    def create(self, map_obj, layer):
        pass


class OutlinesLayerFactory(BaseMapServerLayerFactory):
    handled_layer_types = [OutlinesLayer]

    def create(self, map_obj, layer):
        _create_polygon_layer(map_obj, )  # TODO

        


# ------------------------------------------------------------------------------
# utils
# ------------------------------------------------------------------------------


def _create_raster_layer_obj(map_obj, extent, sr):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_RASTER

    if extent:
        layer_obj.setMetaData("wms_extent", "%f %f %f %f" % extent)
        layer_obj.setExtent(*extent)

    if sr.srid is not None:
        short_epsg = "EPSG:%d" % sr.srid
        layer_obj.setMetaData("ows_srs", short_epsg)
        layer_obj.setMetaData("wms_srs", short_epsg)

    layer_obj.setProjection(sr.proj)

    return layer_obj


def _create_polygon_layer(map_obj, geometry):
    layer_obj = ms.layerObj(map_obj)
    layer_obj.type = ms.MS_LAYER_POLYGON

    # TODO

    return layer_obj

POLYGON_COLORS = {
    "red": ms.colorObj(255, 0, 0),
    "green": ms.colorObj(0, 128, 0),
    "blue": ms.colorObj(0, 0, 255),
    "white": ms.colorObj(255, 255, 255),
    "black": ms.colorObj(0, 0, 0),
    "yellow": ms.colorObj(255, 255, 0),
    "orange": ms.colorObj(255, 165, 0),
    "magenta": ms.colorObj(255, 0, 255),
    "cyan": ms.colorObj(0, 255, 255),
    "brown": ms.colorObj(165, 42, 42)
}


def _create_geometry_class(color_name, fill=False):
    cls = ms.classObj()
    style = ms.styleObj()

    try:
        color = POLYGON_COLORS[color_name]
    except KeyError:
        raise  # TODO

    style.outlinecolor = color
    if fill:
        style.color = color
    cls.insertStyle(style)
    cls.group = color_name
    return cls


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
