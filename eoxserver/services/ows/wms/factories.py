
from eoxserver.core import Component, implements
from eoxserver.contrib.mapserver import Layer
from eoxserver.resources.coverages import models


class AbstractLayerFactory(Component):
    implements(MapServerLayerFactoryInterface)
    abstract = True


class CoverageLayerFactory(AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    suffix = None

    def generate(self, eo_object):
        return Layer(eo_object.identifer)


class CoverageOutlineLayerFactory(AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic, 
               #models.DatasetSeries)
              )
    suffix = "_bands"

    def generate(self, eo_object):
        pass

