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
from django.db.models import Q

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage mosaics. This command uses sub-commands for the
        specific tasks: create, delete, insert, exclude, purge.
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        insert_parser = self.add_subparser(parser, 'insert')
        exclude_parser = self.add_subparser(parser, 'exclude')
        refresh_parser = self.add_subparser(parser, 'refresh')
        purge_parser = self.add_subparser(parser, 'purge')
        parsers = [
            create_parser, delete_parser, insert_parser, exclude_parser,
            refresh_parser, purge_parser
        ]

        # identifier is a common argument
        for parser in parsers:
            parser.add_argument(
                'identifier', nargs=1, help='The mosaic identifier'
            )

        create_parser.add_argument(
            '--type', '-t', dest='type_name', required=True,
            help='The coverage type name of the mosaic. Mandatory.'
        )
        create_parser.add_argument(
            '--grid', '-g', dest='grid_name', default=None,
            help='The optional grid name.'
        )

        # common arguments for insertion/exclusion
        insert_parser.add_argument(
            'coverage_identifiers', nargs='+',
            help='The identifiers of the coverages to insert'
        )
        exclude_parser.add_argument(
            'coverage_identifiers', nargs='+',
            help=(
                'The identifiers of the coverages to exclude'
            )
        )

    @transaction.atomic
    def handle(self, subcommand, identifier, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, insert, exclude, purge.
        """
        identifier = identifier[0]
        if subcommand == "create":
            self.handle_create(identifier, *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(identifier, *args, **kwargs)
        elif subcommand == "insert":
            self.handle_insert(identifier, *args, **kwargs)
        elif subcommand == "exclude":
            self.handle_exclude(identifier, *args, **kwargs)
        elif subcommand == "refresh":
            self.handle_refresh(identifier, *args, **kwargs)
        elif subcommand == "purge":
            self.handle_purge(identifier, *args, **kwargs)

    def handle_create(self, identifier, type_name, grid_name, **kwargs):
        """ Handle the creation of a new mosaic.
        """
        if grid_name:
            try:
                grid = models.Grid.objects.get(name=grid_name)
            except models.Grid.DoesNotExist:
                raise CommandError("Grid %r does not exist." % grid_name)
        else:
            grid = None

        try:
            coverage_type = models.CoverageType.objects.get(
                name=type_name
            )
        except models.CoverageType.DoesNotExist:
            raise CommandError(
                "Coverage type %r does not exist." % type_name
            )

        models.Mosaic.objects.create(
            identifier=identifier,
            coverage_type=coverage_type, grid=grid,
            axis_1_size=0,
        )

        self.print_msg(
            'Successfully inserted created mosaic %s' % identifier
        )

    def handle_delete(self, identifier, **kwargs):
        """ Handle the deletion of a mosaic
        """
        mosaic = self.get_mosaic(identifier)
        grid = mosaic.grid
        mosaic.delete()

        grid_used = models.EOObject.objects.filter(
            Q(coverage__grid=grid) | Q(mosaic__grid=grid),
        ).exists()

        # clean up grid as well, if it is not referenced anymore
        # but saving named (user defined) grids
        if grid and not grid.name and not grid_used:
            grid.delete()

        self.print_msg(
            'Successfully deleted mosaic %s' % identifier
        )

    def handle_insert(self, identifier, coverage_identifiers, **kwargs):
        """ Handle the insertion of coverages into a mosaic
        """
        mosaic = self.get_mosaic(identifier)

        coverages = list(
            models.Coverage.objects.filter(
                identifier__in=coverage_identifiers
            )
        )

        if len(coverages) != len(set(coverage_identifiers)):
            actual = set(obj.identifier for obj in coverages)
            missing = set(coverage_identifiers) - actual
            raise CommandError(
                "No such coverage with ID%s: %s"
                % ("s" if len(missing) > 1 else "", ", ".join(missing))
            )

        for coverage in coverages:
            try:
                models.mosaic_insert_coverage(mosaic, coverage)
                self.print_msg(
                    'Successfully inserted coverage %s into mosaic %s'
                    % (coverage.identifier, mosaic.identifier)
                )
            except Exception as e:
                raise CommandError(
                    "Could not insert coverage %r into mosaic %r. "
                    "Error was: %s"
                    % (coverage.identifier, mosaic.identifier, e)
                )

    def handle_exclude(self, identifier, coverage_identifiers, **kwargs):
        """ Handle the exclusion of arbitrary objects from a mosaic
        """
        mosaic = self.get_mosaic(identifier)

        coverages = list(
            models.Coverage.objects.filter(
                identifier__in=coverage_identifiers
            )
        )

        if len(coverages) != len(set(coverage_identifiers)):
            actual = set(obj.identifier for obj in coverages)
            missing = set(coverage_identifiers) - actual
            raise CommandError(
                "No such object with ID%s: %s"
                % (len(missing) > 1, ", ".join(missing))
            )

        for coverage in coverages:
            try:
                models.mosaic_exclude_coverage(mosaic, coverage)
                self.print_msg(
                    'Successfully excluded coverage %s from mosaic %s'
                    % (coverage.identifier, mosaic.identifier)
                )
            except Exception as e:
                raise CommandError(
                    "Could not exclude coverage %r from mosic %r. "
                    "Error was: %s"
                    % (coverage.identifier, mosaic.identifier, e)
                )

    def handle_refresh(self, identifier, **kwargs):
        mosaic = self.get_mosaic(identifier)
        try:
            models.mosaic_recalc_metadata(mosaic)
            mosaic.full_clean()
            mosaic.save()

            self.print_msg(
                'Successfully refreshed metadata for mosaic %s'
                % (mosaic.identifier)
            )
        except Exception as e:
            raise CommandError(
                "Could not refresh metadata for mosaic %r. "
                "Error was: %s"
                % (mosaic.identifier, e)
            )

    def handle_purge(self, identifier, **kwargs):
        pass

    def get_mosaic(self, identifier):
        """ Helper method to get a mosaic by identifier or raise a
            CommandError.
        """
        try:
            return models.Mosaic.objects.get(identifier=identifier)
        except models.Mosaic.DoesNotExist:
            raise CommandError("Mosaic %r does not exist." % identifier)
