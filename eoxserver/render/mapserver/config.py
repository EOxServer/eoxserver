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

DEFAULT_EOXS_MAPSERVER_LAYER_FACTORIES = [
    'eoxserver.render.mapserver.factories.CoverageLayerFactory',
    'eoxserver.render.mapserver.factories.OutlinedCoverageLayerFactory',
    'eoxserver.render.mapserver.factories.MosaicLayerFactory',
    'eoxserver.render.mapserver.factories.BrowseLayerFactory',
    'eoxserver.render.mapserver.factories.OutlinedBrowseLayerFactory',
    'eoxserver.render.mapserver.factories.MaskLayerFactory',
    'eoxserver.render.mapserver.factories.MaskedBrowseLayerFactory',
    'eoxserver.render.mapserver.factories.OutlinesLayerFactory',
]
