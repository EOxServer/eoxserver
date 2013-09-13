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

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.timetools import isoformat
from eoxserver.backends.cache import CacheContext
from eoxserver.contrib.mapserver import create_request, Map, Layer
from eoxserver.services.component import MapServerComponent, env
from eoxserver.services.ows.common.config import CapabilitiesConfigReader


class WMSCapabilitiesRenderer(object):
    def render(self, collections, suffixes, request_values):
        ms_component = MapServerComponent(env)
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        map_ = Map()
        map_.setMetaData({
            "enable_request": "*",
            "onlineresource": conf.http_service_url,
            "title": conf.title,
            "abstract": conf.abstract,
            "accessconstraints": conf.access_constraints,
            "addresstype": "",
            "address": conf.delivery_point,
            "stateorprovince": conf.administrative_area,
            "city": conf.city,
            "postcode": conf.postal_code,
            "country": conf.country,
            "contactelectronicmailaddress": conf.electronic_mail_address,
            "contactfacsimiletelephone": conf.phone_facsimile,
            "contactvoicetelephone": conf.phone_voice,
            "contactperson": conf.individual_name,
            "contactorganization": conf.provider_name,
            "contactposition": conf.position_name,
            "fees": conf.fees,
            "keywordlist": ",".join(conf.keywords),
        }, namespace="ows")
        map_.setProjection("EPSG:4326")


        for collection in collections:
            group_name = None
            
            # calculate extent and timextent for every collection
            extent = " ".join(map(str, collection.extent_wgs84))

            eo_objects = collection.eo_objects.filter(
                begin_time__isnull=False, end_time__isnull=False
            )
            timeextent = ",".join(
                map(
                    lambda o: (
                        "/".join(
                            map(isoformat, o.time_extent)
                        ) + "/PT1S"
                    ), eo_objects
                )
            )

            if len(suffixes) > 1:
                # create group layer, if there is more than one suffix for this 
                # collection
                group_name = collection.identifier + "_group"
                group_layer = Layer(group_name)
                group_layer.setMetaData({
                    "title": group_name,
                    "extent": extent
                }, namespace="wms")
                map_.insertLayer(group_layer)

            for suffix in suffixes:
                layer_name = collection.identifier + (suffix or "")
                layer = Layer(layer_name)
                if group_name:
                    layer.setMetaData({
                        "layer_group": "/" + group_name
                    }, namespace="wms")

                layer.setMetaData({
                    "title": layer_name,
                    "extent": extent,
                    "timeextent": timeextent
                }, namespace="wms")
                map_.insertLayer(layer)
        
        request = create_request(request_values)
        response = map_.dispatch(request)
        return response.content, response.content_type



class WMSMapRenderer(object):
    def render(self, layer_groups, request_values, **options):
        ms_component = MapServerComponent(env)

        map_ = Map()
        map_.setMetaData("ows_enable_request", "*")
        map_.setProjection("EPSG:4326")

        group_layers = SortedDict()
        coverage_layers = []
        connector_to_layers = {}
        layers_to_style = []

        with CacheContext() as cache:
            for names, suffix, coverage in layer_groups.walk():
                # get a factory for the given coverage and suffix
                factory = ms_component.get_layer_factory(
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
                        connector = ms_component.get_connector(data_items)
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
            style_applicators = ms_component.style_applicators
            for coverage, data_items, layers in layers_to_style:
                for layer in layers:
                    for applicator in style_applicators:
                        applicator.apply(coverage, data_items, layer, cache)

            request = create_request(request_values)

            try:
                response = map_.dispatch(request)
                return response.content, response.content_type
            finally:
                # cleanup
                for connector, items in connector_to_layers.items():
                    for coverage, data_items, layer in items:
                        connector.disconnect(coverage, data_items, layer, cache)


