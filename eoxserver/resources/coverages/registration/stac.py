# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

import json
from os.path import isabs, join, dirname, normpath
from urllib.parse import urlparse

from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q
from django.db import transaction

from eoxserver.contrib import osr
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.backends import models as backends
from eoxserver.backends.access import gdal_open
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration.registrators.gdal import GDALRegistrator
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)
from eoxserver.resources.coverages.registration.product import create_metadata
from eoxserver.resources.coverages.registration.base import get_grid
from eoxserver.resources.coverages.metadata.coverage_formats import (
    get_reader_by_test
)


def get_product_type_name(stac_item):
    """ Create a ProductType name from a STAC Items metadata
    """

    properties = stac_item['properties']
    assets = stac_item['assets']

    parts = []

    platform = properties.get('platform') or properties.get('eo:platform')
    instruments = properties.get('instruments') or \
        properties.get('eo:instruments')
    constellation = properties.get('constellation') or \
        properties.get('eo:constellation')
    mission = properties.get('mission') or properties.get('eo:mission')

    if platform:
        parts.append(platform)

    if instruments:
        parts.extend(instruments)

    if constellation:
        parts.append(constellation)

    if mission:
        parts.append(mission)

    bands = properties.get('eo:bands')
    if not bands:
        bands = []
        for asset in assets.values():
            bands.extend(asset.get('eo:bands'), [])

    parts.extend([band['name'] for band in bands])

    if not parts:
        raise RegistrationError(
            'Failed to generate Product type name from metadata'
        )

    return '_'.join(parts)


@transaction.atomic
def register_stac_product(location, stac_item, product_type=None, storage=None,
                          replace=False):
    """ Registers a single parsed STAC item as a Product. The
        product type to be used can be specified via the product_type_name
        argument.
    """

    identifier = stac_item['id']
    replaced = False

    if replace:
        if models.Product.objects.filter(identifier=identifier).exists():
            models.Product.objects.filter(identifier=identifier).delete()
            replaced = True

    geometry = stac_item['geometry']
    properties = stac_item['properties']
    assets = stac_item['assets']

    # fetch the product type by name, metadata or passed object
    if isinstance(product_type, models.ProductType):
        pass
    if isinstance(product_type, str):
        product_type = models.ProductType.objects.get(name=product_type)
    else:
        product_type = models.ProductType.objects.get(
            name=get_product_type_name(stac_item)
        )

    if isinstance(storage, str):
        storage = backends.Storage.objects.get(name=storage)

    footprint = GEOSGeometry(json.dumps(geometry))
    if 'start_datetime' in properties and 'end_datetime' in properties:
        start_time = parse_iso8601(properties['start_datetime'])
        end_time = parse_iso8601(properties['end_datetime'])
    else:
        start_time = end_time = parse_iso8601(properties['datetime'])

    # check if the product already exists
    if models.Product.objects.filter(identifier=identifier).exists():
        if replace:
            models.Product.objects.filter(identifier=identifier).delete()
        else:
            raise RegistrationError('Product %s already exists' % identifier)

    product = models.Product.objects.create(
        identifier=identifier,
        begin_time=start_time,
        end_time=end_time,
        footprint=footprint,
        product_type=product_type,
    )

    metadata = {}
    simple_mappings = {
        'eo:cloud_cover': 'cloud_cover',
        'sar:instrument_mode': 'sensor_mode',
        'sat:relative_orbit': 'orbit_number',
        'view:incidence_angle': [
            'minimum_incidence_angle', 'maximum_incidence_angle'
        ],
        'view:sun_azimuth': 'illumination_azimuth_angle',
        'view:sun_elevation': 'illumination_elevation_angle',

    }

    for stac_key, field_name in simple_mappings.items():
        value = properties.get(stac_key)
        if value:
            if isinstance(field_name, str):
                metadata[field_name] = value
            else:
                for name in field_name:
                    metadata[name] = value

    # 'sar:frequency_band'
    # 'sar:center_frequency'
    # doppler_frequency ?
    # 'sar:product_type' #
    # 'sar:resolution_range'
    # 'sar:resolution_azimuth'
    # 'sar:pixel_spacing_range'
    # 'sar:pixel_spacing_azimuth'
    # 'sar:looks_range'
    # 'sar:looks_azimuth'
    # 'sar:looks_equivalent_number'
    # 'view:azimuth'

    complex_mappings = {
        'sar:polarizations': (
            'polarization_channels', lambda v: ', '.join(v)
        ),
        'sar:observation_direction': (
            'antenna_look_direction', lambda v: v.upper()
        ),
        'sat:orbit_state': (
            'orbit_direction', lambda v: v.upper()
        ),
    }

    for stac_key, field_desc in complex_mappings.items():
        raw_value = properties.get(stac_key)
        if raw_value:
            field_name, prep = field_desc
            value = prep(raw_value)
            if isinstance(field_name, str):
                metadata[field_name] = value
            else:
                for name in field_name:
                    metadata[name] = value

    # actually create the metadata object
    create_metadata(product, metadata)

    registrator = GDALRegistrator()

    for asset_name, asset in assets.items():
        overrides = {}
        bands = asset.get('eo:bands')
        if not bands:
            continue

        if not isinstance(bands, list):
            bands = [bands]

        band_names = [band['name'] for band in bands]
        coverage_type = models.CoverageType.objects.get(
            Q(allowed_product_types=product_type),
            *[
                Q(field_types__identifier=band_name)
                for band_name in band_names
            ]
        )
        overrides['identifier'] = '%s_%s' % (identifier, asset_name)

        # create the storage item
        parsed = urlparse(asset['href'])

        if not isabs(parsed.path):
            path = normpath(join(dirname(location), parsed.path))
        else:
            path = parsed.path

        # arraydata_item = models.ArrayDataItem(
        #     location=path,
        #     storage=storage,
        #     band_count=len(bands),
        # )

        coverage_footprint = footprint
        if 'proj:geometry' in asset:
            coverage_footprint = GEOSGeometry(
                json.dumps(asset['proj:geometry'])
            )

        overrides['footprint'] = coverage_footprint.wkt

        shape = asset.get('proj:shape') or properties.get('proj:shape')
        transform = asset.get('proj:transform') or \
            properties.get('proj:transform')
        epsg = asset.get('proj:epsg') or properties.get('proj:epsg')

        if shape:
            overrides['size'] = shape

        if transform:
            overrides['origin'] = [transform[transform[0], transform[3]]]

        if epsg and transform:
            sr = osr.SpatialReference(epsg)
            axis_names = ['x', 'y'] if sr.IsProjected() else ['long', 'lat']
            grid_def = {
                'coordinate_reference_system': epsg,
                'axis_names': axis_names,
                'axis_types': ['spatial', 'spatial'],
                'axis_offsets': [transform[1], transform[5]],
            }
            overrides['grid'] = grid_def  # get_grid(grid_def)

        # if not grid_def or not size or not origin:
        #     ds = gdal_open(arraydata_item)
        #     reader = get_reader_by_test(ds)
        #     if not reader:
        #         raise RegistrationError(
        #             'Failed to get metadata reader for coverage'
        #         )
        #     values = reader.read(ds)
        #     grid_def = values['grid']
        #     size = values['size']
        #     origin = values['origin']

        registrator.register(
            data_locations=[([storage.name] if storage else []) + [path]],
            metadata_locations=[],
            coverage_type_name=coverage_type.name,
            footprint_from_extent=False,
            overrides=overrides,
            replace=replace,
        )

        # grid = get_grid(grid_def)

        # if models.Coverage.objects.filter(identifier=coverage_id).exists():
        #     if replace:
        #         models.Coverage.objects.filter(identifier=coverage_id).delete()
        #     else:
        #         raise RegistrationError(
        #             'Coverage %s already exists' % coverage_id
        #         )

        # coverage = models.Coverage.objects.create(
        #     identifier=coverage_id,
        #     footprint=coverage_footprint,
        #     begin_time=start_time,
        #     end_time=end_time,
        #     grid=grid,
        #     axis_1_origin=origin[0],
        #     axis_2_origin=origin[1],
        #     axis_1_size=size[0],
        #     axis_2_size=size[1],
        #     coverage_type=coverage_type,
        #     parent_product=product,
        # )

        # arraydata_item.coverage = coverage
        # arraydata_item.full_clean()
        # arraydata_item.save()

    # TODO: browses if possible

    return (product, replaced)


@transaction.atomic
def create_product_type_from_stac_collection(stac_collection,
                                             product_type_name=None):
    """
    """
    pass


@transaction.atomic
def create_product_type_from_stac_item(stac_item, product_type_name=None,
                                       ignore_existing=False):
    """ Creates a ProductType from a parsed STAC Item. Also creates all
        related CoverageTypes and their interned FieldTypes.

        Returns the ProductType and a boolean, indicating whether it was
        created or did already exist.
    """

    if product_type_name is None:
        product_type_name = get_product_type_name(stac_item)

    existing = models.ProductType.objects.filter(
        name=product_type_name
    ).first()
    if existing and ignore_existing:
        return (existing, False)
    elif existing:
        raise RegistrationError(
            'Product type %s already exists' % product_type_name
        )

    properties = stac_item['properties']
    assets = stac_item['assets']

    # list of Asset ID + bands
    bands_list = []

    for asset_name, asset in assets.items():
        if 'eo:bands' in asset:
            bands_list.append(
                (
                    asset_name,
                    asset['eo:bands']
                    if isinstance(asset['eo:bands'], list) else
                    [asset['eo:bands']]
                )
            )

    if not bands_list and 'eo:bands' in properties:
        bands_list.extend(
            (band['name'], [band])
            for band in properties['eo:bands']
        )

    if not bands_list:
        raise RegistrationError(
            'Failed to extract band defintion from STAC Item'
        )

    # create product type itself
    product_type = models.ProductType.objects.create(name=product_type_name)

    # iterate over bands and create coverage types
    for name, bands in bands_list:
        coverage_type = models.CoverageType.objects.create(
            name='%s_%s' % (product_type_name, name)
        )
        product_type.allowed_coverage_types.add(coverage_type)

        for i, band in enumerate(bands):
            models.FieldType.objects.create(
                coverage_type=coverage_type,
                index=i,
                identifier=band['name'],
                definition=band.get('common_name'),
            )

    browse_defs = properties.get('brow:browses', {})
    for browse_name, browse in browse_defs.items():
        browse_bands = browse.get('bands')
        range_ = browse.get('range')
        expression = browse.get('expression')
        browse_def = {'name': browse_name}
        if browse_bands:
            if len(browse_bands) not in (1, 3, 4):
                raise RegistrationError(
                    'Failed to create browse type: wrong number of bands'
                )
            browse_def['red_or_grey_expression'] = browse_bands[0]
            browse_def['red_or_grey_range_min'] = range_[0]
            browse_def['red_or_grey_range_max'] = range_[1]
            if len(browse_bands) >= 3:
                browse_def['green_expression'] = browse_bands[1]
                browse_def['green_range_min'] = range_[0]
                browse_def['green_range_max'] = range_[1]
                browse_def['blue_expression'] = browse_bands[2]
                browse_def['blue_range_min'] = range_[0]
                browse_def['blue_range_max'] = range_[1]
            if len(browse_bands) == 3:
                browse_def['alpha_expression'] = browse_bands[3]
                browse_def['alpha_range_min'] = range_[0]
                browse_def['alpha_range_max'] = range_[1]

        elif expression:
            browse_def['red_or_grey_expression'] = expression

        models.BrowseType.objects.create(
            product_type=product_type,
            **browse_def,
        )

    return (product_type, True)
