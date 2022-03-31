# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
from django.contrib.gis.geos import Polygon
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.utils.six import string_types

from eoxserver.backends.access import vsi_open
from eoxserver.backends.util import resolve_storage
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.metadata.coverage_formats import (
    get_reader_by_test
)
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)


class RegistrationReport(object):
    def __init__(self, coverage, replaced, metadata_parsers,
                 retrieved_metadata):
        self.coverage = coverage
        self.replaced = replaced
        self.metadata_parsers = metadata_parsers
        self.retrieved_metadata = retrieved_metadata


class BaseRegistrator(object):
    """ Abstract base component to be used by specialized registrators.
    """

    abstract = True

    metadata_keys = frozenset((
        "identifier",
        # "footprint", "begin_time", "end_time",
        "size", "origin", "grid"
    ))

    def register(self, data_locations, metadata_locations,
                 coverage_type_name=None, footprint_from_extent=False,
                 overrides=None, identifier_template=None,
                 highest_resolution=False, replace=False, cache=None,
                 use_subdatasets=False, simplify_footprint_tolerance=None,
                 statistics=None):
        """ Main registration method

            :param data_locations:
            :param data_semantics: Either a list of strings (one for each data
                                   location in ``data_locations``) or ``None``,
                                   in which case the semantics will be filled
                                   by best guess.
            :param metadata_locations:
            :param overrides:
            :returns: A registration report
            :rtype: `RegistrationReport`
        """
        replaced = False
        retrieved_metadata = overrides or {}

        # fetch the coverage type if a type name was specified
        coverage_type = None
        if coverage_type_name:
            try:
                coverage_type = models.CoverageType.objects.get(
                    name=coverage_type_name
                )
            except models.CoverageType.DoesNotExist:
                raise RegistrationError(
                    'No such coverage type %r' % coverage_type_name
                )

        # create MetaDataItems for each item that is metadata
        metadata_items = [
            models.MetaDataItem(
                location=location[-1],
                storage=resolve_storage(location[:-1])
            )
            for location in metadata_locations
        ]

        # prepare ArrayDataItems for each given location
        arraydata_items = []
        arraydata_item_statistics = []
        statistics = statistics or [None] * len(data_locations)
        if len(statistics) != len(data_locations):
            raise ValueError("Invalid number of statistics passed")

        for location, stats in zip(data_locations, statistics):
            # handle storages and/or subdataset specifiers
            path = location[-1]
            # parts = path.split(':')

            parts = [
                part.replace('\\:', ':')
                for part in re.split(r'(?<!\\):', path)
            ]

            subdataset_type = None
            subdataset_locator = None
            if use_subdatasets and len(parts) > 1:
                path = parts[1]
                subdataset_type = parts[0]
                subdataset_locator = ":".join(parts[2:])
            else:
                path = path.replace('\\:', ':')

            arraydata_items.append(
                models.ArrayDataItem(
                    location=path,
                    storage=resolve_storage(location[:-1]),
                    subdataset_type=subdataset_type,
                    subdataset_locator=subdataset_locator,
                )
            )

            band_stats = None
            if stats:
                band_stats = []
                for i, stat in enumerate(stats, start=1):
                    band_stats.append(
                        models.BandStatistics(
                            band_index=i,
                            mean=stat.get('mean'),
                            minimum=stat.get('minimum'),
                            maximum=stat.get('maximum'),
                            stddev=stat.get('stddev'),
                            valid_percent=stat.get('valid_percent'),
                            histogram=stat.get('histogram'),
                        )
                    )
            arraydata_item_statistics.append(band_stats)

        metadata_parsers = []

        # read metadata until we are satisfied or run out of metadata items
        for metadata_item in metadata_items:
            if not self.missing_metadata_keys(retrieved_metadata):
                break

            metadata_parsers.append(
                self._read_metadata(
                    metadata_item, retrieved_metadata, cache
                )
            )

        # check the coverage type for expected amount of fields
        if coverage_type:
            num_fields = coverage_type.field_types.count()
            if len(arraydata_items) != 1 \
                    and len(arraydata_items) != num_fields:
                raise RegistrationError(
                    'Invalid number of data files specified. Expected 1 or %d '
                    'got %d.'
                    % (num_fields, len(arraydata_items))
                )

            # TODO: lookup actual band counts

            if len(arraydata_items) == 1:
                arraydata_items[0].band_count = num_fields

            else:
                for i, arraydata_item in enumerate(arraydata_items):
                    arraydata_item.field_index = i
                    arraydata_item.band_count = 1

        elif len(arraydata_items) != 1:
            raise RegistrationError(
                'Invalid number of data files specified.'
            )

            # TODO find actual bands

        # if there is still some metadata missing, read it from the data
        for arraydata_item in arraydata_items:
            if not self.missing_metadata_keys(retrieved_metadata) and \
                    not highest_resolution:
                break
            metadata_parsers.append(
                self._read_metadata_from_data(
                    arraydata_item, retrieved_metadata, cache,
                    highest_resolution
                )
            )

        if self.missing_metadata_keys(retrieved_metadata):
            raise RegistrationError(
                "Missing metadata keys %s."
                % ", ".join(self.missing_metadata_keys(retrieved_metadata))
            )

        identifier = retrieved_metadata["identifier"]
        if identifier_template:
            identifier = identifier_template.format(**retrieved_metadata)
            retrieved_metadata["identifier"] = identifier

        collections = []
        product = None
        if replace:
            try:
                # get a list of all collections the coverage was in.
                coverage = models.Coverage.objects.get(
                    identifier=identifier
                )
                product = coverage.parent_product
                collections = list(models.Collection.objects.filter(
                    coverages=coverage.pk
                ))

                coverage.delete()
                replaced = True

            except models.Coverage.DoesNotExist:
                pass

        # calculate the footprint from the extent
        if footprint_from_extent:
            footprint = self._footprint_from_grid(
                retrieved_metadata['grid'], retrieved_metadata['origin'],
                retrieved_metadata['size']
            )
            retrieved_metadata['footprint'] = footprint

        if simplify_footprint_tolerance is not None and \
                retrieved_metadata.get('footprint'):
            footprint = retrieved_metadata.get('footprint')
            retrieved_metadata['footprint'] = footprint.simplify(
                simplify_footprint_tolerance, preserve_topology=True
            )

        coverage = self._create_coverage(
            identifier=identifier,
            footprint=retrieved_metadata.get('footprint'),
            begin_time=retrieved_metadata.get('begin_time'),
            end_time=retrieved_metadata.get('end_time'),

            size=retrieved_metadata['size'],
            origin=retrieved_metadata['origin'],
            grid=retrieved_metadata['grid'],
            coverage_type_name=coverage_type_name,

            arraydata_items=arraydata_items,
            metadata_items=metadata_items,
            arraydata_item_statistics=arraydata_item_statistics,
        )

        # when we replaced the coverage, re-insert the newly created coverage
        # to the collections and/or product
        for collection in collections:
            models.collection_insert_eo_object(collection, coverage)

        if product:
            models.product_add_coverage(product, coverage)

        return RegistrationReport(
            coverage, replaced, metadata_parsers, retrieved_metadata
        )

    def _read_metadata(self, metadata_item, retrieved_metadata, cache):
        """ Read all available metadata of a ``data_item`` into the
        ``retrieved_metadata`` :class:`dict`.
        """

        with vsi_open(metadata_item) as f:
            content = f.read()
            reader = get_reader_by_test(content)
            if reader:
                values = reader.read(content)

                format_ = values.pop("format", None)
                if format_:
                    metadata_item.format = format_

                for key, value in values.items():
                    retrieved_metadata.setdefault(key, value)

                if values:
                    return reader, values
            return None

    def _read_metadata_from_data(self, data_item, retrieved_metadata, cache,
                                 highest_resolution):
        "Interface method to be overridden in subclasses"
        raise NotImplementedError

    def _footprint_from_grid(self, grid, origin, size):
        "Calculate the footprint from the grid"
        if grid['axis_types'][:2] != ['spatial', 'spatial']:
            raise RegistrationError("Cannot compute footprint from given grid")

        x1, y1 = origin[:2]
        dx, dy = grid['axis_offsets']
        sx, sy = size[:2]
        x2, y2 = (x1 + sx * dx, y1 + sy * dy)

        footprint = Polygon.from_bbox((
            min(x1, x2), min(y1, y2),
            max(x1, x2), max(y1, y2)
        ))

        footprint.transform(
            CoordTransform(
                SpatialReference(grid['coordinate_reference_system']),
                SpatialReference(4326)
            )
        )
        return footprint

    def _create_coverage(self, identifier, footprint, begin_time, end_time,
                         size, origin, grid, coverage_type_name,
                         arraydata_items, metadata_items,
                         arraydata_item_statistics):

        coverage_type = None
        if coverage_type_name:
            try:
                coverage_type = models.CoverageType.objects.get(
                    name=coverage_type_name
                )
            except models.CoverageType.DoesNotExist:
                raise RegistrationError(
                    'Coverage type %r does not exist' % coverage_type_name
                )

        grid = self._get_grid(grid)

        if len(size) < 4:
            size = list(size) + [None] * (4 - len(size))
        elif len(size) > 4:
            raise RegistrationError('Highest dimension number is 4.')

        if len(origin) < 4:
            origin = list(origin) + [None] * (4 - len(origin))
        elif len(origin) > 4:
            raise RegistrationError('Highest dimension number is 4.')

        (axis_1_size, axis_2_size, axis_3_size, axis_4_size) = size
        (axis_1_origin, axis_2_origin, axis_3_origin, axis_4_origin) = origin

        coverage = models.Coverage(
            identifier=identifier, footprint=footprint,
            begin_time=begin_time, end_time=end_time,
            coverage_type=coverage_type,
            grid=grid,
            axis_1_origin=axis_1_origin,
            axis_2_origin=axis_2_origin,
            axis_3_origin=axis_3_origin,
            axis_4_origin=axis_4_origin,
            axis_1_size=axis_1_size,
            axis_2_size=axis_2_size,
            axis_3_size=axis_3_size,
            axis_4_size=axis_4_size,
        )

        coverage.full_clean()
        coverage.save()

        # attach all data items
        for metadata_item in metadata_items:
            metadata_item.eo_object = coverage
            metadata_item.full_clean()
            metadata_item.save()

        for arraydata_item, band_statistics in \
                zip(arraydata_items, arraydata_item_statistics):
            arraydata_item.coverage = coverage
            arraydata_item.full_clean()
            arraydata_item.save()

            if band_statistics:
                for band_stats in band_statistics:
                    band_stats.arraydata_item = arraydata_item
                    band_stats.full_clean()
                    band_stats.save()

        return coverage

    def _create_metadata(self, coverage, metadata_values):
        metadata_values = dict(
            (name, convert(name, value, models.CoverageMetadata))
            for name, value in metadata_values.items()
            if value is not None
        )

        models.CoverageMetadata.objects.create(
            coverage=coverage, **metadata_values
        )

    def missing_metadata_keys(self, retrieved_metadata):
        """ Return a :class:`frozenset` of metadata keys still missing.
        """
        return self.metadata_keys - frozenset(retrieved_metadata.keys())

    def _get_grid(self, definition):
        return get_grid(definition)


def get_grid(definition):
    """ Get or create a grid according to our defintion
    """
    grid = None
    if isinstance(definition, string_types):
        try:
            grid = models.Grid.objects.get(name=definition)
        except models.Grid.DoesNotExist:
            raise RegistrationError(
                'Grid %r does not exist' % definition
            )
    elif definition:
        axis_names = definition.get('axis_names', [])
        axis_types = definition['axis_types']
        axis_offsets = definition['axis_offsets']

        # check lengths and destructure
        if len(axis_types) != len(axis_offsets):
            raise RegistrationError('Dimensionality mismatch')
        elif axis_names and len(axis_names) != len(axis_types):
            raise RegistrationError('Dimensionality mismatch')

        if len(axis_types) < 4:
            axis_types = list(axis_types) + [None] * (4 - len(axis_types))
        elif len(axis_types) > 4:
            raise RegistrationError('Highest dimension number is 4.')

        if len(axis_offsets) < 4:
            axis_offsets = (
                list(axis_offsets) + [None] * (4 - len(axis_offsets))
            )
        elif len(axis_offsets) > 4:
            raise RegistrationError('Highest dimension number is 4.')

        # translate axis type name to ID
        axis_type_names_to_id = {
            name: id_
            for id_, name in models.Grid.AXIS_TYPES
        }

        axis_types = [
            axis_type_names_to_id[axis_type] if axis_type else None
            for axis_type in axis_types
        ]

        for name, offset in zip(axis_names, axis_offsets):
            if offset == 0:
                raise RegistrationError(
                    'Invalid offset for axis %s: %s.' % (name, offset)
                )

        # unwrap axis types, offsets, names
        (type_1, type_2, type_3, type_4) = axis_types
        (offset_1, offset_2, offset_3, offset_4) = axis_offsets

        # TODO: use names like 'time', or 'x'/'y', etc
        axis_names = axis_names or [
            '%d' % i if i < len(axis_types) else None
            for i in range(len(axis_types))
        ]

        (name_1, name_2, name_3, name_4) = (
            axis_names + [None] * (4 - len(axis_names))
        )

        # try to find a suitable grid: with the given axis types,
        # offsets and coordinate reference system
        grid = models.Grid.objects.filter(
            coordinate_reference_system=definition[
                'coordinate_reference_system'
            ],
            axis_1_type=type_1,
            axis_2_type=type_2,
            axis_3_type=type_3,
            axis_4_type=type_4,
            axis_1_offset=offset_1,
            axis_2_offset=offset_2,
            axis_3_offset=offset_3,
            axis_4_offset=offset_4,
        ).first()
        if grid is None:
            # create a new grid from the given definition
            grid = models.Grid.objects.create(
                coordinate_reference_system=definition[
                    'coordinate_reference_system'
                ],
                axis_1_name=name_1,
                axis_2_name=name_2,
                axis_3_name=name_3,
                axis_4_name=name_4,
                axis_1_type=type_1,
                axis_2_type=type_2,
                axis_3_type=type_3,
                axis_4_type=type_4,
                axis_1_offset=offset_1,
                axis_2_offset=offset_2,
                axis_3_offset=offset_3,
                axis_4_offset=offset_4,
                resolution=definition.get('resolution')
            )
    return grid


def is_common_value(field):
    try:
        if isinstance(field, ForeignKey):
            field.related_model._meta.get_field('value')
            return True
    except Exception:
        pass
    return False


def convert(name, value, model_class):
    field = model_class._meta.get_field(name)
    if is_common_value(field):
        return field.related_model.objects.get_or_create(
            value=value
        )[0]
    elif field.choices:
        return dict((v, k) for k, v in field.choices)[value]
    return value
