#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from django.contrib.gis.geos.collections import MultiPolygon
from eoxserver.contrib import mapserver as ms
from eoxserver.services.mapserver.wms.layers.base import (
    LayerFactory, StyledLayerMixIn, PolygonLayerMixIn,
)

class MaskLayerFactory(LayerFactory, PolygonLayerMixIn, StyledLayerMixIn):
    def _mask(self, mask_items, outline):
        mask = MultiPolygon(())
        for mask_item in mask_items:
            mask = mask | mask_item.geometry
        return mask & outline

    def generate(self):
        mask_name = self.suffix[1:]
        layer = self._polygon_layer(self.group, filled=True, srid=4326)

        for cov, cov_name in reversed(self.coverages):
            # get the mask items
            mask_items = cov.vector_masks.filter(
                semantic__startswith=mask_name
            )

            # get part of the visible footprint
            mask = self._mask(mask_items, cov.footprint)

            # skip empty masks
            if mask.empty:
                continue

            # generate feature
            shape = ms.shapeObj.fromWKT(mask.wkt)
            shape.initValues(2)
            shape.setValue(0, cov_name)
            shape.setValue(1, mask_name)

            # add feature to the group
            layer.addFeature(shape)

        yield layer, None, ()

