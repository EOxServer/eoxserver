import mapscript

from eoxserver.core import Component, implements
from eoxserver.services.interfaces import CoverageRendererInterface

class CoverageRenderer(Component):
    implements(CoverageRendererInterface)
    abstract = True


class RectifiedCoverageMapServerRenderer(CoverageRenderer):
    handles = (models.RectifiedDataset,)

    def render(self, coverage, **kwargs):
        map_obj = 
        ows_request = mapscript.OWSRequest()
        ows_request.type = mapscript.MS_GET_REQUEST

        self.dispatch(map_obj, ows_request)


    def create_map(self, ):
        return mapscript.mapObj()

    def create_request(self, params):
        ows_request = mapscript.OWSRequest()
        ows_request.type = mapscript.MS_GET_REQUEST

        used_keys = {}

        for key, value in params.items():
            key = key.lower()
            
            # addParameter() available in MapServer >= 6.2 
            # https://github.com/mapserver/mapserver/issues/3973
            try:
                ows_request.addParameter(key.lower(), escape(value))
            # Workaround for MapServer 6.0
            except AttributeError:
                used_keys.setdefault(key, 0)
                used_keys[key] += 1
                ows_request.setParameter(
                    "%s_%d" % (key, used_keys[key]), escape(value)
                )


    def dispatch(self, map, request):
        


    def create_request_obj(self, **kwargs):
        pass


class ReferenceableDatasetRenderer(CoverageRenderer):
    handles = (models.ReferenceableDataset,)

    def render(self, coverage, **kwargs):
        pass
