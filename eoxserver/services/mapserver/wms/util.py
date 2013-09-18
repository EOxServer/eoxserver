#-------------------------------------------------------------------------------
# $Id$
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


from itertools import chain

from django.db.models import Q
from django.utils.datastructures import SortedDict

from eoxserver.core import Component, ExtensionPoint
from eoxserver.contrib.mapserver import Layer
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, LayerFactoryInterface, StyleApplicatorInterface
)


class MapServerWMSBaseComponent(Component):
    """ Base class for various WMS render components using MapServer.
    """

    connectors = ExtensionPoint(ConnectorInterface)
    layer_factories = ExtensionPoint(LayerFactoryInterface)
    style_applicators = ExtensionPoint(StyleApplicatorInterface)


    def get_connector(self, data_items):
        for connector in self.connectors:
            if connector.supports(data_items):
                return connector
        return None


    def get_layer_factory(self, suffix):
        result = None
        for factory in self.layer_factories:
            if suffix == factory.suffix:
                if result:
                    pass # TODO
                    #raise Exception("Found")
                result = factory
                return result
        return result


    def setup_map(self, layer_selection, map_, options, cache):
        group_layers = SortedDict()
        coverage_layers = {}

        x= tuple(layer_selection.walk())

        # set up group layers
        for collections, _, name, suffix in x:
            if not collections:
                continue

            factory = self.get_layer_factory(suffix)
            if not factory:
                # raise or pass?
                continue

            group_name = collections[-1].identifier + (suffix or "")
            group_layer = factory.generate_group(group_name)
            group_layers[group_name] = group_layer


        for collections, coverage, name, suffix in layer_selection.walk():
            # get a factory for the given coverage and suffix
            factory = self.get_layer_factory(suffix)

            group_layer = None
            group_name = None

            if collections:
                group_name = collections[-1].identifier + (suffix or "")
                group_layer = group_layers.get(group_name)

            if not coverage:
                layers = (Layer(name),)
            else:
                data_items = coverage.data_items.all()
                coverage.cached_data_items = data_items
                layers = tuple(factory.generate(coverage, group_layer, options))


            for layer in layers:
                coverage_layers.setdefault(coverage, []).append(layer)
                if not coverage or not factory:
                    continue

                if group_name:
                    layer.setMetaData("wms_layer_group", "/" + group_name)

                if factory.requires_connection:
                    connector = self.get_connector(data_items)
                    if not connector:
                        # TODO: raise or pass?
                        raise ""

                    connector.connect(coverage, data_items, layer, cache)
                

        for layer in chain(group_layers.values(), chain(*coverage_layers.values())):
            old_layer = map_.getLayerByName(layer.name)
            if old_layer:
                # remove the old layer and reinsert the new one, to 
                # raise the layer to the top.
                # TODO: find a more efficient way to do this
                map_.removeLayer(old_layer.index)
            map_.insertLayer(layer)


        # apply any styles
        style_applicators = self.style_applicators
        for coverage, layers in coverage_layers.items():
            if not coverage:
                continue

            data_items = (getattr(coverage, "cached_data_items", None)
                          or coverage.data_items.all())
            for layer in layers:
                for applicator in style_applicators:
                    applicator.apply(coverage, data_items, layer, cache)

        return coverage_layers


    def teardown_map(self, map_, coverage_layers, cache):
        for coverage, layers in coverage_layers.items():
            if not coverage:
                continue

            data_items = (getattr(coverage, "cached_data_items", None)
                          or coverage.data_items.all())

            connector = self.get_connector(data_items)
            if not connector:
                continue

            for layer in layers:
                try:
                    connector.disconnect(coverage, data_items, layer, cache)
                except Exception:
                    # TODO log
                    pass


    def get_empty_layers(self, name):
        layer = Layer(name)
        layer.setMetaData("wms_enable_request", "getmap")
        return (layer,)


        """
        for names, suffix, coverage in layer_groups.walk():
            # get a factory for the given coverage and suffix
            factory = self.get_layer_factory(
                coverage.real_type, suffix
            )
            if not factory:
                raise "Could not find a factory for suffix '%s'" % suffix

            suffix = suffix or "" # transform None to empty string

            group_name = None
            group_layer = None

            group_name = "/" + "/".join(
                map(lambda n: n + suffix, names[1:])
            )

            if len(names) > 1:
                # create a group layer
                if group_name not in group_layers:
                    group_layer = factory.generate_group(names[-1] + suffix)
                    if group_layer:
                        group_layers[group_name] = group_layer
            if not group_layer:
                group_layer = group_layers.get(group_name)


            data_items = coverage.data_items.filter(
            #    Q(semantic__startswith="bands") | Q(semantic="tileindex")
            )

            layers = tuple(factory.generate(coverage, group_layer, options))
            for layer in layers:
                if group_name:
                    layer.setMetaData("wms_layer_group", group_name)

                if factory.requires_connection:
                    connector = self.get_connector(data_items)
                    if not connector:
                        raise ""

                    connector.connect(coverage, data_items, layer, cache)
                    connector_to_layers.setdefault(connector, []).append(
                        (coverage, data_items, layer)
                    )
                coverage_layers.append(layer)

            layers_to_style.append((coverage, data_items, layers))


        for layer in chain(group_layers.values(), coverage_layers):
            old_layer = map_.getLayerByName(layer.name)
            if old_layer:
                # remove the old layer and reinsert the new one, to 
                # raise the layer to the top.
                # TODO: find a more efficient way to do this
                map_.removeLayer(old_layer.index)
            map_.insertLayer(layer)

        # apply any styles
        style_applicators = self.style_applicators
        for coverage, data_items, layers in layers_to_style:
            for layer in layers:
                for applicator in style_applicators:
                    applicator.apply(coverage, data_items, layer, cache)

        return connector_to_layers
        """
