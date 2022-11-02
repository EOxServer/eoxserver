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

import re
import datetime
import logging

from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)
from eoxserver.contrib.gdal import open_with_env
from eoxserver.contrib import gdal
from eoxserver.resources.coverages import models
from eoxserver.backends import models as backends
from eoxserver.resources.coverages.registration.registrators.gdal import (
    GDALRegistrator
)
from osgeo.osr import SpatialReference, CoordinateTransformation
from django.contrib.gis.geos import Polygon
from django.core.management.base import CommandError

import numpy as np

logger = logging.getLogger()


def create_product(item_id, time, footprint, band_arrays, storage,
                   xyz_dimensions, product_type, replace, path, index):

    product_identifier = '%s_slice_%s' % (item_id, index+1)
    # TODO: figure out how to compute/pass nodata
    # nodata_value = dim['nodata_value']

    product_type = models.ProductType.objects.get(name=product_type)

    replaced = False

    # check if the product already exists
    if models.Product.objects.filter(
            identifier=product_identifier).exists():
        if replace:
            logger.debug('Deleting existing Product %s' % product_identifier)
            models.Product.objects.filter(
                identifier=product_identifier).delete()
            replaced = True
        else:
            raise RegistrationError(
                'Product %s already exists' % product_identifier)

    product = models.Product.objects.create(
        identifier=product_identifier,
        begin_time=time['begin_time'],
        end_time=time['end_time'],
        footprint=footprint,
        product_type=product_type,
    )
    logger.debug('successfully Created product %s' % product_identifier)

    registrator = GDALRegistrator()

    # adding coverages:
    for dim in band_arrays:
        if dim not in xyz_dimensions:
            overrides = {}
            coverage_type = None
            overrides['identifier'] = '%s_%s' % (product_identifier, dim)
            overrides['footprint'] = footprint

            # nodata_value = dim['nodata_value']
            file_path = 'ZARR:"%s":/%s:%s' % (path, dim, index)
            # TODO: coverage types created ? or configured and
            # all needed is the name?
            try:
                coverage_type = models.CoverageType.objects.get(
                    name=dim
                )
            except models.CoverageType.DoesNotExist:
                raise CommandError(
                    "Coverage type %r does not exist." % dim
                )
            report = registrator.register(
                data_locations=[([
                    storage.name] if storage else []) + [file_path]],
                metadata_locations=[],
                coverage_type_name=coverage_type.name,
                footprint_from_extent=False,
                overrides=overrides,
                replace=replace,
            )

    models.product_add_coverage(product, report.coverage)
    logger.debug('successfully Created coverage %s' % overrides['identifier'])
    return (product, replaced)


def reproject_extent(dimension, extent):
    dscrs = dimension['srs']['wkt']
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


def compute_extent(path, env):
    x_ds = open_with_env('ZARR:"%s":/X' % path, env)
    y_ds = open_with_env('ZARR:"%s":/Y' % path, env)
    minmax_x = compute_min_max(x_ds)
    minmax_y = compute_min_max(y_ds)
    bbox = [minmax_x[0], minmax_y[0], minmax_x[1], minmax_y[1]]

    return bbox


def create_dates_array(path, env, begin_time):
    time_ds = open_with_env('ZARR:"%s":/time' % path, env)
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


def register_zarr_item(zarr_item, file_href=None,
                       env={}, storage=None, replace=False,):
    """ Registers a single zarr item as a Collection. The
        collection_type to be used can be specified via the product_type_name
        argument.
    """

    # Create a collection with the zarr item name
    # check if the collection does not already exist ?

    models.Collection.objects.create(
                identifier=zarr_item,
                collection_type=None, grid=None
            )

    # TODO: get metadata with env
    metadata = gdal.MultiDimInfo('ZARR:"%s"' % file_href)

    if isinstance(storage, str):
        storage = backends.Storage.objects.get(name=storage)

    fixed_dimensions = []
    for dimension in metadata['dimensions']:
        fixed_dimensions.append(dimension['name'])

    # footprint is the same for all ?

    extent = compute_extent(file_href, env)

    # get the start-date
    time_string = metadata['arrays']['time']['unit']
    match = re.search('\d{4}-\d{2}-\d{2}', time_string)
    start_date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()

    # create time array with date values
    date_array = create_dates_array(file_href, env, start_date)

    # create footprint, assuming that all bands share the same footprint and
    # projection the first band is the only one that is needed
    for dim in metadata['arrays']:
        if dim not in fixed_dimensions:
            footprint = reproject_extent(metadata['arrays'][dim], extent)
            if isinstance(footprint, str):
                break

    for i in range(len(date_array)):
        product_type = "%s_time%s" % (zarr_item, i+1)
        create_product(
            zarr_item, date_array[i], footprint, metadata['arrays'], storage,
            fixed_dimensions, product_type, replace, file_href, i)
