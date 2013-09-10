


from eoxserver.core import Component, implements
from eoxserver.contrib.mapserver import (
    Layer, MS_LAYER_POLYGON, shapeObj, classObj, styleObj, colorObj
)
from eoxserver.resources.coverages import models


class AbstractLayerFactory(Component):
    implements(MapServerLayerFactoryInterface)
    abstract = True

    def generate(self, eo_object):
        layer.setMetaData("wms_extent", "%f %f %f %f" % eo_object.extent_wgs84)
        layer.setMetaData("wms_enable_request", "getcapabilities getmap getfeatureinfo")


    def _set_projection(self, layer, sr):
        short_epsg = "EPSG:%d" % sr.epsg
        layer.setProjection(sr.proj)
        layer.setMetaData("ows_srs", short_epsg) 
        layer.setMetaData("wms_srs", short_epsg) 


class CoverageLayerFactory(AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    suffix = None
    requires_connection = True

    def generate(self, eo_object):
        layer = Layer(eo_object.identifer)
        # TODO: dateline...
        yield layer

    def generate_group(self, name):
        return Layer(name)


class CoverageBandsLayerFactory(AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic, 
               #models.DatasetSeries)
              )
    suffix = "_bands"
    requires_connection = True

    def generate(self, eo_object):
        layer = Layer(eo_object.identifier + self.suffix)
        layer.setProcessing()
        # TODO: get band options
        yield layer
        # TODO: dateline wrapping

    def generate_group(self, name):
        return Layer(name)


class CoverageOutlinesLayerFactory(AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.ReferenceableDataset, models.RectifiedStitchedMosaic,)
    suffix = "_outlines"
    requires_connection = False

    STYLES = (
        ("red", 255, 0, 0),
        ("green", 0, 128, 0),
        ("blue", 0, 0, 255),
        ("white", 255, 255, 255),
        ("black", 0, 0, 0),
        ("yellow", 255, 255, 0),
        ("orange", 255, 165, 0),
        ("magenta", 255, 0, 255),
        ("cyan", 0, 255, 255),
        ("brown", 165, 42, 42)
    )
    
    DEFAULT_STYLE = "red"

    def generate(self, eo_object):
        layer = Layer(eo_object.identifier + self.suffix, type=MS_LAYER_POLYGON)
        
        # create a shape from the objects footprint
        shape = shapeObj.fromWKT(eo_object.footprint.wkt)

        # set the features values and add it to the layer
        shape.initValues(1)
        shape.setValue(0, coverage.identifier)
        layer.addFeature(shape)
        layer.addProcessing("ITEMS=identifier")

        # set projection info
        srid = 4326
        layer.setProjection(crss.asProj4Str(srid))
        layer.setMetaData("ows_srs", crss.asShortCode(srid)) 
        layer.setMetaData("wms_srs", crss.asShortCode(srid)) 

        layer.dump = True

        layer.header = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_header.html")
        layer.template = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_dataset.html")
        layer.footer = os.path.join(settings.PROJECT_DIR, "conf", "outline_template_footer.html")
        
        layer.setMetaData("gml_include_items", "all")
        layer.setMetaData("wms_include_items", "all")

        layer.offsite = colorObj(0, 0, 0)

        # add style info
        for name, r, g, b in self.STYLES:
            outline_class = classObj()
            outline_style = styleObj()
            outline_style.outlinecolor = colorObj(r, g, b)
            outline_class.insertStyle(outline_style)
            outline_class.group = name
        
            layer.insertClass(outline_class)

        layer.classgroup = self.DEFAULT_STYLE

        # TODO: what about dateline...
        yield layer


    def generate_group(self, name):
        return Layer(name, type=MS_LAYER_POLYGON)

