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

from eoxserver.core import Component, implements
from eoxserver.resources.coverages import models
from eoxserver.services.mapserver.interfaces import LayerPluginInterface
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, typelist

from eoxserver.services.mapserver.wms.layers.mask_layer_factory \
    import MaskLayerFactory


class EnabledMasksConfigReader(config.Reader):
    section = "services.ows.wms"
    mask_names = config.Option(type=typelist(str, ","), default=[])


class MaskLayerPlugin(Component):
    implements(LayerPluginInterface)
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic)
    requires_connection = True

    @property
    def suffixes(self):
        return ["_%s" % mask for mask in self.enabled_masks]

    @property
    def enabled_masks(self):
        return EnabledMasksConfigReader(get_eoxserver_config()).mask_names

    def get_layer_factory(self, suffix, options):
        factory = MaskLayerFactory(suffix, options)
        factory.plugin = self
        return factory

