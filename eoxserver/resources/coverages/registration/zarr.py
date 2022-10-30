# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Mussab Abdalla <mussab.abdalla@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

from eoxserver.resources.coverages import models
from osgeo.osr import SpatialReference, CoordinateTransformation
from django.contrib.gis.geos import Polygon
from eoxserver.contrib.gdal import open_with_env, get_extent
from eoxserver.contrib import gdal
import numpy as np

import re
import datetime


def extract_products_values(dimension, extent):
    identifier = dimension['identifier']
    nodata_value = dimension['nodata_value']
    footprint = reproject_extent(dimension, extent)

    pass


def create_product(item_id, time, extent, metadata_arrays, xyz_dimensions):
    for dim in metadata_arrays:
        if dim not in xyz_dimensions:
            metadata_arrays[dim]["identifier"] = '%s_%s' % (item_id, dim)
            # TODO: register product
            # product_register(metadata_arrays[dim], extent)
    pass


def reproject_extent(dimension, extent):
    dscrs = dimension['srs']
    dcrs = SpatialReference()
    dcrs.ImportFromWkt(dscrs)

    wgs84 = SpatialReference()
    wgs84.ImportFromEPSG(4326)

    dcrs2wgs84 = CoordinateTransformation(dcrs, wgs84)
    wgs84_extent = dcrs2wgs84.TransformBounds(
        extent[0], extent[1], extent[2], extent[3], 21
        )
    footprint = Polygon(
            (
                (wgs84_extent[1], wgs84_extent[0]),
                (wgs84_extent[3], wgs84_extent[0]),
                (wgs84_extent[3], wgs84_extent[2]),
                (wgs84_extent[1], wgs84_extent[2]),
                (wgs84_extent[1], wgs84_extent[0]),
            )
        )

    return footprint.wkt


def compute_extent(path):
    x_ds = gdal.Open('%s:/X' % path)
    y_ds = gdal.Open('%s:/Y' % path)
    minmax_x = compute_min_max(x_ds)
    minmax_y = compute_min_max(y_ds)
    bbox = [minmax_x[0], minmax_y[0], minmax_x[1], minmax_y[1]]

    return bbox


def create_dates_array(path, begin_time):
    time_ds = gdal.Open('%s:/time' % path)
    ds_arr = np.nditer(time_ds.ReadAsArray(), flags=['f_index'])
    dates_array = []

    for time in ds_arr:
        date_value = begin_time + datetime.timedelta(days=time.item())
        dates_array.append(date_value)
    products_time_spans = []

    for i in range(len(dates_array)):
        products_time_spans.append({
            # TODO: figure out a way to compute begin time and end time
            'begin_time': dates_array[i].strftime('%Y-%m-%dT%H:%M:%SZ'),
            'end_time': (
                dates_array[i] + datetime.timedelta(days=1)
                ).strftime('%Y-%m-%dT%H:%M:%SZ')
        })

    return products_time_spans


def compute_min_max(dim):
    dimension = dim.ReadAsArray()
    return [dimension[0, 0], dimension[0, dimension.size-1]]


def register_zarr_item(zarr_item, collection_type=None, storage=None,):
    """ Registers a single zarr item as a Collection. The
        collection_type to be used can be specified via the product_type_name
        argument.
    """

    # TODO: Create a collection with the zarr item name
    # check if the collection does not already exist ?

    models.Collection.objects.create(
                identifier=zarr_item,
                collection_type=None, grid=None
            )

    # TODO: Open the zarr item and read the time dimension

    path = ''

    metadata = gdal.MultiDimInfo(path)

    fixed_dimensions = []
    for dimension in metadata['dimensions']:
        fixed_dimensions.append(dimension['name'])

    # footprint is the same for all ?

    extent = compute_extent(path)

    # get the start-date
    time_string = metadata['arrays']['time']['unit']
    match = re.search('\d{4}-\d{2}-\d{2}', time_string)
    start_date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()

    # TODO: create time array with date values
    date_array = create_dates_array(path, start_date)
    for time in date_array:

        create_product(
            zarr_item, time, extent, metadata['arrays'], fixed_dimensions)
