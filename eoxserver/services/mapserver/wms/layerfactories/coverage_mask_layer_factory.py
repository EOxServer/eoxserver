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


import logging

from eoxserver.contrib import mapserver as ms
from eoxserver.backends.access import connect
from eoxserver.resources.coverages import models, crss
from eoxserver.resources.coverages.dateline import (
    extent_crosses_dateline, wrap_extent_around_dateline
)
from eoxserver.services.mapserver.wms.layerfactories.base import (
    AbstractLayerFactory
)



logger = logging.getLogger(__name__)


class CoverageMaskedLayerFactory(AbstractLayerFactory):
    handles = ()
    suffixes = ("_masked",)
    requires_connection = True

    def generate(self, eo_object, group_layer, suffix, options):
        name = eo_object.identifier + suffix
        all_data_items = eo_object.data_items.all()

        mask_semantics = ("polygonmask",)
        mask_items = all_data_items
        for mask_semantic in mask_semantics:
            mask_items = mask_items.filter(semantic__startswith=mask_semantic)

        # check if it is required to create a group layer for the masks
        if len(mask_items) > 1:
            # more than one mask, requires a mask group layer
            mask_group_layer = Layer(eo_object.identifier + "__mask__")
            yield (mask_group_layer, ())
        else:
            mask_group_layer = None

        # generate mask layers
        for i, mask_item in enumerate(mask_items):
            if not mask_group_layer:
                # single mask, set it as the "group"
                mask_layer = self.create_mask_polygon_layer(
                    eo_object.identifier + "__mask__"
                )
                mask_group_layer = mask_layer
            else: 
                mask_layer = self.create_mask_polygon_layer(
                    "%s__mask__%d" % (eo_object.identifier, i)
                )
                mask_layer.group = mask_group_layer.name

            yield (mask_layer, (mask_item,))


        super_items = super(CoverageMaskedLayerFactory, self).generate(
            eo_object, group_layer, suffix, options
        )
        for layer, data_items in super_items:
            # if we do have a mask, reference it in the layer
            if mask_group_layer:
                layer.mask = mask_layer.name

            # set the layer name with the right suffix
            layer.name = layer.name + suffix
            if layer.group:
                layer.group = layer.group + suffix

            # "re-yield" the layer and its items
            yield (layer, data_items)

    def create_mask_polygon_layer(self, name):
        mask_layer = ms.layerObj()
        mask_layer.name = name
        mask_layer.type = ms.MS_LAYER_POLYGON

        mask_layer.setMetaData("eoxs_geometry_reversed", "true")

        cls = ms.classObj(mask_layer)
        style = ms.styleObj(cls)
        style.color.setRGB(0, 0, 0)
        return mask_layer

    def generate_group(self, name):
        layer = ms.layerObj()
        layer.name = name
        layer.type = ms.MS_LAYER_RASTER
        return layer

