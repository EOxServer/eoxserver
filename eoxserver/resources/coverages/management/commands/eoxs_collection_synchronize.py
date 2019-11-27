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

from django.core.management.base import CommandError, BaseCommand
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.synchronization import synchronize
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):

    help = "Synchronizes one or more collections and all their data sources."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--identifier", "-i", dest="collection_ids", action='append',
            help="Collection to be synchronized."
        )
        parser.add_argument(
            "--all", "-a", dest="all_collections", action='store_true',
            default=False, help="Optional. Synchronize all collections."
        )

    @nested_commit_on_success
    def handle(self, collection_ids, all_collections, *args, **kwargs):

        if all_collections:
            collection_ids = [
                c.identifier for c in models.Collection.objects.all()
            ]
        elif not collection_ids:
            raise CommandError(
                "Missing the mandatory collection identifier(s)!"
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
