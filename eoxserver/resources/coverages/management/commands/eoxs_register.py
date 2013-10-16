#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from optparse import make_option
from itertools import chain

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, BaseCommand
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core import env
from eoxserver.contrib import gdal, osr
from eoxserver.backends import models as backends
from eoxserver.backends.component import BackendComponent
from eoxserver.backends.cache import CacheContext
from eoxserver.backends.access import connect
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.metadata.component import MetadataComponent
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb
)


def _variable_args_cb(option, opt_str, value, parser):
    """ Helper function for optparse module. Allows
        variable number of option values when used
        as a callback.
    """
    args = []
    for arg in parser.rargs:
        if not arg.startswith('-'):
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if getattr(parser.values, option.dest):
        args.extend(getattr(parser.values, option.dest))
    setattr(parser.values, option.dest, args)
    

def _variable_args_cb_list(option, opt_str, value, parser):
    """ Helper function for optparse module. Allows variable number of option 
        values when used as a callback.
    """
    args = []
    for arg in parser.rargs:
        if not arg.startswith('-'):
            args.append(arg)
        else:
            del parser.rargs[:len(args)]
            break
    if not getattr(parser.values, option.dest):
        setattr(parser.values, option.dest, [])

    getattr(parser.values, option.dest).append(args)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier", "--coverage-id", dest="identifier",
            action="store", default=None,
            help=("Override identifier")
        ),
        make_option("-d", "--data", dest="data",
            action="callback", callback=_variable_args_cb_list, default=[],
            help=("[storage_type:url] [package_type:location]* format:location")
        ),
        make_option("-s", "--semantic", dest="semantics",
            action="callback", callback=_variable_args_cb, default=None,
            help=("Optional. If given, one semantic must be present for each "
                 "'--data' option.")
        ),
        make_option("-m", "--meta-data", dest="metadata", 
            action="callback", callback=_variable_args_cb_list, default=[],
            help=("Optional. [storage_type:url] [package_type:location]* format:location")
        ),
        make_option("-r", "--range-type", dest="range_type_name",
            help=("Mandatory. Name of the stored range type. ")
        ),

        make_option("-e", "--extent", dest="extent", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Override extent.")
        ),

        make_option("--size", dest="size", 
            action="callback", callback=_variable_args_cb,
            help=("Override size.")
        ),

        make_option("-p", "--projection", dest="projection", 
            action="store", default=None,
            help=("Override projection.")
        ),

        make_option("-f", "--footprint", dest="footprint", 
            action="store", default=None,
            help=("Override footprint.")
        ),

        make_option("--begin-time", dest="begin_time", 
            action="store", default=None,
            help=("Override begin time.")
        ),

        make_option("--end-time", dest="end_time", 
            action="store", default=None,
            help=("Override end time.")
        ),

        make_option("--coverage-type", dest="coverage_type",
            action="store", default="RectifiedDataset",
            help=("The actual coverage type.")
        )
    )

    @transaction.commit_on_success
    def handle(self, *args, **kwargs):
        with CacheContext() as cache:
            self.handle_with_cache(cache, *args, **kwargs)


    def handle_with_cache(self, cache, *args, **kwargs):
        metadata_component = MetadataComponent(env)
        datas = kwargs["data"]
        semantics = kwargs.get("semantics")
        metadatas = kwargs["metadata"]
        range_type_name = kwargs["range_type_name"]

        if range_type_name is None:
            raise CommandError("No range type name specified.")
        range_type = models.RangeType.objects.get(name=range_type_name)

        # TODO: not required, as the keys are already
        metadata_keys = set((
            "identifier", "extent", "size", "projection", 
            "footprint", "begin_time", "end_time"
        ))

        all_data_items = []
        retrieved_metadata = {}

        retrieved_metadata.update(
            self._get_overrides(**kwargs)
        )

        for metadata in metadatas:
            storage, package, format, location = self._get_location_chain(metadata)
            data_item = backends.DataItem(
                location=location, format=format or "", semantic="metadata", 
                storage=storage, package=package,
            )
            data_item.full_clean()
            data_item.save()
            all_data_items.append(data_item)

            with open(connect(data_item, cache)) as f:
                content = f.read()
                reader = metadata_component.get_reader_by_test(content)
                if reader:
                    values = reader.read(content)
                    for key, value in values.items():
                        if key in metadata_keys:
                            retrieved_metadata.setdefault(key, value)

                        # TODO: think this over. semantic would be required


        if len(datas) < 1:
            raise CommandError("No data files specified.")

        if semantics is None:
            # TODO: check corner cases.
            # e.g: only one data item given but multiple bands in range type
            # --> bands[1:<bandnum>]
            if len(datas) == 1:
                if len(range_type) == 1:
                    semantics = ["bands[1]"]
                else:
                    semantics = ["bands[1:%d]" % len(range_type)]
            
            else:
                semantics = ["bands[%d]" % i for i in range(len(datas))]


        for data, semantic in zip(datas, semantics):
            storage, package, format, location = self._get_location_chain(data)
            data_item = backends.DataItem(
                location=location, format=format or "", semantic=semantic, 
                storage=storage, package=package,
            )
            data_item.full_clean()
            data_item.save()
            all_data_items.append(data_item)

            # TODO: other opening methods than GDAL
            ds = gdal.Open(connect(data_item, cache))
            reader = metadata_component.get_reader_by_test(ds)
            if reader:
                values = reader.read(ds)
                for key, value in values.items():
                    if key in metadata_keys:
                        retrieved_metadata.setdefault(key, value)
            ds = None

        if len(metadata_keys - set(retrieved_metadata.keys())):
            raise CommandError(
                "Missing metadata keys %s." 
                % ", ".join(metadata_keys - set(retrieved_metadata.keys()))
            )

        try:
            CoverageType = getattr(models, kwargs["coverage_type"])
        except:
            pass
            # TODO: split into module path/coverage and get correct coverage class

        try:
            coverage = CoverageType()
            coverage.range_type = range_type
            
            proj = retrieved_metadata.pop("projection")
            if isinstance(proj, int):
                retrieved_metadata["srid"] = proj
            else:
                definition, format = proj

                # Try to identify the SRID from the given input
                try:
                    sr = osr.SpatialReference(definition, format)
                    retrieved_metadata["srid"] = sr.srid
                except Exception, e:
                    retrieved_metadata["projection"] = models.Projection.objects.get(format=format, definition=definition)

            #coverage.identifier = identifier # TODO: bug in models for some coverages
            for key, value in retrieved_metadata.items():
                print key
                setattr(coverage, key, value)

            coverage.full_clean()
            coverage.save()

            for data_item in all_data_items:
                data_item.dataset = coverage
                data_item.full_clean()
                data_item.save()

        except ValidationError, e:
            # TODO: show error message
            raise CommandError(str(e))

        print "Successfully registered one dataset."

        
    def _get_overrides(self, identifier=None, size=None, extent=None, 
                       begin_time=None, end_time=None, footprint=None, **kwargs):

        overrides = {}

        if identifier:
            overrides["identifier"] = identifier

        if extent:
            overrides["extent"] = map(float, extent.split(","))

        if size:
            overrides["size"] = map(int, size.split(","))            

        if begin_time:
            overrides["begin_time"] = parse_datetime(begin_time)

        if end_time:
            overrides["end_time"] = parse_datetime(end_time)

        if footprint:
            overrides["footprint"] = GEOSGeometry(footprint)

        return overrides


    def _get_location_chain(self, items):
        """ Returns the tuple
        """
        component = BackendComponent(env)
        storage = None
        package = None

        storage_type, url = self._split_location(items[0])
        if storage_type:
            storage_component = component.get_storage_component(storage_type)
        else:
            storage_component = None

        if storage_component:
            storage, _ = backends.Storage.objects.get_or_create(
                url=url, storage_type=storage_type
            )


        # packages
        for item in items[1 if storage else 0:-1]:
            package_component = component.get_package_component(type_or_format)
            format, location = self._split_location(item)
            if package_component:
                package, _ = backends.Package.objects.get_or_create(
                    location=location, format=format, 
                    storage=storage, package=package
                )
                storage = None # override here
            else:
                raise "Could not find package component"

        format, location = self._split_location(items[-1])
        return storage, package, format, location


    def _split_location(self, item):
        """ Splits string as follows: <format>:<location> where format can be 
            None.
        """
        p = item.find(":")
        if p == -1:
            return None, item 
        return item[:p], item[p + 1:]


def save(model):
    model.full_clean()
    model.save()
    return model
