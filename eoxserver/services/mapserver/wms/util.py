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


import logging
from itertools import chain, count 

from django.db.models import Q
from django.utils.datastructures import SortedDict

from eoxserver.core import Component, ExtensionPoint
from eoxserver.contrib import mapserver as ms
from eoxserver.services.mapserver.interfaces import (
    ConnectorInterface, StyleApplicatorInterface, LayerPluginInterface,
)
from eoxserver.services.result import result_set_from_raw_data, get_content_type


logger = logging.getLogger(__name__)


class MapServerWMSBaseComponent(Component):
    """ Base class for various WMS render components using MapServer.
    """

    connectors = ExtensionPoint(ConnectorInterface)
    layer_plugins = ExtensionPoint(LayerPluginInterface) 
    style_applicators = ExtensionPoint(StyleApplicatorInterface)


    def render(self, layer_groups, request_values, **options):
        map_ = ms.Map()
        map_.setMetaData("ows_enable_request", "*")
        map_.setProjection("EPSG:4326")
        map_.imagecolor.setRGB(0, 0, 0)

        session = self.setup_map(layer_groups, map_, options)
        
        with session:
            request = ms.create_request(request_values)
            raw_result = map_.dispatch(request)

            result = result_set_from_raw_data(raw_result)
            return result, get_content_type(result)


    @property
    def suffixes(self):
        return list( chain( *((f.suffixes for f in self.layer_plugins)) ) )


    def get_connector(self, data_items):
        for connector in self.connectors:
            if connector.supports(data_items):
                return connector
        return None


    def setup_map(self, layer_selections, map_, options):

        #---------------------------------------------------------
        # debug print - list existing mapserver layers 
        logger.debug("MAP: %s", map_)
        logger.debug("Initial Layers: ")
        for i in count() :
            l = map_.getLayer(i)
            if not l : break
            logger.debug("\t %s -> %s ", l.name, l.group )
        logger.debug("Initial Layers: end of list")
        #---------------------------------------------------------

        def _get_new_layer_factory(ls,opt):
            for layer_plugin in self.layer_plugins:
                if ls.suffix in layer_plugin.suffixes:
                    return layer_plugin.get_layer_factory(ls,opt)
            raise KeyError

        #---------------------------------------------------------

        # returned session object
        session = ConnectorSession()

        # iterate over the layer selections 
        for layer_selection in layer_selections : 
        
            # initialize the layer_factory 
            factory = _get_new_layer_factory(layer_selection,options)

            # generate the map layers 
            for layer, coverage, data_items in factory.generate() :

                # if necessary create data connector
                if coverage and data_items :
                    connector = self.get_connector(data_items)
                    session.add(connector, coverage, data_items, layer)

                # NOTE: The map_ object shall be cleaned befor inserting
                #       new layers!
                #old_layer = map_.getLayerByName(layer.name)
                #if old_layer:
                    # remove the old layer and reinsert the new one, to
                    # raise the layer to the top.
                    # TODO: find a more efficient way to do this
                    #map_.removeLayer(old_layer.index)

                map_.insertLayer(layer)

        #---------------------------------------------------------
        # debug print - list existing mapserver layers 
        logger.debug("MAP: %s", map_)
        logger.debug("Current Layers: ")
        for i in count() :
            l = map_.getLayer(i)
            if not l : break
            logger.debug("\t %s -> %s ", l.name, l.group )
        logger.debug("Current Layers: end of list")
        #---------------------------------------------------------

        # TODO: apply styles
        # TODO: move this to map/legendgraphic renderer only?
        #for coverage, layer, data_items in session.coverage_layers:
        #    for applicator in self.style_applicators:
        #        applicator.apply(coverage, data_items, layer)

        return session


class ConnectorSession(object):
    """ Helper class to be used in `with` statements. Allows connecting and 
        disconnecting all added layers with the given data items.
    """
    def __init__(self):
        self.item_list = []

    def add(self, connector, coverage, data_items, layer):
        self.item_list.append(
            (connector, coverage, layer, data_items)
        )

    def __enter__(self):
        for connector, coverage, layer, data_items in self.item_list:
            if connector:
                connector.connect(coverage, data_items, layer)

    def __exit__(self, *args, **kwargs):
        for connector, coverage, layer, data_items in self.item_list:
            if connector:
                connector.disconnect(coverage, data_items, layer)


    @property
    def coverage_layers(self):
        return map(lambda it: (it[1], it[2], it[3]), self.item_list)
