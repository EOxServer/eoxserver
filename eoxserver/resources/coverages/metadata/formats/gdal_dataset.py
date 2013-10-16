#-------------------------------------------------------------------------------
# $Id$
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

from eoxserver.core import Component, ExtensionPoint, implements
from eoxserver.contrib import gdal
from eoxserver.resources.coverages.metadata.interfaces import (
    MetadataReaderInterface, GDALDatasetMetadataReaderInterface
)
from eoxserver.processing.gdal import reftools


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
        if ds is not None:
            size = (ds.RasterXSize, ds.RasterYSize)
            gt = ds.GetGeoTransform()
            extent = None

            if gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
                x_extent = (gt[0], gt[0] + size[0] * gt[1])
                y_extent = (gt[3] + size[1] * gt[5], gt[3])

                extent = (
                    min(x_extent),
                    min(y_extent),
                    max(x_extent),
                    max(y_extent)
                )
            
            projection = ds.GetProjection()

            values = {
                "size": (ds.RasterXSize, ds.RasterYSize),
            }

            if projection:
                values["projection"] = (projection, "WKT")
            if extent:
                values["extent"] = extent

            reader = self._find_additional_reader(ds)
            if reader:
                additional_values = reader.read_ds(ds)
                for key, value in additional_values.items():
                    values.setdefault(key, value)

            if ds.GetGCPCount() > 0:
                values["footprint"] = GEOSGeometry(
                    reftools.get_footprint_wkt(raw_metadata)
                )

            return values

            
            
        raise Exception("Could not parse from obj '%s'." % repr(obj))

    def _find_additional_reader(self, ds):
        for reader in self.additional_readers:
            if reader.test_ds(ds):
                return reader
        return None
