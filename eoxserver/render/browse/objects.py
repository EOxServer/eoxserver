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

from eoxserver.contrib import gdal
from eoxserver.contrib.osr import SpatialReference
from eoxserver.backends.access import get_vsi_path


BROWSE_MODE_RGB = "rgb"
BROWSE_MODE_RGBA = "rgba"
BROWSE_MODE_GRAYSCALE = "grayscale"


class Browse(object):
    def __init__(self, name, browse_filename, size, extent, crs, mode,
                 footprint):
        self._name = name
        self._browse_filename = browse_filename
        self._size = size
        self._extent = extent
        self._crs = crs
        self._mode = mode
        self._footprint = footprint

    @property
    def name(self):
        return self._name

    @property
    def browse_filename(self):
        return self._browse_filename

    @property
    def size(self):
        return self._size

    @property
    def extent(self):
        return self._extent

    @property
    def crs(self):
        return self._crs

    @property
    def spatial_reference(self):
        return SpatialReference(self.crs)

    @property
    def mode(self):
        return self._mode

    @property
    def footprint(self):
        return self._footprint

    @classmethod
    def from_model(cls, product_model, browse_model):
        filename = get_vsi_path(browse_model)
        size = (browse_model.width, browse_model.height)
        extent = (
            browse_model.min_x, browse_model.min_y,
            browse_model.max_x, browse_model.max_y
        )

        ds = gdal.Open(filename)
        mode = _get_ds_mode(ds)
        ds = None

        if browse_model.browse_type:
            name = '%s__%s' % (
                product_model.identifier, browse_model.browse_type.name
            )
        else:
            name = product_model.identifier

        return cls(
            name, filename, size, extent,
            browse_model.coordinate_reference_system, mode,
            product_model.footprint
        )

    @classmethod
    def from_file(cls, filename):
        ds = gdal.Open(filename)
        size = (ds.RasterXSize, ds.RasterYSize)
        extent = gdal.get_extent(ds)
        mode = _get_ds_mode(ds)

        return cls(
            filename, filename, size, extent, ds.GetProjection(), mode, None
        )


class Mask(object):
    def __init__(self, mask_filename=None, geometry=None):
        assert mask_filename or geometry

        self._mask_filename = mask_filename
        self._geometry = geometry

    @property
    def mask_filename(self):
        return self._mask_filename

    @property
    def geometry(self):
        return self._geometry

    @classmethod
    def from_model(cls, mask_model):
        return cls(
            get_vsi_path(mask_model) if mask_model.location else None,
            mask_model.geometry
        )


class MaskedBrowse(Mask, Browse):
    def __init__(self, name, browse_filename, size, extent, crs, mode, footprint,
                 mask_filename=None, geometry=None):
        Browse.__init__(
            self, browse_filename, size, extent, crs, mode, footprint
        )
        Mask.__init__(self, mask_filename, geometry)

    @classmethod
    def from_browse_and_mask(cls, browse, mask):
        return cls(
            browse.browse_filename, browse.size, browse.extent, browse.crs,
            browse.mode, browse.footprint, mask.mask_filename, mask.geometry
        )

    @classmethod
    def from_models(cls, product_model, browse_model, mask_model):
        return cls.from_browse_and_mask(
            Browse.from_model(product_model, browse_model),
            Mask.from_model(mask_model)
        )


def _get_ds_mode(ds):
    first = ds.GetRasterBand(1)

    count = ds.RasterCount
    if count == 1 or count > 4 and not first.GetColorTable():
        mode = BROWSE_MODE_GRAYSCALE
    elif (count == 1 and first.GetColorTable()) or count == 4:
        mode = BROWSE_MODE_RGBA
    elif count == 3 and first.GetColorInterpretation() == gdal.GCI_RedBand:
        mode = BROWSE_MODE_RGB

    return mode
