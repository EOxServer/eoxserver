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

from typing import List, Tuple, Optional, Union

from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal import SpatialReference, CoordTransform, DataSource

from eoxserver.contrib import gdal
from eoxserver.backends.access import get_vsi_path, get_vsi_env, gdal_open
from eoxserver.render.coverage.objects import Coverage


BROWSE_MODE_RGB = "rgb"
BROWSE_MODE_RGBA = "rgba"
BROWSE_MODE_GRAYSCALE = "grayscale"


OptionalNumeric = Optional[Union[float, int]]


class Browse(object):
    def __init__(self, name, filename, env, size, extent, crs, mode, footprint):
        self._name = name
        self._filename = filename
        self._env = env
        self._size = size
        self._extent = extent
        self._crs = crs
        self._mode = mode
        self._footprint = footprint

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        return self._filename

    @property
    def env(self):
        return self._env

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
        if self._footprint:
            return self._footprint
        else:
            polygon = Polygon.from_bbox(self.extent)
            srs = SpatialReference(self.crs)
            if srs.srid != 4326:
                ct = CoordTransform(srs, SpatialReference(4326))
                polygon.transform(ct)
            return polygon

    @classmethod
    def from_model(cls, product_model, browse_model):
        filename = get_vsi_path(browse_model)
        env = get_vsi_env(browse_model.storage)
        size = (browse_model.width, browse_model.height)
        extent = (
            browse_model.min_x, browse_model.min_y,
            browse_model.max_x, browse_model.max_y
        )

        ds = gdal_open(browse_model)
        mode = _get_ds_mode(ds)
        ds = None

        if browse_model.browse_type:
            name = '%s__%s' % (
                product_model.identifier, browse_model.browse_type.name
            )
        else:
            name = product_model.identifier

        return cls(
            name, filename, env, size, extent,
            browse_model.coordinate_reference_system, mode,
            product_model.footprint
        )

    @classmethod
    def from_file(cls, filename, env=None):
        env = env or {}
        ds = gdal.Open(filename)
        size = (ds.RasterXSize, ds.RasterYSize)
        extent = gdal.get_extent(ds)
        mode = _get_ds_mode(ds)

        return cls(
            filename, env, filename, size, extent,
            ds.GetProjection(), mode, None
        )


class GeneratedBrowse(Browse):
    def __init__(self, name, band_expressions, ranges, nodata_values,
                 fields_and_coverages, field_list, footprint, variables,
                 show_out_of_bounds_data=False,
                 ):
        self._name = name
        self._band_expressions = band_expressions
        self._ranges = ranges
        self._nodata_values = nodata_values
        self._fields_and_coverages = fields_and_coverages
        self._field_list = field_list
        self._footprint = footprint
        self._variables = variables
        self._show_out_of_bounds_data = show_out_of_bounds_data

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        for field, coverages in self._fields_and_coverages.items():
            return coverages[0].size

    @property
    def extent(self):
        for field, coverages in self._fields_and_coverages.items():
            return coverages[0].extent

    @property
    def crs(self):
        for field, coverages in self._fields_and_coverages.items():
            return coverages[0].grid.coordinate_reference_system

    @property
    def spatial_reference(self):
        for field, coverages in self._fields_and_coverages.items():
            return coverages[0].grid.spatial_reference

    @property
    def mode(self):
        field_count = len(self._band_expressions)
        if field_count == 1:
            return BROWSE_MODE_GRAYSCALE
        elif field_count == 3:
            return BROWSE_MODE_RGB
        elif field_count == 4:
            return BROWSE_MODE_RGB

    @property
    def band_expressions(self):
        return self._band_expressions

    @property
    def ranges(self) -> List[Tuple[OptionalNumeric, OptionalNumeric]]:
        return self._ranges

    @property
    def nodata_values(self) -> List[OptionalNumeric]:
        return self._nodata_values

    @property
    def fields_and_coverages(self):
        return self._fields_and_coverages

    @property
    def field_list(self):
        return self._field_list

    @property
    def variables(self):
        return self._variables

    @property
    def show_out_of_bounds_data(self) -> bool:
        return self._show_out_of_bounds_data

    @classmethod
    def from_coverage_models(cls, band_expressions, ranges, nodata_values,
                             fields_and_coverage_models,
                             product_model, variables, show_out_of_bounds_data):

        fields_and_coverages = {
            field_name: [
                Coverage.from_model(coverage)
                for coverage in coverages
            ]
            for field_name, coverages in fields_and_coverage_models.items()
        }

        return cls(
            product_model.identifier,
            band_expressions,
            ranges,
            nodata_values,
            fields_and_coverages, [
                fields_and_coverages[field_name][0].range_type.get_field(
                    field_name
                )
                for field_name in fields_and_coverages.keys()
            ],
            product_model.footprint,
            variables,
            show_out_of_bounds_data,
        )


class Mask(object):
    def __init__(self, filename=None, geometry=None, validity=False):
        self._filename = filename
        self._geometry = geometry
        self._validity = validity

    @property
    def filename(self):
        return self._filename

    @property
    def geometry(self):
        return self._geometry

    def load_geometry(self):
        ds = DataSource(self.filename)
        layer = ds[0]
        geometries = layer.get_geoms()

        first = geometries[0]
        for other in geometries[1:]:
            first = first.union(other)
        return first.geos

    @property
    def validity(self):
        return self._validity

    @classmethod
    def from_model(cls, mask_model, mask_type):
        filename = None
        if mask_model and mask_model.location:
            filename = get_vsi_path(mask_model)

        geometry = None
        if mask_model:
            geometry = mask_model.geometry

        mask_type = mask_type or mask_model.mask_type

        validity = False
        if mask_type:
            validity = mask_type.validity

        return cls(filename, geometry, validity)


class MaskedBrowse(object):
    def __init__(self, browse, mask):
        self._browse = browse
        self._mask = mask

    @property
    def browse(self):
        return self._browse

    @property
    def mask(self):
        return self._mask

    @classmethod
    def from_models(cls, product_model, browse_model, mask_model,
                    mask_type_model):
        return cls(
            Browse.from_model(product_model, browse_model),
            Mask.from_model(mask_model, mask_type_model)
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
