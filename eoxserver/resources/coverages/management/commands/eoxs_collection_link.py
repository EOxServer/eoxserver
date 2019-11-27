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

from itertools import product
from django.core.management.base import CommandError, BaseCommand
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):

    help = """
        Link (insert) one or more EOObjects into one or more collections.
        Pre-existing links are ignored.
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "-c", "--collection", dest="collection_ids", action='append',
            required=True,
            help="Collection in which the object(s) shall be inserted."
        )
        parser.add_argument(
            "-a", "--add", dest="add_ids", action='append', required=True,
            help="Inserted eo-object."
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
        # extract the collections
        ignore_missing_collection = kwargs['ignore_missing_collection']
        collections = []
        for collection_id in kwargs['collection_ids']:
            try:
                collections.append(
                    models.Collection.objects.get(identifier=collection_id)
                )
            except models.Collection.DoesNotExist:
                msg = (
                    "There is no Collection matching the given "
                    "identifier: '%s'" % collection_id
                )
                if ignore_missing_collection:
                    self.print_wrn(msg)
                else:
                    raise CommandError(msg)

        # extract the children
        ignore_missing_object = kwargs['ignore_missing_object']
        objects = []
        for add_id in kwargs['add_ids']:
            try:
                objects.append(
                    models.EOObject.objects.get(identifier=add_id)
                )
            except models.EOObject.DoesNotExist:
                msg = (
                    "There is no EOObject matching the given identifier: '%s'"
                    % add_id
                )
                if ignore_missing_object:
                    self.print_wrn(msg)
                else:
                    raise CommandError(msg)

        try:
            for collection, eo_object in product(collections, objects):
                # check whether the link does not exist
                if eo_object not in collection:
                    self.print_msg(
                        "Linking: %s <--- %s" % (collection, eo_object)
                    )
                    collection.insert(eo_object)

                else:
                    self.print_wrn(
                        "Collection %s already contains %s"
                        % (collection, eo_object)
                    )

        except Exception as error:
            self.print_traceback(error, kwargs)
            raise CommandError("Linking failed: %s" % error)
