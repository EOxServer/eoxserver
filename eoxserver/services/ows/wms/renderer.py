
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