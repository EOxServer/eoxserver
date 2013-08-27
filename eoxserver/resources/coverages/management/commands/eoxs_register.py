from optparse import make_option
from itertools import chain

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.core import env
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
        make_option("-m", "--meta-data", dest="metadata", 
            action="callback", callback=_variable_args_cb_list, default=[],
            help=("[storage_type:url] [package_type:location]* format:location")
        ),
        make_option("-r", "--range-type", dest="rangetype", 
            action="callback", callback=_variable_args_cb_list, default=[],
            help=("[storage_type:url] [package_type:location]* format:location")
        ),

        make_option("-e", "--extent", dest="extent", 
            action="callback", callback=_variable_args_cb, default=None,
            help=("Override extent.")
        ),

        make_option("-s", "--size", dest="size", 
            action="callback", callback=_variable_args_cb,
            help=("Override size.")
        ),

        make_option("-p", "--projection", dest="projection", 
            action="store", default=None,
            help=("Override projection.")
        ),

        make_option("-f", "--footprint", dest="footprint", 
            action="callback", callback=_variable_args_cb,
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

        metadata_component = MetadataComponent(env)
        datas = kwargs["data"]
        metadatas = kwargs["metadata"]

        # TODO: what if the data is referenced in the metadata files? like in DIMAP
        # TODO: ignore this case right now.

        metadata_models = []

        for metadata in metadatas:
            import pdb; pdb.set_trace()
            storage, package, format, location = self._get_location_chain(metadata)
            metadata_model = backends.DataItem(
                location=location, format=format or "", semantic="metadata", 
                storage=storage, package=package,
            )
            metadata_model.full_clean()
            metadata_model.save()
            metadata_models.append(item)

        # TODO: not required, as the keys are already
        metadata_keys = set((
            "identifier", "extent", "size", "projection", 
            "footprint", "begin_time", "end_time"
        ))

        retrieved_metadata = {}

        # TODO: apply defaults from CLI


        with CacheContext() as c:
            for model in metadata_models:
                with open(retrieve(model, c)) as f:
                    content = f.read()
                    reader = metadata_component.get_reader_by_test(content)
                    if reader:
                        values = reader.read(content)
                        for key, value in values.items():
                            if key in metadata_keys:
                                retrieved_metadata.setdefault(key, value)

                            if key == "datafiles":
                                datas.append(value) # TODO append

        if len(metadata_keys - set(retrieved_metadata.keys())):
            raise 

        if len(datas) < 1:
            raise CommandError("No data files specified.")
        try:
            CoverageType = getattr(models, kwargs["coverage_type"])
        except:
            pass
            # TODO: split into module path/coverage and get correct coverage class




        try:
            coverage = CoverageType(**coverage_params)
            coverage.identifier = identifier # TODO: bug in models for some coverages
            coverage.full_clean()
            coverage.save()
        except ValidationError, e:
            # TODO: show error message
            raise

        

        # for each metadata create one data item
        




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


class DataChain(object):

    def __init__(self, location, format=None, packages=None, storage=None):
        pass
