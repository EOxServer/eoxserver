#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

from django.core.management import call_command
from django.core.management.base import CommandError, BaseCommand
from eoxserver.core.util.importtools import import_module
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):

    help = """
        Creates a new Collection. By default the type of the new collection is
        DatasetSeries.
        Optionally the collection can directly be inserted into other
        collections and can be directly supplied with sub-objects.

        The type of the collection must be specified with a prepended module
        path if the type is not one of the standard collection types.
        E.g: 'myapp.models.MyCollection'.
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-i", "--identifier", dest="identifier", required=True,
            help="Dataset series identifier."
        )
        parser.add_argument(
            "-t", "--type", dest="type", default="DatasetSeries", help=(
                "Optional. Type of the collection to create. Defaults to "
                "`DatasetSeries`."
            )
        )
        parser.add_argument(
            "-c", "--collection", dest="collection_ids", action='append',
            help="Optional. Link to one or more collections."
        )
        parser.add_argument(
            "-a", "--add", dest="object_ids", action='append',
            help="Optional. Link one or more eo-objects."
        )
        parser.add_argument(
            '--ignore-missing-collection', dest='ignore_missing_collection',
            action="store_true", default=False, help=(
                "Optional. Proceed even if the linked parent "
                "does not exist. By default, a missing parent "
                "will terminate the command."
            )
        )
        parser.add_argument(
            '--ignore-missing-object', dest='ignore_missing_object',
            action="store_true", default=False, help=(
                "Optional. Proceed even if the linked child "
                "does not exist. By default, a missing child "
                "will terminate the command."
            )
        )

    @nested_commit_on_success
    def handle(self, *args, **kwargs):
        identifier = kwargs['identifier']
        collection_type = kwargs["type"]
        try:
            module = models
            if "." in collection_type:
                mod_name, _, collection_type = collection_type.rpartition(".")
                module = import_module(mod_name)

            collection_class = getattr(module, collection_type)

            if not issubclass(collection_class, models.Collection):
                raise CommandError(
                    "Type '%s' is not a collection type." % collection_type
                )
        except AttributeError:
            raise CommandError(
                "Unsupported collection type '%s'." % collection_type
            )

        # is the identifier unique?
        if models.EOObject.objects.filter(identifier=identifier).exists():
            raise CommandError(
                "The identifier '%s' is already in use." % identifier
            )

        self.print_msg("Creating Collection: '%s'" % identifier)

        try:
            collection = collection_class(identifier=identifier)
            collection.full_clean()
            collection.save()

            ignore_missing_collection = kwargs["ignore_missing_collection"]
            # insert into super collections and insert child objects
            if kwargs["collection_ids"]:
                call_command(
                    "eoxs_collection_link",
                    collection_ids=kwargs["collection_ids"],
                    add_ids=[identifier],
                    ignore_missing_collection=ignore_missing_collection
                )

            if kwargs["object_ids"]:
                call_command(
                    "eoxs_collection_link",
                    collection_ids=[identifier], add_ids=kwargs["object_ids"],
                    ignore_missing_object=kwargs["ignore_missing_object"],
                )

        except Exception as error:
            self.print_traceback(error, kwargs)
            raise CommandError("Collection creation failed: %s" % error)

        self.print_msg("Collection created successfully.")
