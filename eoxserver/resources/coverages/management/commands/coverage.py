# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)
from eoxserver.resources.coverages.registration.registrators.gdal import (
    GDALRegistrator
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage coverages. This command uses sub-commands for the
        specific tasks: register, deregister
    """
    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        deregister_parser = self.add_subparser(parser, 'deregister')

        register_parser.add_argument(
            "--data", "--data-location", "-d",
            dest="data_locations", nargs="+", action="append", default=[],
            help=(
                "Add a data location to the coverage. In the form "
                "[[... storage] storage] path"
            )
        )
        register_parser.add_argument(
            "--meta-data", "--meta-data-location", "-m",
            dest="metadata_locations", nargs="+", action="append", default=[],
            help=(
                "Add a meta-data file to the coverage. In the form "
                "[[... storage] storage] path"
            )
        )
        register_parser.add_argument(
            '--type', '--coverage-type', '-t',
            dest='coverage_type_name', default=None,
            help='The name of the coverage type to associate the coverage with.'
        )
        register_parser.add_argument(
            '--grid', '-g',
            dest='grid_name', default=None,
            help='The name of the grid to associate the coverage with.'
        )
        register_parser.add_argument(
            "--size", "-s",
            dest="size", default=None, nargs="+",
            help="Override size."
        )
        register_parser.add_argument(
            "--origin", "-o", dest="origin", default=None, nargs="+",
            help="Override origin."
        )
        register_parser.add_argument(
            "--footprint", "-f",
            dest="footprint", default=None,
            help=(
                "Override footprint. Must be supplied as WKT Polygons or "
                "MultiPolygons."
            )
        )
        register_parser.add_argument(
            "--identifier", "-i",
            dest="identifier", default=None,
            help="Override identifier."
        )
        register_parser.add_argument(
            "--begin-time", "-b",
            dest="begin_time", default=None,
            help="Override begin time. Format is ISO8601 datetime strings."
        )
        register_parser.add_argument(
            "--end-time", "-e",
            dest="end_time", default=None,
            help="Override end time. Format is ISO8601 datetime strings."
        )
        register_parser.add_argument(
            "--replace", "-r",
            dest="replace", action="store_true", default=False,
            help=(
                "Optional. If the coverage with the given identifier already "
                "exists, replace it. Without this flag, this would result in "
                "an error."
            )
        )

        deregister_parser.add_argument(
            'identifier', nargs=1,
            help='The identifier of the coverage to derigster'
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: register, deregister.
        """
        print args
        print kwargs
        if subcommand == "register":
            self.handle_register(*args, **kwargs)
        elif subcommand == "deregister":
            self.handle_deregister(kwargs['identifier'][0], *args, **kwargs)

    def handle_register(self, coverage_type_name,
                        data_locations, metadata_locations,
                        **kwargs):
        """ Handle the creation of a new coverage.
        """
        overrides = {
            key: kwargs[key]
            for key in [
                'begin_time', 'end_time', 'footprint', 'identifier',
                'origin', 'size', 'grid'
            ]
            if kwargs.get(key)
        }

        GDALRegistrator().register(
            data_locations=data_locations,
            metadata_locations=metadata_locations,
            coverage_type_name=coverage_type_name,
            overrides=overrides,
            replace=kwargs['replace'],
        )

    def handle_deregister(self, identifier, **kwargs):
        """ Handle the deregistration a coverage
        """
        try:
            models.Coverage.objects.get(identifier=identifier).delete()
        except models.Coverage.DoesNotExist:
            raise CommandError('No such Coverage %r' % identifier)
        raise NotImplementedError
