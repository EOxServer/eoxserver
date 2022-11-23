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

from weakref import proxy
from typing import List

from eoxserver.render.coverage.objects import (
    GRID_TYPE_TEMPORAL, GRID_TYPE_ELEVATION, Coverage, Mosaic,
)


class Layer(object):
    """ Abstract layer
    """
    def __init__(self, name, style):
        self._name = name
        self._style = style
        self._map = None

    @property
    def name(self):
        return self._name

    @property
    def style(self):
        return self._style

    @property
    def map(self):
        return self._map

    @map.setter
    def map(self, map_):
        self._map = proxy(map_)


class CoverageLayer(Layer):
    """ Representation of a coverage layer.
    """
    def __init__(self, name, style, coverage, bands, wavelengths, time,
                 elevation, ranges):
        super(CoverageLayer, self).__init__(name, style)
        self._coverage = coverage
        self._bands = bands
        self._wavelengths = wavelengths
        self._time = time
        self._elevation = elevation
        self._ranges = ranges

    @property
    def coverage(self) -> Coverage:
        return self._coverage

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths

    @property
    def time(self):
        return self._time

    @property
    def elevation(self):
        return self._elevation

    @property
    def ranges(self):
        return self._ranges


class CoveragesLayer(Layer):
    """ Representation of a coverages layer.
    """
    def __init__(self, name, style, coverages, bands, wavelengths, time,
                 elevation, ranges):
        super(CoveragesLayer, self).__init__(name, style)
        self._coverages = coverages
        self._bands = bands
        self._wavelengths = wavelengths
        self._time = time
        self._elevation = elevation
        self._ranges = ranges

    @property
    def coverages(self) -> List[Coverage]:
        return self._coverages

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths

    @property
    def time(self):
        return self._time

    @property
    def elevation(self):
        return self._elevation

    @property
    def ranges(self):
        return self._ranges


class OutlinedCoveragesLayer(Layer):
    """ Representation of an outlined coverages layer.
    """
    def __init__(self, name, style, coverages, bands, wavelengths, time,
                 elevation, ranges):
        super(OutlinedCoveragesLayer, self).__init__(name, style)
        self._coverages = coverages
        self._bands = bands
        self._wavelengths = wavelengths
        self._time = time
        self._elevation = elevation
        self._ranges = ranges

    @property
    def coverages(self):
        return self._coverages

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths

    @property
    def time(self):
        return self._time

    @property
    def elevation(self):
        return self._elevation

    @property
    def ranges(self):
        return self._ranges


class MosaicLayer(Layer):
    def __init__(self, name, style, mosaic, coverages, bands, wavelengths, time,
                 elevation, ranges):
        super(MosaicLayer, self).__init__(name, style)
        self._mosaic = mosaic
        self._coverages = coverages
        self._bands = bands
        self._wavelengths = wavelengths
        self._time = time
        self._elevation = elevation
        self._ranges = ranges

    @property
    def mosaic(self) -> Mosaic:
        return self._mosaic

    @property
    def coverages(self):
        return self._coverages

    @property
    def bands(self):
        return self._bands

    @property
    def wavelengths(self):
        return self._wavelengths

    @property
    def time(self):
        return self._time

    @property
    def elevation(self):
        return self._elevation

    @property
    def ranges(self):
        return self._ranges


class BrowseLayer(Layer):
    """ Representation of a browse layer.
    """
    def __init__(self, name, style, browses, ranges=None):
        super(BrowseLayer, self).__init__(name, style)
        self._browses = browses
        self._ranges = ranges

    @property
    def browses(self):
        return self._browses

    @property
    def ranges(self):
        return self._ranges


class OutlinedBrowseLayer(Layer):
    """ Representation of a browse layer.
    """
    def __init__(self, name, style, browses, ranges=None):
        super(OutlinedBrowseLayer, self).__init__(name, style)
        self._browses = browses
        self._ranges = ranges

    @property
    def browses(self):
        return self._browses

    @property
    def ranges(self):
        return self._ranges


class MaskLayer(Layer):
    """ Representation of a mask layer.
    """
    def __init__(self, name, style, masks):
        super(MaskLayer, self).__init__(name, style)
        self._masks = masks

    @property
    def masks(self):
        return self._masks


class MaskedBrowseLayer(Layer):
    """ Representation of a layer.
    """
    def __init__(self, name, style, masked_browses):
        super(MaskedBrowseLayer, self).__init__(name, style)
        self._masked_browses = masked_browses

    @property
    def masked_browses(self):
        return self._masked_browses


class OutlinesLayer(Layer):
    """ Representation of a layer.
    """
    def __init__(self, name, style, fill, footprints, masks=None):
        super(OutlinesLayer, self).__init__(name, style)
        self._footprints = footprints
        self._masks = masks
        self._fill = fill

    @property
    def footprints(self):
        return self._footprints

    @property
    def masks(self):
        return self._masks

    @property
    def fill(self):
        return self._fill


class Map(object):
    """ Abstract interpretation of a map to be drawn.
    """
    def __init__(self, layers: List[Layer], width, height, format, bbox, crs, bgcolor=None,
                 transparent=True, time=None, elevation=None):
        self._layers = layers
        self._width = int(width)
        self._height = int(height)
        self._format = format
        self._bbox = bbox
        self._crs = crs
        self._bgcolor = bgcolor
        self._transparent = transparent
        self._time = time
        self._elevation = elevation

        for layer in layers:
            layer.map = self

    @property
    def layers(self) -> List[Layer]:
        return self._layers

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def format(self):
        return self._format

    @property
    def bbox(self):
        return self._bbox

    @property
    def crs(self):
        return self._crs

    @property
    def bgcolor(self):
        return self._bgcolor

    @property
    def transparent(self):
        return self._transparent

    @property
    def time(self):
        return self._time

    @property
    def elevation(self):
        return self._elevation

    def __repr__(self):
        return (
            'Map: %r '
            'width=%r '
            'height=%r '
            'format=%r '
            'bbox=%r '
            'crs=%r '
            'bgcolor=%r '
            'transparent=%r '
            'time=%r '
            'elevation=%r' % (
                self.layers, self.width, self.height, self.format, self.bbox,
                self.crs, self.bgcolor, self.transparent, self.time,
                self.elevation,
            )
        )


class LayerDescription(object):
    """ Abstract layer description
    """

    is_raster = False

    def __init__(self, name, bbox=None, dimensions=None, queryable=False,
                 styles=None, sub_layers=None, title=None):
        self._name = name
        self._bbox = bbox
        self._dimensions = dimensions if dimensions is not None else {}
        self._queryable = queryable
        self._styles = styles if styles is not None else []
        self._sub_layers = sub_layers if sub_layers is not None else []
        self._title = title

    @property
    def name(self):
        return self._name

    @property
    def bbox(self):
        return self._bbox

    @property
    def dimensions(self):
        return self._dimensions

    @property
    def queryable(self):
        return self._queryable

    @property
    def styles(self):
        return self._styles

    @property
    def sub_layers(self):
        return self._sub_layers

    @property
    def title(self):
        return self._title or self.name

    @classmethod
    def from_coverage(cls, coverage, styles):
        extent = coverage.extent
        grid = coverage.grid

        dimensions = {}
        if GRID_TYPE_ELEVATION in grid.types:
            elevation_dim = grid.types.index(GRID_TYPE_ELEVATION)
            dimensions['elevation'] = {
                'min': extent[elevation_dim],
                'max': extent[len(extent) / 2 + elevation_dim],
                'step': grid.offsets[elevation_dim],
                'default': extent[len(extent) / 2 + elevation_dim],
                'units': 'CRS:'  # TODO: get vertical part of crs
            }

        if GRID_TYPE_TEMPORAL in grid.types:
            temporal_dim = grid.types.index(GRID_TYPE_TEMPORAL)
            dimensions['time'] = {
                'min': extent[temporal_dim],
                'max': extent[len(extent) / 2 + temporal_dim],
                'step': grid.offsets[temporal_dim],
                'default': extent[len(extent) / 2 + temporal_dim],
                'units': 'ISO8601'
            }

        range_type = coverage.range_type
        band_names = [
            field.identifier for field in range_type
        ]
        wavelengths = [
            str(field.wavelength)
            for field in range_type
            if field.wavelength is not None
        ]

        dimensions['bands'] = {'values': band_names}

        if wavelengths:
            dimensions['wavelength'] = {'values': wavelengths}

        return cls(
            coverage.identifier,
            bbox=coverage.footprint.extent if coverage.footprint else None,
            dimensions=dimensions,
            styles=styles
        )

    @property
    def from_browse_type(cls, eo_object, browse_type):
        browse_type
