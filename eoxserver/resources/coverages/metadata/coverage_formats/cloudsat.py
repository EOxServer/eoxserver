# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from datetime import datetime

from django.contrib.gis.geos import Polygon, LineString, MultiLineString
from django.utils.timezone import make_aware, utc
from pyhdf.HDF import HDF, HC
from pyhdf.SD import SD
import pyhdf.VS

from eoxserver.contrib import gdal
from eoxserver.core.util.timetools import parse_iso8601


def open_gdal(obj):
    if isinstance(obj, gdal.Dataset):
        return obj
    try:
        return gdal.Open(obj)
    except RuntimeError:
        return None


def parse_datetime(value):
    return make_aware(
        datetime.strptime(value, '%Y%m%d%H%M%S'), utc
    )


class Cloudsat2BGeoprofCoverageMetadataReader(object):
    def test(self, obj):
        ds = open_gdal(obj)

        filename = ds.GetFileList()[0]

        sub_ds = open_gdal(
            'HDF4_EOS:EOS_SWATH:"%s":2B-GEOPROF:CPR_Cloud_mask'
            % filename
        )
        return sub_ds is not None

    def get_format_name(self, obj):
        return "cloudsat-2b-geoprof"

    def read(self, obj):
        ds = open_gdal(obj)
        filename = ds.GetFileList()[0]
        sub_ds = open_gdal(
            'HDF4_EOS:EOS_SWATH:"%s":2B-GEOPROF:CPR_Cloud_mask'
            % filename
        )
        metadata = sub_ds.GetMetadata()

        grid = {
            'coordinate_reference_system': 'EPSG:4326',
            'axis_offsets': [1, 1],
            'axis_types': ['temporal', 'elevation'],
            'axis_names': ['date', 'height'],
        }


        # driver = sub_ds.GetDriver()
        size = (sub_ds.RasterXSize, sub_ds.RasterYSize)

        stepsize = 10
        vdata = HDF(filename, HC.READ).vstart()
        lons = vdata.attach('Longitude')[:][0::stepsize]
        lats = vdata.attach('Latitude')[:][0::stepsize]

        footprint = MultiLineString(
            LineString([
                (lon[0], lat[0])
                for lon, lat in zip(lons, lats)
            ])
        )

        values = {
            "size": size,
            "begin_time": parse_datetime(metadata['start_time']),
            "end_time": parse_datetime(metadata['end_time']),
            "grid": grid,
            "footprint": footprint,
        }

        return values
