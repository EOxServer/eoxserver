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

from django.db.models import ForeignKey
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.contrib import gdal
from eoxserver.backends import models as backends
from eoxserver.backends.storages import get_handler_by_test
from eoxserver.backends.access import get_vsi_path, get_vsi_env
from eoxserver.backends.util import resolve_storage
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration import base
from eoxserver.resources.coverages.metadata.component import (
    ProductMetadataComponent
)
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)


class ProductRegistrator(base.BaseRegistrator):
    def register(self, metadata_locations, mask_locations, package_path,
                 overrides, identifier_template=None, type_name=None,
                 extended_metadata=True, discover_masks=True,
                 discover_browses=True, discover_metadata=True, replace=False,
                 simplify_footprint_tolerance=None):
        product_type = None
        if type_name:
            product_type = models.ProductType.objects.get(name=type_name)

        component = ProductMetadataComponent()

        browse_handles = []
        mask_locations = mask_locations or []
        metadata = {}

        package = None
        if package_path:
            handler = get_handler_by_test(package_path)
            if not handler:
                raise RegistrationError(
                    'Storage %r is not supported' % package_path
                )

            package, _ = backends.Storage.objects.get_or_create(
                url=package_path, storage_type=handler.name
            )

            if discover_masks or discover_browses or discover_metadata:
                collected_metadata = component.collect_package_metadata(
                    package, handler
                )
                if discover_metadata:
                    metadata.update(collected_metadata)
                if discover_browses:
                    browse_handles.extend([
                        (browse_type, package_path, browse_path)
                        for browse_type, browse_path in metadata.pop(
                            'browses', []
                        )
                    ])
                if discover_masks:
                    mask_locations.extend([
                        (mask_type, package_path, mask_path)
                        for mask_type, mask_path in metadata.pop(
                            'mask_files', []
                        )
                    ])

                    mask_locations.extend([
                        (mask_type, geometry)
                        for mask_type, geometry in metadata.pop('masks', [])
                    ])

        metadata_items = [
            models.MetaDataItem(
                location=location[-1],
                storage=resolve_storage(location[:-1])
            )
            for location in metadata_locations
        ]

        new_metadata = {}
        for metadata_item in reversed(metadata_items):
            new_metadata.update(self._read_product_metadata(
                component, metadata_item
            ))

        mask_locations.extend(new_metadata.pop('masks', []))

        metadata.update(new_metadata)
        metadata.update(dict(
            (key, value) for key, value in overrides.items()
            if value is not None
        ))

        # apply overrides
        identifier = metadata.get('identifier')
        footprint = metadata.get('footprint')
        begin_time = metadata.get('begin_time')
        end_time = metadata.get('end_time')

        if identifier_template:
            identifier = identifier_template.format(metadata)
            metadata['identifier'] = identifier

        if simplify_footprint_tolerance is not None and footprint:
            footprint = footprint.simplify(
                simplify_footprint_tolerance, preserve_topology=True
            )

        replaced = False
        if replace:
            try:
                models.Product.objects.get(identifier=identifier).delete()
                replaced = True
            except models.Product.DoesNotExist:
                pass

        product = models.Product.objects.create(
            identifier=identifier,
            footprint=footprint,
            begin_time=begin_time,
            end_time=end_time,
            product_type=product_type,
            package=package,
        )

        if extended_metadata and metadata:
            create_metadata(product, metadata)

        # register all masks
        for mask_handle in mask_locations:
            geometry = None
            storage = None
            location = ''
            if isinstance(mask_handle[1], GEOSGeometry):
                geometry = GEOSGeometry(mask_handle[1])
            else:
                storage = resolve_storage(mask_handle[1:-1])
                location = mask_handle[-1]

            try:
                mask_type = models.MaskType.objects.get(
                    name=mask_handle[0], product_type=product_type
                )
            except models.MaskType.DoesNotExist:
                raise

            models.Mask.objects.create(
                product=product,
                mask_type=mask_type,
                storage=storage,
                location=location,
                geometry=geometry
            )

        # register all browses
        for browse_handle in browse_handles:
            browse_type = None
            if browse_handle[0]:
                # TODO: only browse types for that product type
                browse_type = models.BrowseType.objects.get(
                    name=browse_handle[0], product_type=product_type
                )

            browse = models.Browse(
                product=product,
                location=browse_handle[-1],
                storage=resolve_storage(browse_handle[1:-1])
            )

            # Get a VSI handle for the browse to get the size, extent and CRS
            # via GDAL
            vsi_path = get_vsi_path(browse)
            ds = gdal.Open(vsi_path)
            browse.width = ds.RasterXSize
            browse.height = ds.RasterYSize
            browse.coordinate_reference_system = ds.GetProjection()
            extent = gdal.get_extent(ds)
            browse.min_x, browse.min_y, browse.max_x, browse.max_y = extent

            browse.full_clean()
            browse.save()

        for metadata_item in metadata_items:
            metadata_item.eo_object = product
            metadata_item.full_clean()
            metadata_item.save()

        return product, replaced

    def _read_product_metadata(self, component, metadata_item):
        path = get_vsi_path(metadata_item)
        with gdal.config_env(get_vsi_env(metadata_item.storage)):
            return component.read_product_metadata_file(path)


def create_metadata(product, metadata_values):
    value_items = [
        (convert_name(name), value)
        for name, value in metadata_values.items()
        if value is not None
    ]

    metadata_values = dict(
        (name, convert_value(name, value, models.ProductMetadata))
        for name, value in value_items
        if value is not None and has_field(models.ProductMetadata, name)
    )

    models.ProductMetadata.objects.create(
        product=product, **metadata_values
    )


def is_common_value(field):
    try:
        if isinstance(field, ForeignKey):
            field.related_model._meta.get_field('value')
            return True
    except:
        pass
    return False


def has_field(model, field_name):
    try:
        model._meta.get_field(field_name)
        return True
    except:
        return False


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_name(name):
    namespace, _, sub_name = name.partition(':')
    if namespace in ('eop', 'opt', 'sar', 'alt'):
        return camel_to_underscore(sub_name)
    return camel_to_underscore(name)


def convert_value(name, value, model_class):
    field = model_class._meta.get_field(name)
    if is_common_value(field):
        return field.related_model.objects.get_or_create(
            value=value
        )[0]
    elif field.choices:
        return dict((v, k) for k, v in field.choices)[value]
    return value
