# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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

from os.path import join
from uuid import uuid4

from eoxserver.contrib import vsi, gdal, vrt
from eoxserver.processing.gdal.vrt import create_simple_vrt
from eoxserver.processing.gdal import reftools
from eoxserver.render.coverage.objects import Mosaic
from eoxserver.resources.coverages.dateline import wrap_extent_around_dateline


class MosaicConnector(object):
    """ Connector for single file layers.
    """

    def supports(self, mosaic, data_items):
        return isinstance(mosaic, Mosaic)

    def connect(self, mosaic, data_items, layer, options):
        try:
            nodata_values = [
                field.nil_values[0][0]
                for field in mosaic.range_type
            ]
        except IndexError:
            nodata_values = None

        vrt_path = '/vsimem/%s.vrt' % uuid4().hex
        vrt.gdalbuildvrt(
            vrt_path, [
                coverage.arraydata_locations[0].path
                for coverage in mosaic.coverages
            ],
            nodata=nodata_values
        )
        layer.data = vrt_path

    def disconnect(self, coverage, data_items, layer, options):
        if layer.data:
            vsi.remove(layer.data)
