
from itertools import chain

from django.db.models import Q

from eoxserver.backends.cache import CacheContext
from eoxserver.contrib.mapserver import create_request, Map
from eoxserver.services.component import MapServerComponent, env

class WMSCapabilitiesRenderer(object):
    def render(self, request, coverages_qs, dataset_series_qs):
        ms_component = MapServerComponent(env)
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        map_ = Map()
        # TODO: add all the capabilities relevant metadata

        factory_cache = {}

        for coverage in coverages_qs:
            coverage_type = coverage.real_type
            if coverage_type not in factory_cache:
                factory_cache[coverage_type] = [
                    factory
                    for factory in ms_component.layer_factories
                    if issubclass(coverage_type, factory.handles)
                ]

            for factory in factory_cache[coverage_type]:
                layer = factory.generate(coverage)

            map_.insertLayer(layer)
            # TODO meta layer via layer groups

        return map_.dispatch(r)


class WMSMapRenderer(object):
    def render(self, layer_groups, request_values, **options):
        ms_component = MapServerComponent(env)

        map_ = Map()
        map_.setMetaData("ows_enable_request", "*")
        map_.setProjection("EPSG:4326")

        group_names = set()
        group_layers = []
        coverage_layers = []
        connector_to_layers = {}

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

                if len(names) > 1:
                    group_name = "/" + "/".join(
                        map(lambda n: n + suffix, names[1:])
                    )
                    # create a group layer
                    if group_name not in group_names:
                        group_names.add(group_name)
                        group_layer = factory.generate_group(names[-1] + suffix)
                        if group_layer:
                            group_layers.append(group_layer)

                data_items = coverage.data_items.filter(
                    Q(semantic__startswith="bands") | Q(semantic="tileindex")
                )

                layers = factory.generate(coverage, options)
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

            for layer in chain(group_layers, coverage_layers):
                old_layer = map_.getLayerByName(layer.name)
                if old_layer:
                    # remove the old layer and reinsert the new one, to 
                    # raise the layer to the top.
                    # TODO: find a more efficient way to do this
                    map_.removeLayer(old_layer.index)
                    continue
                map_.insertLayer(layer)

            request = create_request(request_values)

            try:
                response = map_.dispatch(request)
                return response.content, response.content_type
            finally:
                # cleanup
                for connector, items in connector_to_layers.items():
                    for coverage, data_items, layer in items:
                        connector.disconnect(coverage, data_items, layer, cache)
