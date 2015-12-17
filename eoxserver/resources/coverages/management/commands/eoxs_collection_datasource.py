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
from textwrap import dedent

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages import models
from eoxserver.backends import models as backends
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, _variable_args_cb, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--identifier", "-i", dest="collection_ids",
            action='callback', callback=_variable_args_cb,
            default=None, help=("Collection(s) that will be provided with the "
                                "datasource.")
        ),
        make_option("--source", "-s", dest="source",
            action="store", default=None,
            help="Mandatory. The source glob pattern to match datasets"
        ),
        make_option("--template", "-t", dest="templates",
            action='callback', callback=_variable_args_cb,
            default=None, help=("Collection(s) that will be provided with the "
                                "datasource.")
        )
    )

    args = (
        "-i <collection-id> [-i ...] -s <source-path-glob> "
        "[-t <template-path-glob> ...]"
    )

    help = dedent("""
        Add a datasource to a collection.

        The datasource must have a primary source regular expression. When
        synchronized, all files matched will then be associated with expanded
        templates. The templates can make use the following template tags that
        will be replaced for each source file:

          - {basename}: the sources file basename (name without directory)
          - {root}: like {basename}, but without file extension
          - {extension}: the source files extension
          - {dirname}: the directory path of the source file
          - {source}: the full path of the source file
    """)

    @nested_commit_on_success
    def handle(self, collection_ids, source, templates, *args, **kwargs):
        if not collection_ids:
            raise CommandError(
                "Missing the mandatory collection identifier(s)!"
            )

        if not source:
            raise CommandError("Missing mandatory parameter `--source.")

        print templates
        templates = templates or []

        for collection_id in collection_ids:
            collection = models.Collection.objects.get(identifier=collection_id)
            datasource = models.DataSource.objects.create(collection=collection)

            backends.DataItem.objects.create(
                dataset=datasource, semantic="source[bands]", location=source
            )
            print source

            for template in templates:
                backends.DataItem.objects.create(
                    dataset=datasource, semantic="template[metadata]",
                    location=template
                )
                print template
