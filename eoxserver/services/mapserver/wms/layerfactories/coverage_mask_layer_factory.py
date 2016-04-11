#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011-2014 EOX IT Services GmbH
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
from eoxserver.resources.coverages import models

from eoxserver.services.mapserver.wms.layerfactories.base import (
    BaseCoverageLayerFactory
)


class CoverageMaskedLayerFactory(BaseCoverageLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    suffixes = ("_masked",)
    requires_connection = True

    def generate(self, eo_object, group_layer, suffix, options):
        mask_layer_name = eo_object.identifier + "__mask__"

        # handle the mask layers

        # get the applicable sematics
        mask_semantics = ("polygonmask",)
        mask_items = eo_object.data_items.all()
        for mask_semantic in mask_semantics:
            mask_items = mask_items.filter(semantic__startswith=mask_semantic)

        # layer creating closure
        def _create_mask_polygon_layer(name):
            mask_layer = ms.layerObj()
            mask_layer.name = name
            mask_layer.type = ms.MS_LAYER_POLYGON

            mask_layer.setMetaData("eoxs_geometry_reversed", "true")

            cls = ms.classObj(mask_layer)
            style = ms.styleObj(cls)
            style.color.setRGB(0, 0, 0)
            return mask_layer

        # multiple masks shall be grouped by a group layer
        if len(mask_items) > 1:

            # more than one mask, requires a mask group layer
            mask_layer = ms.Layer(mask_layer_name)

            yield (mask_layer, ())

            # generate mask layers
            for i, mask_item in enumerate(mask_items):

                mask_sublayer = _create_mask_polygon_layer(
                    "%s%2.2d" % (mask_layer_name, i)
                )
                mask_sublayer.group = mask_layer.name

                yield (mask_sublayer, (mask_item,))

        # single mask shall be used directly as a "group" layer
        elif len(mask_items) == 1:

            mask_layer = _create_mask_polygon_layer(mask_layer_name)

            yield (mask_layer, (mask_items[0],))

        # no mask at all
        else:
            mask_layer = None

        # handle the image layers
        super_items = super(CoverageMaskedLayerFactory, self).generate(
            eo_object, group_layer, suffix, options
        )

        for layer, data_items in super_items:

            # if we do have a mask, reference it in the layer
            if mask_layer:
                layer.mask = mask_layer.name

            # fix the layer name by appending the right suffix
            layer.name = layer.name + suffix
            if layer.group:
                layer.group = layer.group + suffix

            # "re-yield" the layer and its items
            yield (layer, data_items)

    def generate_group(self, name):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_RASTER
        return layer
