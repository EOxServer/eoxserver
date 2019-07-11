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

from eoxserver.contrib import gdal
from eoxserver.processing.gdal import reftools as rt
from eoxserver.contrib import osr
from eoxserver.resources.coverages.metadata.coverage_formats import (
    get_gdal_dataset_format_readers
)


def open_gdal(obj):
    if isinstance(obj, gdal.Dataset):
        return obj
    try:
        return gdal.Open(obj)
    except RuntimeError:
        return None


class GDALDatasetMetadataReader(object):
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

        projection = ds.GetProjection()

        # --= rectified datasets =--
        # NOTE: If the projection is a non-zero string then
        #       the geocoding is given by the Geo-Trasnformation
        #       matrix - not matter what are the values.
        if projection and not (ds.GetGCPProjection() and ds.GetGCPCount() > 0):
            sr = osr.SpatialReference(projection)
            if sr.srid is not None:
                projection = 'EPSG:%d' % sr.srid

            gt = ds.GetGeoTransform()

            values['origin'] = [gt[0], gt[3]]

            values['grid'] = {
                'coordinate_reference_system': projection,
                'axis_offsets': [gt[1], gt[5]],
                'axis_types': ['spatial', 'spatial'],
                'axis_names': ['x', 'y'] if sr.IsProjected() else ['long', 'lat'],
            }

            if sr.GetLinearUnitsName() in ('metre', 'meter', 'm') \
                    and abs(gt[1]) == abs(gt[5]):
                values['grid']['resolution'] = abs(gt[1])

        # --= tie-point encoded referenceable datasets =--
        # NOTE: If the GCP projection is a non-zero string and
        #       there are GCPs we are dealing with a tie-point geocoded
        #       referenceable dataset. The extent is given by the image
        #       footprint. The fooprint must not be wrapped arround
        #       the date-line!
        elif ds.GetGCPProjection() and ds.GetGCPCount() > 0:
            projection = ds.GetGCPProjection()
            sr = osr.SpatialReference(projection)
            if sr.srid is not None:
                projection = 'EPSG:%d' % sr.srid

            values['grid'] = {
                'coordinate_reference_system': projection,
                'axis_offsets': [None, None],
                'axis_types': ['spatial', 'spatial'],
                'axis_names': ['x', 'y'] if sr.IsProjected() else ['long', 'lat']
            }
            values['origin'] = [None, None]

            # # parse the spatial reference to get the EPSG code
            sr = osr.SpatialReference(ds.GetGCPProjection(), "WKT")

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

                values['footprint'] = footprint
            pass

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
        for reader in get_gdal_dataset_format_readers():
            if reader.test_ds(ds):
                return reader
        return None
