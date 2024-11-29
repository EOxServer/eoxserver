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

import logging
import tempfile
from typing import List, Tuple, Type
from uuid import uuid4
from contextlib import contextmanager

from eoxserver.contrib import mapserver as ms
from eoxserver.contrib import vsi
from eoxserver.render.browse.defaultstyles import (
    DEFAULT_RASTER_STYLES, DEFAULT_GEOMETRY_STYLES
)
from eoxserver.render.mapserver.factories import (
    BaseMapServerLayerFactory, get_layer_factories
)
from eoxserver.render.map.objects import Map, Layer
from eoxserver.resources.coverages.formats import getFormatRegistry


logger = logging.getLogger(__name__)


# TODO: move this to render.map.exceptions
class MapRenderError(Exception):
    def __init__(self, message, code=None, locator=None):
        super(MapRenderError, self).__init__(message)
        self.code = code
        self.locator = locator


class MapserverMapRenderer(object):

    OUTPUTFORMATS = [
        ('')
    ]

    def get_geometry_styles(self):
        return list(DEFAULT_GEOMETRY_STYLES.values())

    def get_raster_styles(self):
        return list(DEFAULT_RASTER_STYLES.values())

    def get_supported_layer_types(self):
        layer_types = []
        for layer_factory in get_layer_factories():
            layer_types.extend(layer_factory.handled_layer_types)
        return set(layer_types)

    def get_supported_formats(self):
        return getFormatRegistry().getSupportedFormatsWMS()

    def getOutputFormat(self, layer_format):
        frmt = getFormatRegistry().getFormatByMIME(layer_format)
        outputformat_obj = ms.outputFormatObj(frmt.driver)
        outputformat_obj.mimetype = frmt.mimeType

        if frmt.defaultExt:
            if frmt.defaultExt.startswith('.'):
                extension = frmt.defaultExt[1:]
            else:
                extension = frmt.defaultExt

            outputformat_obj.extension = extension
        return outputformat_obj

    def render_map(self, render_map):
        layers = render_map.layers
        format_ = render_map.format
        transparent = render_map.transparent
        with self._prepare_map(
            layers,
            format_,
            render_map.width,
            render_map.height,
            (render_map.bbox),
            render_map.crs,
            transparent
                ) as map_obj:

            if render_map.bgcolor:
                map_obj.imagecolor.setHex("#" + render_map.bgcolor.lower())
            else:
                map_obj.imagecolor.setRGB(0, 0, 0)

            # actually render the map
            image_obj = map_obj.draw()

            try:
                image_bytes = image_obj.getBytes()
            except Exception:
                tmp_name = '/vsimem/%s' % uuid4().hex
                image_obj.save(tmp_name, map_obj)
                with vsi.open(tmp_name) as f:
                    image_bytes = f.read()
                vsi.unlink(tmp_name)
            outputformat_obj = self.getOutputFormat(format_)
            extension = outputformat_obj.extension
            if extension:
                if len(render_map.layers) == 1:
                    filename = '%s.%s' % (
                        render_map.layers[0].name, extension
                    )
                else:
                    filename = 'map.%s' % extension
            else:
                filename = None

        return image_bytes, outputformat_obj.mimetype, filename

    def render_legend(self, legend):
        layers = [legend.layer]
        with self._prepare_map(layers, legend.format) as map_obj:
            outputformat_obj = self.getOutputFormat(legend.format)
            legend_obj = map_obj.legend
            legend_obj.width = legend.width or 1000
            legend_obj.height = legend.height or 1000

            image_obj = map_obj.drawLegend()
            try:
                image_bytes = image_obj.getBytes()
            except Exception:
                tmp_name = '/vsimem/%s' % uuid4().hex
                image_obj.save(tmp_name, map_obj)
                with vsi.open(tmp_name) as f:
                    image_bytes = f.read()
                vsi.unlink(tmp_name)

            extension = outputformat_obj.extension
            if extension:
                if len(layers) == 1:
                    filename = '%s.%s' % (
                        layers[0].name, extension
                    )
                else:
                    filename = 'legend.%s' % extension
            else:
                filename = None
        return image_bytes, outputformat_obj.mimetype, filename

    @contextmanager
    def _prepare_map(
        self,
        layers,
        format_,
        width=1000,
        height=500,
        bbox=(-180, -90, 180, 90),
        crs='EPSG:4326',
        transparent=False
            ):
        # TODO: get layer creators for each layer type in the map
        map_obj = ms.mapObj()
        map_obj.setExtent(*bbox)
        map_obj.setSize(width, height)
        map_obj.setProjection(crs)
        map_obj.setConfigOption('MS_NONSQUARE', 'yes')
        layers_plus_factories = self._get_layers_plus_factories(layers)
        layers_plus_factories_plus_data = [
            (layer, factory, factory.create(map_obj, layer))
            for layer, factory in layers_plus_factories
        ]

        frmt = getFormatRegistry().getFormatByMIME(format_)

        if not frmt:
            raise MapRenderError(
                'No such format %r' % format_,
                code='InvalidFormat',
                locator='format'
            )

        outputformat_obj = ms.outputFormatObj(frmt.driver)

        outputformat_obj.transparent = (
            ms.MS_ON if transparent else ms.MS_OFF
        )
        outputformat_obj.mimetype = frmt.mimeType

        if frmt.defaultExt:
            if frmt.defaultExt.startswith('.'):
                extension = frmt.defaultExt[1:]
            else:
                extension = frmt.defaultExt

            outputformat_obj.extension = extension

        map_obj.setOutputFormat(outputformat_obj)

        # log the resulting map
        if logger.isEnabledFor(logging.DEBUG):
            with tempfile.NamedTemporaryFile() as f:
                map_obj.save(f.name)
                f.seek(0)
                logger.debug(f.read().decode('ascii'))

        try:
            yield map_obj

        finally:
            # disconnect
            for layer, factory, data in layers_plus_factories_plus_data:
                factory.destroy(map_obj, layer, data)

    def _get_layers_plus_factories(
        self,
        render_map: Map,
    ) -> List[Tuple[Layer, BaseMapServerLayerFactory]]:
        layers_plus_factories = []
        type_to_layer_factory = {}

        for layer in render_map:
            layer_type = type(layer)
            if layer_type in type_to_layer_factory:
                factory = type_to_layer_factory[layer_type]
            else:
                factory = self._get_layer_factory(layer_type)
                type_to_layer_factory[layer_type] = factory

            layers_plus_factories.append((layer, factory()))

        return layers_plus_factories

    def _get_layer_factory(self, layer_type: Type[Layer]):
        for factory in get_layer_factories():
            if factory.supports(layer_type):
                return factory
        raise MapRenderError(
            'Could not find a layer factory for %r' % layer_type.__name__
        )
