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


from django.contrib.gis.geos import GEOSGeometry

from eoxserver.contrib import gdal
from eoxserver.backends import models as backends
from eoxserver.backends.access import retrieve, get_vsi_path
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.registration import base
from eoxserver.resources.coverages.metadata.component import (
    ProductMetadataComponent
)
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)


class ProductRegistrator(base.BaseRegistrator):
    def register(self, file_handles, mask_handles, package_path,
                 overrides, type_name=None, extended_metadata=True,
                 discover_masks=True, discover_browses=True, replace=False):
        product_type = None
        if type_name:
            product_type = models.ProductType.objects.get(name=type_name)

        component = ProductMetadataComponent()

        browse_handles = []
        mask_handles = []
        metadata = {}

        package = None
        if package_path:
            # TODO: identify type of package
            from eoxserver.backends.storages import get_handler_by_test
            handler = get_handler_by_test(package_path)
            if not handler:
                raise RegistrationError(
                    'Storage %r is not supported' % package_path
                )

            package, _ = backends.Storage.objects.get_or_create(
                url=package_path, storage_type=handler.name
            )
            metadata.update(component.collect_package_metadata(package))
            if discover_browses:
                browse_handles.extend([
                    (browse_type, package_path, browse_path)
                    for browse_type, browse_path in metadata.pop('browses', [])
                ])
            if discover_masks:
                mask_handles.extend([
                    (mask_type, package_path, mask_path)
                    for mask_type, mask_path in metadata.pop('mask_files', [])
                ])

                mask_handles.extend([
                    (mask_type, geometry)
                    for mask_type, geometry in metadata.pop('masks', [])
                ])

        data_items = []
        for file_handle in file_handles:
            data_items.append(retrieve(*file_handle))

        new_metadata = component.collect_metadata(data_items)
        new_metadata.update(metadata)

        md_identifier = new_metadata.pop('identifier', None)
        md_footprint = new_metadata.pop('footprint', None)
        md_begin_time = new_metadata.pop('begin_time', None)
        md_end_time = new_metadata.pop('end_time', None)
        mask_handles.extend(new_metadata.pop('masks', []))

        # apply overrides
        identifier = overrides.get('identifier') or md_identifier
        footprint = overrides.get('footprint') or md_footprint
        begin_time = overrides.get('begin_time') or md_begin_time
        end_time = overrides.get('end_time') or md_end_time

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
            models.ProductMetadata.objects.create(
                product=product,
                # **metadata
            )

        # register all masks
        for mask_handle in mask_handles:
            geometry = None
            storage = None
            location = ''
            try:
                geometry = GEOSGeometry(mask_handle[1])
            except:
                storage = self.resolve_storage(mask_handle[1:-1])
                location = mask_handle[-1]

            models.Mask.objects.create(
                product=product,
                mask_type=models.MaskType.objects.get(name=mask_handle[0]),
                storage=storage,
                location=location,
                geometry=geometry
            )

        # register all browses
        for browse_handle in browse_handles:
            browse_type = None
            if browse_handle[0]:
                print browse_handle[0]
                browse_type = models.BrowseType.objects.get(
                    name=browse_handle[0]
                )

            browse = models.Browse(
                product=product,
                location=browse_handle[-1],
                storage=self.resolve_storage(browse_handle[1:-1])
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

        return product, replaced
