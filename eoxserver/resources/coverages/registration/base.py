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

from eoxserver.core import Component, implements, env
from eoxserver.contrib import osr
from eoxserver.backends import models as backends
from eoxserver.backends.access import retrieve
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

    def register(self, items, overrides=None, cache=None):
        retrieved_metadata = overrides or {}

        # create DataItems for each item that is metadata
        metadata_items = [
            self._create_data_item(*i) for i in items if i[2] == "metadata"
        ]

        # read metadata until we are satisfied or run out of metadata items
        for metadata_item in metadata_items:
            if not self.missing_metadata_keys(retrieved_metadata):
                break
            self._read_metadata(metadata_item, retrieved_metadata, cache)

        # create DataItems for each item that is not metadata
        data_items = [
            self._create_data_item(*i) for i in items if i[2] != "metadata"
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

        return self._create_dataset(
            data_items=chain(metadata_items, data_items),
            **retrieved_metadata
        )

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
                    if key in self.metadata_keys:
                        retrieved_metadata.setdefault(key, value)

    def _read_metadata_from_data(self, data_item, retrieved_metadata, cache):
        "Interface method to be overridden in subclasses"
        raise NotImplementedError

    def _create_dataset(self, identifier, extent, size, projection,
                        footprint, begin_time, end_time, coverage_type,
                        range_type_name, data_items):

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

        coverage.identifier = identifier
        coverage.extent = extent
        coverage.size = size
        coverage.footprint = footprint
        coverage.begin_time = begin_time
        coverage.end_time = end_time

#        coverage.visible = kwargs["visible"]

        coverage.full_clean()
        coverage.save()

        # attach all data items
        for data_item in data_items:
            data_item.dataset = coverage
            data_item.full_clean()
            data_item.save()

        return coverage

    def missing_metadata_keys(self, retrieved_metadata):
        """ Return a :class:`frozenset` of metadata keys still missing.
        """
        return self.metadata_keys - frozenset(retrieved_metadata.keys())
