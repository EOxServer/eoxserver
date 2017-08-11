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


class Layer(object):
    """ Abstract layer
    """
    def __init__(self, style):
        self._style = style

    @property
    def style(self):
        return self._style


class CoverageLayer(Layer):
    """ Representation of a coverage layer.
    """
    def __init__(self, coverage, bands, wavelengths, style):
        super(CoverageLayer, self).__init__(style)
        self._coverage = coverage
        self._bands = bands
        self._wavelengths = wavelengths

    @property
    def coverage(self):
        return self._coverage

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths


class CoverageMosaicLayer(Layer):
    def __init__(self, coverages, bands, wavelengths, style):
        super(CoverageMosaicLayer, self).__init__(style)
        self._coverages = coverages
        self._bands = bands
        self._wavelengths = wavelengths

    @property
    def coverages(self):
        return self._coverages

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths


class BrowseLayer(Layer):
    """ Representation of a browse layer.
    """
    def __init__(self, browses, style):
        super(BrowseLayer, self).__init__(style)
        self._browses = browses

    @property
    def browses(self):
        return self._browses


class MaskLayer(Layer):
    """ Representation of a mask layer.
    """
    def __init__(self, masks, style):
        super(MaskLayer, self).__init__(style)
        self._masks = masks

    @property
    def masks(self):
        return self._masks


class MaskedBrowseLayer(Layer):
    """ Representation of a layer.
    """
    def __init__(self, masked_browses, style):
        super(MaskedBrowseLayer, self).__init__(style)
        self._masked_browses = masked_browses

    @property
    def masked_browses(self):
        return self._masked_browses


class OutlinesLayer(Layer):
    """ Representation of a layer.
    """
    def __init__(self, footprints, style):
        super(OutlinesLayer, self).__init__(style)
        self._footprints = footprints

    @property
    def footprints(self):
        return self._footprints


class Map(list):
    """ Abstract interpretation of a map to be drawn.
    """
    def __init__(self, width, height, bbox, crs, layers):
        super(Map, self).__init__(layers)

        self._width = width
        self._height = height
        self._bbox = bbox
        self._crs = crs

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def bbox(self):
        return self._bbox

    @property
    def crs(self):
        return self._crs
