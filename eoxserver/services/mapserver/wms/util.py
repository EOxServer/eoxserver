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


import logging
from itertools import chain

from django.utils.datastructures import SortedDict

from eoxserver.core import Component, ExtensionPoint
from eoxserver.core.config import get_eoxserver_config
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages.crss import CRSsConfigReader
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, LayerFactoryInterface, StyleApplicatorInterface
)
from eoxserver.services.result import result_set_from_raw_data, get_content_type
from eoxserver.services.exceptions import RenderException
from eoxserver.services.ows.wms.exceptions import InvalidFormat

logger = logging.getLogger(__name__)


class MapServerWMSBaseComponent(Component):
    """ Base class for various WMS render components using MapServer.
    """

    connectors = ExtensionPoint(ConnectorInterface)
    layer_factories = ExtensionPoint(LayerFactoryInterface)
    style_applicators = ExtensionPoint(StyleApplicatorInterface)

    def render(self, layer_groups, request_values, **options):
        map_ = ms.Map()
        map_.setMetaData("ows_enable_request", "*")
        map_.setProjection("EPSG:4326")
        map_.imagecolor.setRGB(0, 0, 0)

        # set supported CRSs
        decoder = CRSsConfigReader(get_eoxserver_config())
        crss_string = " ".join(
            map(lambda crs: "EPSG:%d" % crs, decoder.supported_crss_wms)
        )
        map_.setMetaData("ows_srs", crss_string)
        map_.setMetaData("wms_srs", crss_string)

        self.check_parameters(map_, request_values)

        session = self.setup_map(layer_groups, map_, options)

        with session:
            request = ms.create_request(request_values)
            raw_result = map_.dispatch(request)

            result = result_set_from_raw_data(raw_result)
            return result, get_content_type(result)

    def check_parameters(self, map_, request_values):
        for key, value in request_values:
            if key.lower() == "format":
                if not map_.getOutputFormatByName(value):
                    raise InvalidFormat(value)
                break
        else:
            raise RenderException("Missing 'format' parameter")

    @property
    def suffixes(self):
        return list(
            chain(*[factory.suffixes for factory in self.layer_factories])
        )

    def get_connector(self, data_items):
        for connector in self.connectors:
            if connector.supports(data_items):
                return connector
        return None

    def get_layer_factory(self, suffix):
        result = None
        for factory in self.layer_factories:
            if suffix in factory.suffixes:
                if result:
                    pass  # TODO
                    #raise Exception("Found")
                result = factory
                return result
        return result

    def setup_map(self, layer_selection, map_, options):
        group_layers = SortedDict()
        session = ConnectorSession(options)

        # set up group layers before any "real" layers
        for collections, _, name, suffix in tuple(layer_selection.walk()):
            if not collections:
                continue

            # get a factory for the given suffix
            factory = self.get_layer_factory(suffix)
            if not factory:
                # raise or pass?
                continue

            # get the groups name, which is the name of the collection + the
            # suffix
            group_name = collections[-1].identifier + (suffix or "")

            # generate a group layer
            group_layer = factory.generate_group(group_name)
            group_layers[group_name] = group_layer

        # set up the actual layers for each coverage
        for collections, coverage, name, suffix in layer_selection.walk():
            # get a factory for the given coverage and suffix
            factory = self.get_layer_factory(suffix)

            group_layer = None
            group_name = None

            if collections:
                group_name = collections[-1].identifier + (suffix or "")
                group_layer = group_layers.get(group_name)

            if not coverage:
                # add an empty layer to not produce errors out of bounds.
                if name:
                    tmp_layer = ms.layerObj()
                    tmp_layer.name = (name + suffix) if suffix else name
                    layers_and_data_items = ((tmp_layer, ()),)
                else:
                    layers_and_data_items = ()

            elif not factory:
                tmp_layer = ms.layerObj()
                tmp_layer.name = name
                layers_and_data_items = ((tmp_layer, ()),)
            else:
                data_items = coverage.data_items.all()
                coverage.cached_data_items = data_items
                layers_and_data_items = tuple(factory.generate(
                    coverage, group_layer, suffix, options
                ))

            for layer, data_items in layers_and_data_items:
                connector = self.get_connector(data_items)

                if group_name:
                    layer.setMetaData("wms_layer_group", "/" + group_name)

                session.add(connector, coverage, data_items, layer)

        coverage_layers = [layer for _, layer, _ in session.coverage_layers]
        for layer in chain(group_layers.values(), coverage_layers):
            old_layer = map_.getLayerByName(layer.name)
            if old_layer:
                # remove the old layer and reinsert the new one, to
                # raise the layer to the top.
                # TODO: find a more efficient way to do this
                map_.removeLayer(old_layer.index)
            map_.insertLayer(layer)

        # apply any styles
        # TODO: move this to map/legendgraphic renderer only?
        for coverage, layer, data_items in session.coverage_layers:
            for applicator in self.style_applicators:
                applicator.apply(coverage, data_items, layer)

        return session

    def get_empty_layers(self, name):
        layer = ms.layerObj()
        layer.name = name
        layer.setMetaData("wms_enable_request", "getmap")
        return (layer,)


class ConnectorSession(object):
    """ Helper class to be used in `with` statements. Allows connecting and
        disconnecting all added layers with the given data items.
    """
    def __init__(self, options=None):
        self.item_list = []
        self.options = options or {}

    def add(self, connector, coverage, data_items, layer):
        self.item_list.append(
            (connector, coverage, layer, data_items)
        )

    def __enter__(self):
        for connector, coverage, layer, data_items in self.item_list:
            if connector:
                connector.connect(coverage, data_items, layer, self.options)

    def __exit__(self, *args, **kwargs):
        for connector, coverage, layer, data_items in self.item_list:
            if connector:
                connector.disconnect(coverage, data_items, layer, self.options)

    @property
    def coverage_layers(self):
        return map(lambda it: (it[1], it[2], it[3]), self.item_list)
