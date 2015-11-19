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

from optparse import make_option

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.synchronization import synchronize
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--identifier", "-i", dest="collection_ids",
            action='callback', callback=_variable_args_cb,
            default=None, help=("Collection(s) to be synchronized.")
        ),
        make_option("--all", "-a", dest="all_collections",
            action='store_true', default=False,
            help=("Optional. Synchronize all collections.")
        )
    )

    args = (
        "-i <collection-id> [-i <collection-id> ...] "
    )

    help = "Synchronizes one or more collections and all their data sources."

    @nested_commit_on_success
    def handle(self, collection_ids, all_collections, *args, **kwargs):
        if not collection_ids and not all_collections:
            raise CommandError(
                "Missing the mandatory collection identifier(s)!"
            )

        if all_collections:
            collection_ids = (
                c.identifier for c in models.Collection.objects.all()
            )

        for collection_id in collection_ids:
            try:
                collection = models.Collection.objects.get(
                    identifier=collection_id
                )
            except models.Collection.DoesNotExist:
                raise CommandError(
                    "Collection '%s' does not exist." % collection_id
                )

            self.print_msg("Synchronizing collection '%s'." % collection_id)
            registered, deleted = synchronize(collection.cast())
            self.print_msg(
                "Finished synchronizing collection '%s'. Registered %d new "
                "datasets, deleted %d stale datasets." % (
                    collection_id, registered, deleted
                )
            )
