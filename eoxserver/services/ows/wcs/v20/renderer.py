
from eoxserver.core import Component, implements
from eoxserver.contrib.mapserver import Request, Map, Layer
from eoxserver.services.interfaces import CoverageRendererInterface
from eoxserver.resources.coverages import models

class CoverageRenderer(Component):
    implements(CoverageRendererInterface)
    abstract = True


class RectifiedCoverageMapServerRenderer(CoverageRenderer):
    handles = (models.RectifiedDataset,)

    def render(self, coverage, **kwargs):
        with CacheContext() as c:
            data = connect(coverage, c)
            self._render(coverage, data, **kwargs)


    def _render(self, coverage, data, **kwargs):
        # configure map
        format = kwargs.get("format", getMSWCSNativeFormat(coverage.format))

        map_ = Map()

        of = getMSOutputFormat(format, coverage)
        map_.appendOutputFormat(of)
        map_.setOutputFormat(of)

        # create and configure layer
        layer = Layer(coverage.identifier)

        # TODO: decide whether or not to use the tileindex

        layer.data = data
        layer.setProjection(coverage.srs.proj)

        # TODO: set layer projection maybe this way??
        """srs = osr.SpatialReference()
        srs.ImportFromEPSG(coverage.srid) # or coverage.projection

        minx, miny, maxx, maxy = eo_object.getExtent()
        size_x, size_y = eo_object.getSize()
        
        false_northing = srs.GetProjParm("false_northing")
        false_easting = srs.GetProjParm("false_easting")
        x_0 = false_easting + minx
        y_0 = false_northing + miny
        to_unit = (maxx - minx) / float(size_x)
        
        if srs.IsProjected():
            
            proj_str = "+init=epsg:%d +x_0=%f +y_0=%f +to_meters=%f" %\
                (srid, x_0, y_0, to_unit)
        else:
            proj_str = "+init=epsg:%d +x_0=%f +y_0=%f +to_degrees=%f" %\
                (srid, x_0, y_0, to_unit)
            
        layer.setProjection(proj_str)"""

        extent = coverage.extent
        size = coverage.size
        rangetype = coverage.rangetype
        resolution = ((extent[2] - extent[0]) / float(size[0]),
                      (extent[1] - extent[3]) / float(size[1]))

        layer.setExtent(*extent)

        layer.setMetaData("ows_title", coverage.identifier)
        layer.setMetaData({
            "label": coverage.identifier,
            "extent": "%.10g %.10g %.10g %.10g" % extent,
            "resolution": "%.10g %.10g" % resolution,
            "size": "%d %d" % size,
            "bandcount": str(len(rangetype.bands)),
            "band_names": " ".join([band.name for band in rangetype.bands]),
            "interval": "%f %f" % rangetype.allowed_values,
            "significant_figures": "%d" % rangetype.significant_figures,
            "rangeset_name": rangetype.name,
            "rangeset_label": rangetype.name,
            "rangeset_axes": ",".join(band.name for band in rangetype.bands),
            "native_format": getMSWCSNativeFormat(coverage.format),
            "nativeformat": getMSWCSNativeFormat(coverage.format),
            "formats": getMSWCSFormatMD(),
            "imagemode": gdalconst_to_imagemode_string(rangetype.data_type)
        }, namespace="wcs")

        for band in rangetype.bands:
            layer.setMetaData({
                "band_description": band.description,
                "band_definition": band.definition,
                "band_uom": band.uom
            }, namespace=band.name)

            # For MS WCS 1.x interface
            layer.setMetaData({
                "label": band.name,
                "interval": "%d %d" % rangetype.allowed_values
            }, namespace="wcs_%s" % band.name)

        map_.insertLayer(layer)

        if "mask" in kwargs:
            # TODO: implement
            pass


        # configure request
        request = Request(kwargs)
        response = map_.dispatch(request)


class ReferenceableDatasetRenderer(CoverageRenderer):
    handles = (models.ReferenceableDataset,)

    def render(self, coverage, **kwargs):
        pass
