import json
from django.contrib.gis.geos import GEOSGeometry
from django.db.models import Q

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.backends import models as backends
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)
from eoxserver.resources.coverages.registration.product import create_metadata


def register_stac_product(stac_item, product_type_name=None, storage=None,
                          replace=False):
    """ Registers a single parsed STAC item as a Product. The
        product type to be used can be specified via the product_type_name
        argument.
    """

    identifier = stac_item['id']
    geometry = stac_item['geometry']
    properties = stac_item['properties']
    assets = stac_item['assets']

    if product_type_name:
        product_type = models.ProductType.objects.get(name=product_type_name)
    else:
        # TODO: figure out product type
        product_type = None

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

    for asset_name, asset in assets.items():
        bands = assets.get('eo:bands')
        if bands:
            band_names = [band['name'] for band in bands]
            coverage_type = models.CoverageType.objects.get(*[
                Q(field_type__name=band_name)
                for band_name in band_names
            ])

        models.Coverage.objects.create(
            coverage_type=coverage_type,
            product=product,
        )


def create_product_type_from_stac_collection(stac_collection,
                                             product_type_name=None):
    """
    """
    pass


def create_product_type_from_stac_item(stac_item, product_type_name=None):
    pass
