#------# ------------------------------------------------------------------------------
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

from django.contrib.gis.geos import Polygon

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.resources.coverages.metadata.utils.landsat8_l1 import (
    is_landsat8_l1_metadata_content, parse_landsat8_l1_metadata_content
)


class Landsat8L1CoverageMetadataReader(object):
    def test(self, obj):
        return is_landsat8_l1_metadata_content(obj)

    def get_format_name(self, obj):
        return "Landsat-8"

    def read(self, obj):
        md = parse_landsat8_l1_metadata_content(obj)

        p = md['PRODUCT_METADATA']
        ul = float(p['CORNER_UL_LON_PRODUCT']), float(p['CORNER_UL_LAT_PRODUCT'])
        ur = float(p['CORNER_UR_LON_PRODUCT']), float(p['CORNER_UR_LAT_PRODUCT'])
        ll = float(p['CORNER_LL_LON_PRODUCT']), float(p['CORNER_LL_LAT_PRODUCT'])
        lr = float(p['CORNER_LR_LON_PRODUCT']), float(p['CORNER_LR_LAT_PRODUCT'])

        values = {}
        values['identifier'] = md['METADATA_FILE_INFO']['LANDSAT_SCENE_ID']
        values['footprint'] = Polygon([ul, ur, lr, ll, ul])
        time = parse_iso8601('%sT%s' % (
            p['DATE_ACQUIRED'], p['SCENE_CENTER_TIME']
        ))
        values['begin_time'] = values['end_time'] = time

        return values
