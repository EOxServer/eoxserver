#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from os.path import join
from uuid import uuid4

from eoxserver.backends.access import get_vsi_path
from eoxserver.contrib import vsi, gdal
from eoxserver.processing.gdal.vrt import create_simple_vrt
from eoxserver.processing.gdal import reftools
from eoxserver.resources.coverages.dateline import wrap_extent_around_dateline


class SimpleConnector(object):
    """ Connector for single file layers.
    """

    def supports(self, coverage, data_items):
        return len(data_items) == 1

    def connect(self, coverage, data_items, layer, options):
        data = data_items[0].path

        if coverage.grid.is_referenceable:
            vrt_path = join("/vsimem", uuid4().hex)
            reftools.create_rectified_vrt(data, vrt_path)
            data = vrt_path
            layer.setMetaData("eoxs_ref_data", data)

        if not layer.metadata.get("eoxs_wrap_dateline") == "true":
            layer.data = data
        else:
            sr = coverage.grid.spatial_reference
            extent = coverage.extent
            e = wrap_extent_around_dateline(extent, sr.srid)

            vrt_path = join("/vsimem", uuid4().hex)
            ds = gdal.Open(data)
            vrt_ds = create_simple_vrt(ds, vrt_path)
            size_x = ds.RasterXSize
            size_y = ds.RasterYSize

            dx = abs(e[0] - e[2]) / size_x
            dy = abs(e[1] - e[3]) / size_y

            vrt_ds.SetGeoTransform([e[0], dx, 0, e[3], 0, -dy])
            vrt_ds = None

            layer.data = vrt_path

    def disconnect(self, coverage, data_items, layer, options):
        if layer.metadata.get("eoxs_wrap_dateline") == "true":
            vsi.remove(layer.data)

        vrt_path = layer.metadata.get("eoxs_ref_data")
        if vrt_path:
            vsi.remove(vrt_path)
