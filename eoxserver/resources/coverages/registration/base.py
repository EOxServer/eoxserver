#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
#-------------------------------------------------------------------------------

from itertools import chain

from django.db.models import ForeignKey

from eoxserver.core import Component, implements, env
from eoxserver.contrib import osr
from eoxserver.backends import models as backends
from eoxserver.backends.access import retrieve
from eoxserver.backends.component import BackendComponent
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.metadata.component import MetadataComponent
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)
from eoxserver.resources.coverages.registration.interfaces import (
    RegistratorInterface
)


class BaseRegistrator(Component):
    """ Abstract base component to be used by specialized registrators.
    """

    implements(RegistratorInterface)

    abstract = True

    metadata_keys = frozenset((
        "identifier", "extent", "size", "projection",
        "footprint", "begin_time", "end_time", "coverage_type",
        "range_type_name"
    ))

    def register(self, data_locations, data_semantics, metadata_locations,
                 overrides=None, replace=False, cache=None):
        """ Main registration method

            :param data_locations:
            :param data_semantics: Either a list of strings (one for each data
                                   location in ``data_locations``) or ``None``,
                                   in which case the semantics will be filled
                                   by best guess.
            :param metadata_locations:
            :param overrides:
        """
        replaced = False
        retrieved_metadata = overrides or {}

        # create DataItems for each item that is metadata
        metadata_items = [
            self._descriptor_to_data_item(location, 'metadata')
            for location in metadata_locations
        ]

        # read metadata until we are satisfied or run out of metadata items
        for metadata_item in metadata_items:
            if not self.missing_metadata_keys(retrieved_metadata):
                break
            self._read_metadata(metadata_item, retrieved_metadata, cache)

        range_type_name = retrieved_metadata.get('range_type_name')
        if not range_type_name:
            raise RegistrationError('Could not determine range type name')
        range_type = models.RangeType.objects.get(name=range_type_name)

        # check if data semantics were passed, otherwise create our own.
        if data_semantics is None:
            # TODO: check corner cases.
            # e.g: only one data item given but multiple bands in range type
            # --> bands[1:<bandnum>]
            if len(data_locations) == 1:
                if len(range_type) == 1:
                    data_semantics = ["bands[1]"]
                else:
                    data_semantics = ["bands[1:%d]" % len(range_type)]

            else:
                data_semantics = ["bands[%d]" % i for i in range(
                    len(data_locations)
                )]

        # create DataItems for each item that is not metadata
        data_items = [
            self._descriptor_to_data_item(location, semantic)
            for location, semantic in zip(data_locations, data_semantics)
        ]
        # if there is still some metadata missing, read it from the data
        for data_item in data_items:
            if not self.missing_metadata_keys(retrieved_metadata):
                break
            self._read_metadata_from_data(data_item, retrieved_metadata, cache)

        if self.missing_metadata_keys(retrieved_metadata):
            raise RegistrationError(
                "Missing metadata keys %s."
                % ", ".join(self.missing_metadata_keys(retrieved_metadata))
            )

        collections = []
        if replace:
            try:
                # get a list of all collections the coverage was in.
                coverage = models.Coverage.objects.get(
                    identifier=retrieved_metadata["identifier"]
                )
                collections = list(models.Collection.objects.filter(
                    eo_objects__in=[coverage.pk]
                ))

                coverage.delete()
                replaced = True

            except models.Coverage.DoesNotExist:
                pass

        product_metadata = retrieved_metadata.pop('product_metadata', None)
        metadata = retrieved_metadata.pop('metadata', None)
        metadata_type = retrieved_metadata.pop('metadata_type', None)

        dataset = self._create_dataset(
            data_items=chain(metadata_items, data_items), **retrieved_metadata
        )

        self._create_metadata(dataset, product_metadata, metadata, metadata_type)

        # when we replaced the dataset, re-insert the newly created dataset to
        # the collections
        for collection in collections:
            collection.insert(dataset)

        return dataset, replaced

    def _read_metadata(self, data_item, retrieved_metadata, cache):
        """ Read all available metadata of a ``data_item`` into the
        ``retrieved_metadata`` :class:`dict`.
        """
        metadata_component = MetadataComponent(env)

        with open(retrieve(data_item, cache)) as f:
            content = f.read()
            reader = metadata_component.get_reader_by_test(content)
            if reader:
                values = reader.read(content)

                format = values.pop("format", None)
                if format:
                    data_item.format = format
                    data_item.full_clean()
                    data_item.save()

                for key, value in values.items():
                    # if key in self.metadata_keys:
                    retrieved_metadata.setdefault(key, value)

    def _read_metadata_from_data(self, data_item, retrieved_metadata, cache):
        "Interface method to be overridden in subclasses"
        raise NotImplementedError

    def _create_dataset(self, identifier, extent, size, projection,
                        footprint, begin_time, end_time, coverage_type,
                        range_type_name, data_items, visible=False,
                        product=None):

        CoverageType = getattr(models, coverage_type)

        coverage = CoverageType()
        coverage.range_type = models.RangeType.objects.get(name=range_type_name)

        if isinstance(projection, int):
            coverage.srid = projection
        else:
            definition, format = projection

            # Try to identify the SRID from the given input
            try:
                sr = osr.SpatialReference(definition, format)
                coverage.srid = sr.srid
            except:
                prj = models.Projection.objects.get(
                    format=format, definition=definition
                )
                coverage.projection = prj

        print footprint

        coverage.identifier = identifier
        coverage.extent = extent
        coverage.size = size
        coverage.footprint = footprint
        coverage.begin_time = begin_time
        coverage.end_time = end_time

        coverage.product = product

        coverage.visible = visible

        coverage.full_clean()
        coverage.save()

        # attach all data items
        for data_item in data_items:
            data_item.dataset = coverage
            data_item.full_clean()
            data_item.save()

        return coverage

    def _create_metadata(self, dataset, product_metadata_values,
                         metadata_values, metadata_type):

        if product_metadata_values:
            product_metadata_values = dict(
                (name, convert(name, value, models.Product))
                for name, value in product_metadata_values.items()
                if value is not None
            )
            models.Product.objects.create(
                coverage=dataset, **product_metadata_values
            )

        if metadata_values:
            metadata_class = models.CoverageMetadata
            if metadata_type == "SAR":
                metadata_class = models.SARMetadata
            elif metadata_type == "OPT":
                metadata_class = models.OPTMetadata
            elif metadata_type == "ALT":
                metadata_class = models.ALTMetadata

            metadata_values = dict(
                (name, convert(name, value, metadata_class))
                for name, value in metadata_values.items()
                if value is not None
            )
            metadata_class.objects.create(coverage=dataset, **metadata_values)

    def missing_metadata_keys(self, retrieved_metadata):
        """ Return a :class:`frozenset` of metadata keys still missing.
        """
        return self.metadata_keys - frozenset(retrieved_metadata.keys())

    def _descriptor_to_data_item(self, path_items, semantic):
        storage, package, frmt, location = self._get_location_chain(path_items)
        data_item = backends.DataItem(
            location=location, format=frmt or "", semantic=semantic,
            storage=storage, package=package,
        )
        data_item.full_clean()
        data_item.save()
        return data_item

    def _create_data_item(self, storage_or_package, location, semantic, format):
        """ Small helper function to create a :class:`DataItem
        <eoxserver.backends.models.DataItem>` from the available inputs.
        """
        storage = None
        package = None
        if isinstance(storage_or_package, backends.Storage):
            storage = storage_or_package
        elif isinstance(storage_or_package, backends.Package):
            package = storage_or_package

        data_item = backends.DataItem(
            storage=storage, package=package, location=location,
            semantic=semantic, format=format
        )
        data_item.full_clean()
        data_item.save()
        return data_item

    def _get_location_chain(self, path_items):
        """ Returns the tuple
        """
        component = BackendComponent(env)
        storage = None
        package = None

        storage_type, url = self._split_location(path_items[0])
        if storage_type:
            storage_component = component.get_storage_component(storage_type)
        else:
            storage_component = None

        if storage_component:
            storage, _ = backends.Storage.objects.get_or_create(
                url=url, storage_type=storage_type
            )

        # packages
        for item in path_items[1 if storage else 0:-1]:
            type_or_format, location = self._split_location(item)
            package_component = component.get_package_component(type_or_format)
            if package_component:
                package, _ = backends.Package.objects.get_or_create(
                    location=location, format=format,
                    storage=storage, package=package
                )
                storage = None  # override here
            else:
                raise Exception(
                    "Could not find package component for format '%s'"
                    % type_or_format
                )

        format, location = self._split_location(path_items[-1])
        return storage, package, format, location

    def _split_location(self, item):
        """ Splits string as follows: <format>:<location> where format can be
            None.
        """
        p = item.find(":")
        if p == -1:
            return None, item
        return item[:p], item[p + 1:]


def is_common_value(field):
    try:
        if isinstance(field, ForeignKey):
            field.related.parent_model._meta.get_field('value')
            return True
    except:
        pass
    return False


def convert(name, value, model_class):
    field = model_class._meta.get_field(name)
    if is_common_value(field):
        return field.related.parent_model.objects.get_or_create(
            value=value
        )[0]
    elif field.choices:
        return dict((v, k) for k, v in field.choices)[value]
    return value
