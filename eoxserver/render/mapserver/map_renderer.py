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

from eoxserver.contrib import mapserver as ms
from eoxserver.render.mapserver.factories import get_layer_factories


logger = logging.getLogger(__name__)


# TODO: move this to render.map.exceptions
class MapRenderError(Exception):
    pass


class MapserverMapRenderer(object):

    OUTPUTFORMATS = [
        ('')
    ]

    def render_map(self, render_map):
        # TODO: get layer creators for each layer type in the map
        map_obj = ms.mapObj()

        if render_map.bgcolor:
            map_obj.imagecolor.setHex("#" + render_map.bgcolor.lower())

        layers_plus_factories = self._get_layers_plus_factories(render_map)

        for layer, factory in layers_plus_factories:
            factory.create(map_obj, layer)

        # TODO: create the format properly
        outputformat_obj = ms.outputFormatObj('GDAL/PNG')

        outputformat_obj.transparent = (
            ms.MS_ON if render_map.transparent else ms.MS_OFF
        )
        outputformat_obj.mimetype = 'image/png'
        map_obj.setOutputFormat(outputformat_obj)

        #

        map_obj.setExtent(*render_map.bbox)
        map_obj.setSize(render_map.width, render_map.height)
        map_obj.setProjection(render_map.crs)

        # log the resulting map
        if logger.isEnabledFor(logging.DEBUG):
            with tempfile.NamedTemporaryFile() as f:
                map_obj.save(f.name)
                f.seek(0)
                logger.debug(f.read())

        # actually render the map
        image_obj = map_obj.draw()

        # disconnect
        for layer, factory in layers_plus_factories:
            factory.destroy(map_obj, layer)

        return image_obj.getBytes(), outputformat_obj.mimetype

    def _get_layers_plus_factories(self, render_map):
        layers_plus_factories = []
        type_to_layer_factory = {}
        for layer in render_map.layers:
            layer_type = type(layer)
            if layer_type in type_to_layer_factory:
                factory = type_to_layer_factory[layer_type]
            else:
                factory = self._get_layer_factory(layer_type)
                type_to_layer_factory[layer_type] = factory

            layers_plus_factories.append((layer, factory()))

        return layers_plus_factories

    def _get_layer_factory(self, layer_type):
        for factory in get_layer_factories():
            if factory.supports(layer_type):
                return factory
        raise MapRenderError(
            'Could not find a layer factory for %r' % layer_type.__name__
        )
