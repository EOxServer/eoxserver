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


from eoxserver.contrib import mapserver as ms
from eoxserver.render.mapserver.factories import get_layer_factories


# TODO: move this to render.map.exceptions
class MapRenderError(Exception):
    pass


class MapserverMapRenderer(object):
    def render_map(self, render_map):
        # TODO: get layer creators for each layer type in the map
        map_obj = ms.mapObj()

        layers_plus_factories = self._get_layers_plus_factories(render_map)

        for layer, factory in layers_plus_factories:
            pass


        for layer, factory in layers_plus_factories:
            pass

    def _get_layers_plus_factories(self, layers):
        layers_plus_factories = []
        type_to_layer_factory = {}
        for layer in layers:
            layer_type = type(layer)
            if layer_type in type_to_layer_factory:
                factory = type_to_layer_factory[layer_type]
            else:
                factory = self._get_layer_factory(layer_type)
                type_to_layer_factory[layer_type] = factory

            layers_plus_factories.append(layer, factory)

        return layers_plus_factories

    def _get_layer_factory(self, layer_type):
        for factory in get_layer_factories():
            if factory.supports(layer_type):
                return factory
        raise MapRenderError(
            'Could not find a layer factory for %r' % layer_type.__name__
        )
