#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon

from eoxserver.core import Component, ExtensionPoint, implements
from eoxserver.contrib import gdal
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface, GDALDatasetMetadataReaderInterface
)
from eoxserver.processing.gdal import reftools as rt
from eoxserver.contrib import osr


def open_gdal(obj):
    if isinstance(obj, gdal.Dataset):
        return obj
    try:
        return gdal.Open(obj)
    except RuntimeError:
        return None


class GDALDatasetMetadataReader(Component):
    implements(MetadataReaderInterface)

    additional_readers = ExtensionPoint(GDALDatasetMetadataReaderInterface)

    def test(self, obj):
        return open_gdal(obj) is not None

    def get_format_name(self, obj):
        ds = open_gdal(obj)
        if not ds:
            return None

        driver = ds.GetDriver()
        return "GDAL/" + driver.ShortName

    def read(self, obj):
        ds = open_gdal(obj)
        if ds is None:
            raise Exception("Could not parse from obj '%s'." % repr(obj))

        driver = ds.GetDriver()
        size = (ds.RasterXSize, ds.RasterYSize)
        values = {"size": size}

        # --= rectified datasets =--
        # NOTE: If the projection is a non-zero string then
        #       the geocoding is given by the Geo-Trasnformation
        #       matrix - not matter what are the values.
        if ds.GetProjection():
            values["coverage_type"] = "RectifiedDataset"
            values["projection"] = (ds.GetProjection(), "WKT")

            # get coordinates of all four image corners
            gt = ds.GetGeoTransform()
            def gtrans(x, y):
                return gt[0] + x*gt[1] + y*gt[2], gt[3] + x*gt[4] + y*gt[5]
            vpix = [(0, 0), (0, size[1]), (size[0], 0), (size[0], size[1])]
            vx, vy = zip(*(gtrans(x, y) for x, y in vpix))

            # find the extent
            values["extent"] = (min(vx), min(vy), max(vx), max(vy))

        # --= tie-point encoded referenceable datasets =--
        # NOTE: If the GCP projection is a non-zero string and
        #       there are GCPs we are dealing with a tie-point geocoded
        #       referenceable dataset. The extent is given by the image
        #       footprint. The fooprint must not be wrapped arround
        #       the date-line!
        elif ds.GetGCPProjection() and ds.GetGCPCount() > 0:
            values["coverage_type"] = "ReferenceableDataset"
            projection = ds.GetGCPProjection()
            values["projection"] = (projection, "WKT")

            # parse the spatial reference to get the EPSG code
            sr = osr.SpatialReference(projection, "WKT")

            # NOTE: GeosGeometry can't handle non-EPSG geometry projections.
            if sr.GetAuthorityName(None) == "EPSG":
                srid = int(sr.GetAuthorityCode(None))

                # get the footprint
                rt_prm = rt.suggest_transformer(ds)
                fp_wkt = rt.get_footprint_wkt(ds, **rt_prm)
                footprint = GEOSGeometry(fp_wkt, srid)

                if isinstance(footprint, Polygon):
                    footprint = MultiPolygon(footprint)
                elif not isinstance(footprint, MultiPolygon):
                    raise TypeError(
                        "Got invalid geometry %s" % type(footprint).__name__
                    )

                values["footprint"] = footprint
                values["extent"] = footprint.extent

        # --= dataset with no geocoding =--
        # TODO: Handling of other types of GDAL geocoding (e.g, RPC).
        else:
            pass

        reader = self._find_additional_reader(ds)
        if reader:
            additional_values = reader.read_ds(ds)
            for key, value in additional_values.items():
                values.setdefault(key, value)

        driver_metadata = driver.GetMetadata()
        frmt = driver_metadata.get("DMD_MIMETYPE")
        if frmt:
            values["format"] = frmt

        return values

    def _find_additional_reader(self, ds):
        for reader in self.additional_readers:
            if reader.test_ds(ds):
                return reader
        return None
