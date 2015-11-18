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
from itertools import product
from os.path import isabs

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.synchronization import synchronize
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--root", "-r", dest="root",
            action='callback', callback=_variable_args_cb,
            default=None, help=("Collection(s) from which the "
                                "objects shall be removed.")
        ),
        make_option("--dry", "-d", dest="dry",
            action="store_true", default=False,
            help="Only do a dry-run and don't delete/register collections."
        )
    )

    args = (
        "<root-dir> [-p <pattern> [ ... ] ] "
    )

    help = """
        Synchronizes one or more collections and all their data sources.
    """

    def handle(self, patterns, *root_dirs):
        root_dir = root_dirs[0]

        subdirs = []
        existing_collections = models.DatasetSeries.objects.filter()  # TODO
        registered_ids = set(c.identifier for c in existing_collections)
        existing_ids = set(subdirs)

        for identifier in registered_ids - existing_ids:
            pass
            # TODO delete series

        for identifier in existing_ids - registered_ids:
            pass
            # TODO: register series

        for identifier in existing_ids & registered_ids:
            pass
            # TODO: print

