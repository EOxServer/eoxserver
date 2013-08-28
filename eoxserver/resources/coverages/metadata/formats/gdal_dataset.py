from django.contrib.gis.geos import Polygon

from eoxserver.core import Component, implements
from eoxserver.contrib import gdal
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface
)


def open_gdal(obj):
    if isinstance(obj, gdal.Dataset):
        return obj
    try:
        return gdal.Open(obj)
    except RuntimeError:
        return None


class GDALDatasetMetadataReader(Component):
    implements(MetadataReaderInterface)

    def test(self, obj):
        return open_gdal(obj) is not None

    def read(self, obj):
        ds = open_gdal(obj)
        if ds is not None:
            size = (ds.RasterXSize, ds.RasterYSize)
            gt = ds.GetGeoTransform()
            extent = None

            # TODO: check if geotransfrom is valid
            extent = (
                gt[0],
                gt[3] + size[1] * gt[5],
                gt[0] + size[0] * gt[1],
                gt[3]
            )
            projection = ds.GetProjection()

            values = {
                "size": (ds.RasterXSize, ds.RasterYSize),
            }

            if projection:
                # TODO: try to get an EPSG code here
                values["projection"] = (projection, "WKT")
            if extent:
                values["extent"] = extent

            return values
            
        raise Exception("Could not parse from obj '%s'." % repr(obj))

