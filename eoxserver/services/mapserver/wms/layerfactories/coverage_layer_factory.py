#-------------------------------------------------------------------------------
# $Id$
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


from eoxserver.core import Component, implements
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import models, crss
from eoxserver.resources.coverages.dateline import (
    extent_crosses_dateline, wrap_extent_around_dateline
)
from eoxserver.services.mapserver.interfaces import LayerFactoryInterface
from eoxserver.services.mapserver.wms.layerfactories import (
    AbstractLayerFactory, OffsiteColorMixIn
)


class CoverageLayerFactory(OffsiteColorMixIn, AbstractLayerFactory):
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    suffixes = (None,)
    requires_connection = True

    def generate(self, eo_object, group_layer, suffix, options):
        coverage = eo_object.cast()
        extent = coverage.extent
        srid = coverage.srid

        data_items = coverage.data_items.all()
        range_type = coverage.range_type

        offsite = self.offsite_color_from_range_type(range_type)
        
        if extent_crosses_dateline(extent, srid):
            identifier = coverage.identifier
            wrapped_extent = wrap_extent_around_dateline(extent, srid)
            layer = self._create_layer(
                coverage, identifier + "_unwrapped", extent, identifier
            )
            if offsite:
                layer.offsite = offsite
            yield layer, data_items
            wrapped_layer = self._create_layer(
                coverage, identifier + "_wrapped", wrapped_extent, identifier, True
            )
            if offsite:
                wrapped_layer.offsite = offsite
            yield wrapped_layer, data_items
        else:
            layer = self._create_layer(
                coverage, coverage.identifier, extent
            )
            if offsite:
                layer.offsite = offsite
            yield layer, data_items


    def generate_group(self, name):
        return ms.Layer(name)
