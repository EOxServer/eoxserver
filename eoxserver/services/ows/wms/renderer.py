
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
    def render(self, request, layer_groups):
        ms_component = MapServerComponent(env)

        map_ = Map()

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
                    Q(semantic__startswith="bands") || Q(semantic="tileindex")
                )

                layers = factory.generate(coverage)
                for layer in layers:
                    layer.setMetaData({
                        "layer_group": group_name
                    }, namespace="wms")

                    if factory.requires_connection:
                        connector = ms_component.get_connector(data_items)
                        if not connector:
                            raise ""

                        connector.connect(coverage, data_items, layer, cache)
                        connector_to_layers.setdefault(connector, []).append(
                            (coverage, data_items, layer)
                        )

            for layer in chain(group_layers, coverage_layers):
                map_.insertLayer(layer)

            try:
                map_.dispatch(request)
            except:
                # cleanup
                for connector, (coverage, data_items, layer) in connector_to_layers.items():
                    connector.disconnect(coverage, data_items, layer, cache)
                raise

