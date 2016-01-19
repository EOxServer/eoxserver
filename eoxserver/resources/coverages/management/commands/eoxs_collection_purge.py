#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

from django.core.management import call_command
from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-i", "--identifier",
            dest="identifier", action="store", default=None,
            help=("Collection identifier.")
        ),
        make_option("-r", "--recursive", "--recursive-purge",
            dest="recursive", action="store_true", default=False,
            help=("Optional. Purge all contained collections.")
        ),
        make_option("-d", "--delete",
            dest="delete", action="store_true", default=False,
            help=("Optional. Delete the collection as-well.")

        )
    )

    args = "-i <collection-id> [-r] [-f]"

    help = """
        Purges a Collection, by deleting all containing items.

        By default, this command does not purge sub-collections contained in the
        specified collection.

        If the `--delete` option is set, then the collection(s) will even be
        removed as-well.
    """

    @nested_commit_on_success
    def handle(self, *args, **kwargs):
        identifier = kwargs['identifier']
        if not identifier:
            raise CommandError("Missing the mandatory collection identifier.")

        try:
            collection = models.Collection.objects.get(identifier=identifier)
        except models.Collection.DoesNotExist:
            raise CommandError("Collection '%s' does not exist." % identifier)

        try:
            count = self._purge_collection(
                collection, kwargs["recursive"], kwargs["delete"]
            )
        except Exception, e:
            self.print_traceback(e, kwargs)
            raise CommandError("Purge of the collection failed: %s" % e)

        self.print_msg("Successfully purged %d collections." % count)

    def _purge_collection(self, collection, recursive, delete):
        collection = collection.cast()
        count = 1

        if recursive:
            sub_collections = collection.eo_objects.filter(
                collection__isnull=False
            )

            for sub_collection in sub_collections:
                count += self._purge_collection(
                    sub_collection, recursive, delete
                )

        identifiers = collection.eo_objects.filter(
            collection__isnull=True
        ).values_list("identifier", flat=True)

        if identifiers:
            call_command("eoxs_dataset_deregister", *identifiers)

        if delete:
            call_command("eoxs_collection_delete",
                identifier=collection.identifier
            )

        return count
