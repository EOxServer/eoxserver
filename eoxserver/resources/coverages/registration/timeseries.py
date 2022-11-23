# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Mussab Abdalla <mussab.abdalla@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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


from osgeo.osr import SpatialReference, CoordinateTransformation
from django.db import transaction
from django.contrib.gis.geos import Polygon
from django.core.management.base import CommandError
import numpy as np

from eoxserver.backends.access import get_vsi_env, get_vsi_storage_path
from eoxserver.contrib.gdal import config_env
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

logger = logging.getLogger(__name__)


def create_product(
    collection,
    begin_time,
    end_time,
    footprint,
    product_type,
    coverage_type_mapping,
    replace,
    driver_name,
    storage,
    path,
    index,
    all_overrides,
    file_identifier,
    product_template,
):
    template_values = {
        "collection_identifier": collection.identifier,
        "file_identifier": file_identifier,
        "index": index,
        "product_type": product_type,
        "begin_time": begin_time,
        "end_time": end_time
    }

    product_identifier = product_template.format(**template_values)

    replaced = False

    # check if the product already exists
    if models.Product.objects.filter(
            identifier=product_identifier).exists():
        if replace:
            logger.info('Deleting existing Product %s', product_identifier)
            models.Product.objects.filter(
                identifier=product_identifier).delete()
            replaced = True
        else:
            raise RegistrationError(
                'Product %s already exists' % product_identifier
            )

    product = models.Product.objects.create(
        identifier=product_identifier,
        begin_time=begin_time,
        end_time=end_time,
        footprint=footprint,
        product_type=product_type,
    )
    models.collection_insert_eo_object(collection, product)

    logger.info('Successfully created product %s', product_identifier)

    registrator = GDALRegistrator()

    # adding coverages:
    for dim_name, coverage_type_name in coverage_type_mapping.items():
        overrides = dict(all_overrides)
        coverage_type = None
        overrides['identifier'] = '%s_%s' % (product_identifier, coverage_type_name)
        overrides['footprint'] = footprint

        file_path = '%s:"%s":%s:%s' % (driver_name, path, dim_name, index)

        # TODO: coverage types created ? or configured and
        # all needed is the name?
        try:
            coverage_type = models.CoverageType.objects.get(
                name=coverage_type_name
            )
        except models.CoverageType.DoesNotExist:
            raise CommandError(
                "Coverage type %r does not exist." % coverage_type_name
            )

        report = registrator.register(
            data_locations=[([
                storage.name] if storage else []) + [file_path]],
            metadata_locations=[],
            coverage_type_name=coverage_type.name,
            footprint_from_extent=False,
            overrides=overrides,
            replace=replace,
            use_subdatasets=True,
        )
        models.product_add_coverage(product, report.coverage)

        # cache grid, size and origin, as it will be the same for all slices
        if not all_overrides:
            coverage = report.coverage
            all_overrides['grid'] = coverage.grid
            all_overrides['size'] = coverage.size
            all_overrides['origin'] = coverage.origin

        logger.info('Successfully created coverage %s' % overrides['identifier'])

    return (product, replaced)


def extent_to_footprint(crs_wkt, extent):
    dcrs = SpatialReference()
    dcrs.ImportFromWkt(crs_wkt)

    wgs84 = SpatialReference()
    wgs84.ImportFromEPSG(4326)

    dcrs2wgs84 = CoordinateTransformation(dcrs, wgs84)
    ll = dcrs2wgs84.TransformPoint(extent[0], extent[1])
    ur = dcrs2wgs84.TransformPoint(extent[2], extent[3])

    footprint = Polygon(
        (
            (ll[1], ll[0]),
            (ur[1], ll[0]),
            (ur[1], ur[0]),
            (ll[1], ur[0]),
            (ll[1], ll[0]),
        )
    )

    return footprint


def compute_min_max(dim):
    dimension = dim.ReadAsArray()
    return [dimension[0, 0], dimension[0, dimension.size - 1]]


def compute_extent(x_path, y_path):
    x_ds = open_with_env(x_path, {})
    y_ds = open_with_env(y_path, {})

    minmax_x = compute_min_max(x_ds)
    minmax_y = compute_min_max(y_ds)
    bbox = [minmax_x[0], minmax_y[0], minmax_x[1], minmax_y[1]]

    return bbox


def create_dates_array(time_path, begin_time):
    time_ds = open_with_env(time_path, {})
    ds_arr = np.nditer(time_ds.ReadAsArray(), flags=['f_index'])
    dates_array = []

    begin_dt = datetime.datetime.combine(
        begin_time, datetime.time.min, datetime.timezone.utc)
    for time in ds_arr:
        dt = begin_dt + datetime.timedelta(days=time.item())
        dates_array.append(dt)

    return [
        (dt, dt + datetime.timedelta(days=1))
        for dt in dates_array
    ]


@transaction.atomic
def register_time_series(
    collection,
    storage,
    path,
    product_type_name,
    coverage_type_mapping,
    x_dim_name,
    y_dim_name,
    time_dim_name,
    product_template,
    replace=True
):

    file_identifier = path.split("/")[-1].split(".")[0]

    if isinstance(storage, str):
        storage = backends.Storage.objects.get(name=storage)

    with config_env(get_vsi_env(storage)):
        vsi_path = get_vsi_storage_path(storage, path)
        metadata = gdal.MultiDimInfo(vsi_path)
        driver_name = metadata['driver'].upper()

        # TODO: get time array dynamically
        match = re.search(r'\d{4}-\d{2}-\d{2}', metadata['arrays']['time']['unit'])
        start_date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()

        fixed_dimensions = []
        for dimension in metadata['dimensions']:
            fixed_dimensions.append(dimension['name'])

        # footprint is the same for all ?

        extent = compute_extent(
            '%s:"%s":%s' % (driver_name, vsi_path, x_dim_name),
            '%s:"%s":%s' % (driver_name, vsi_path, y_dim_name),
        )

        for dim_name, dim in metadata['arrays'].items():
            if dim_name not in fixed_dimensions:
                footprint = extent_to_footprint(dim['srs']['wkt'], extent)
                break

        # create time array with date values
        date_array = create_dates_array(
            '%s:"%s":%s' % (driver_name, vsi_path, time_dim_name),
            start_date
        )

    product_type = models.ProductType.objects.get(name=product_type_name)

    overrides = {}
    for i, (begin_time, end_time) in enumerate(date_array):
        create_product(
            collection,
            begin_time,
            end_time,
            footprint,
            product_type,
            coverage_type_mapping,
            replace,
            driver_name,
            storage,
            path,
            i,
            overrides,
            file_identifier,
            product_template
        )

    return path, replace

# python3 manage.py shell -c "from eoxserver.resources.coverages.registration.zarr import register_time_series; register_time_series('test', 's3', 'filtered_zarr/32N.zarr', 'sample_collection', 'sample_type', {});"

# register_time_series(Collection(),'s3', 'filtered_zarr/32N.zarr', 'sample_type', {'/Band1': 'Band1', '/Band2': 'Band2', '/Band3': 'Band3', '/Band4': 'Band4', '/Band5': 'Band5'}, '/X', '/Y', '/time', "{collection_identifier}_{file_identifier}_{index}");


# python3 manage.py shell -c "from eoxserver.resources.coverages.registration.zarr import register_time_series ; register_time_series('test', 's3', 'filtered_zarr/32N.zarr', 'sample_collection', 'sample_type', {'/Band1': 'Band1', '/Band2': 'Band2', '/Band3': 'Band3', '/Band4': 'Band4', '/Band5': 'Band5'}, '/X', '/Y', '/time');"
