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


from eoxserver.contrib import mapserver as ms
from eoxserver.services.mapserver.wms.layerfactories.base import (
    AbstractLayerFactory, BaseStyleMixIn, PolygonLayerMixIn
)


class CoverageMaskedOutlinesLayerFactory(BaseStyleMixIn, PolygonLayerMixIn,
                                         AbstractLayerFactory):
    suffixes = ("_masked_outlines",)
    requires_connection = False

    def generate(self, eo_object, group_layer, suffix, options):
        # don't generate any layers, but add the footprint as feature to the
        # group layer

        if group_layer:
            layer = group_layer
        else:
            layer = self._create_polygon_layer(
                eo_object.identifier + "_masked_outlines"
            )

        coverage = eo_object.cast()
        layer.setMetaData("eoxs_geometry_reversed", "true")

        mask_items = coverage.data_items.filter(
            semantic__startswith="polygonmask"
        )

        # use the whole footprint if no mask is given
        if not len(mask_items):
            shape = ms.shapeObj.fromWKT(eo_object.footprint.wkt)
            shape.initValues(1)
            shape.setValue(0, eo_object.identifier)
            layer.addFeature(shape)

        yield layer, mask_items

    def generate_group(self, name):
        return self._create_polygon_layer(name)
