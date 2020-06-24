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

import sys
import json
import re

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction, IntegrityError

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage coverage types. This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create',
            help='Create a new coverage type.'
        )
        import_parser = self.add_subparser(parser, 'import')
        delete_parser = self.add_subparser(parser, 'delete',
            help='Delete a coverage type.'
        )
        list_parser = self.add_subparser(parser, 'list')

        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'name', nargs=1, help='The coverage type name. Mandatory.'
            )

        create_parser.add_argument(
            '--field-type', action='append', nargs=5,
            metavar=(
                'identifier', 'description', 'definition', 'unit-of-measure',
                'wavelength'
            ),
            dest='field_types', default=[],
            help=(
                'Add a field type to the coverage type.'
            )
        )

        import_parser.add_argument(
            'locations', nargs='*',
            help='The location(s) of the coverage type schema(s). Mandatory.'
        )
        import_parser.add_argument(
            '--in, -i', dest='stdin', action="store_true", default=False,
            help='Read the definition from stdin instead from a file.'
        )

        delete_parser.add_argument(
            '--force', '-f', action='store_true', default=False,
            help='Also remove all collections associated with that type.'
        )

        list_parser.add_argument(
            '--no-detail', action="store_false", default=True, dest='detail',
            help="Disable the printing of details of the coverage type."
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, insert and exclude.
        """
        if subcommand == "create":
            self.handle_create(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "import":
            self.handle_import(*args, **kwargs)
        elif subcommand == "export":
            self.handle_export(*args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "list":
            self.handle_list(*args, **kwargs)

    def handle_create(self, name, field_types, **kwargs):
        """ Handle the creation of a new coverage type.
        """
        coverage_type = self._create_coverage_type(name)

        self._create_field_types(coverage_type, {}, [
            dict(
                identifier=field_type_definition[0],
                description=field_type_definition[1],
                definition=field_type_definition[2],
                unit_of_measure=field_type_definition[3],
                wavelength=field_type_definition[4]
            )
            for field_type_definition in field_types
        ])

        print('Successfully created coverage type %r' % name)

    def handle_import(self, locations, *args, **kwargs):
        def _import(definitions):
            if isinstance(definitions, dict):
                definitions = [definitions]

            for definition in definitions:
                self._import_definition(definition)

        if kwargs['stdin']:
            try:
                _import(json.load(sys.stdin))
            except ValueError:
                raise CommandError('Could not parse JSON from stdin')
        else:
            for location in locations:
                with open(location) as f:
                    try:
                        _import(json.load(f))
                    except ValueError:
                        raise CommandError(
                            'Could not parse JSON from %r' % location
                        )

    def handle_export(self, name, *args, **kwargs):
        pass

    def handle_delete(self, name, force, **kwargs):
        """ Handle the deletion of a collection type
        """
        try:
            coverage_type = models.CoverageType.objects.get(name=name)

            if force:
                coverages = models.Coverage.objects.filter(
                    coverage_type=coverage_type
                )
                coverages.delete()
            nil_values = set(models.NilValue.objects.filter(
                field_types__coverage_type=coverage_type
            ))

            coverage_type.delete()

            # delete orphaned nil-values
            for nil_value in nil_values:
                if nil_value.field_types.count() == 0:
                    nil_value.delete()

        except models.CoverageType.DoesNotExist:
            raise CommandError('No such coverage type: %r' % name)

        print('Successfully deleted coverage type %r' % name)

    def handle_list(self, detail, *args, **kwargs):
        """ Handle the listing of product types
        """
        for coverage_type in models.CoverageType.objects.all():
            print(coverage_type.name)
            if detail:
                for coverage_type in coverage_type.field_types.all():
                    print("\t%s" % coverage_type.identifier)

    def _import_definition(self, definition):
        name = str(definition['name'])
        coverage_type = self._create_coverage_type(name)
        field_type_definitions = (
            definition.get('field_type') or definition.get('bands')
        )
        self._create_field_types(
            coverage_type, definition, field_type_definitions
        )
        self.print_msg('Successfully imported coverage type %r' % name)

    def _create_coverage_type(self, name):
        try:
            return models.CoverageType.objects.create(name=name)
        except IntegrityError:
            raise CommandError("Coverage type %r already exists." % name)

    def _create_field_types(self, coverage_type, coverage_type_definition,
                            field_type_definitions):
        for i, field_type_definition in enumerate(field_type_definitions):
            uom = (
                field_type_definition.get('unit_of_measure') or
                field_type_definition.get('uom')
            )

            field_type = models.FieldType(
                coverage_type=coverage_type,
                index=i,
                identifier=field_type_definition.get('identifier'),
                description=field_type_definition.get('description'),
                definition=field_type_definition.get('definition'),
                unit_of_measure=uom,
                wavelength=field_type_definition.get('wavelength'),
                significant_figures=field_type_definition.get(
                    'significant_figures'
                )
            )

            if 'numbits' in field_type_definition:
                field_type.numbits = field_type_definition['numbits']
            if 'signed' in field_type_definition:
                field_type.signed = field_type_definition['signed']
            if 'is_float' in field_type_definition:
                field_type.is_float = field_type_definition['is_float']

            # per field data type
            if 'data_type' in field_type_definition:
                field_type.numbits, field_type.signed, field_type.is_float = \
                    self._parse_data_type(field_type_definition['data_type'])

            # global data type
            elif 'data_type' in coverage_type_definition:
                field_type.numbits, field_type.signed, field_type.is_float = \
                    self._parse_data_type(coverage_type_definition['data_type'])

            field_type.full_clean()
            field_type.save()

            nil_value_definitions = field_type_definition.get('nil_values', [])
            for nil_value_definition in nil_value_definitions:
                # TODO: in Django 1.11 a `get` query did not work
                nil_value = next(iter(models.NilValue.objects.filter(
                    value=nil_value_definition['value'],
                    reason=nil_value_definition['reason'],
                    field_types__coverage_type=coverage_type,
                )), None)
                if not nil_value:
                    nil_value = models.NilValue.objects.create(
                        value=nil_value_definition['value'],
                        reason=nil_value_definition['reason'],
                    )

                nil_value.field_types.add(field_type)
                nil_value.save()

            allowed_value_ranges = field_type_definition.get(
                'allowed_value_ranges', []
            )
            for allowed_value_range_definition in allowed_value_ranges:
                models.AllowedValueRange.objects.create(
                    field_type=field_type,
                    start=allowed_value_range_definition[0],
                    end=allowed_value_range_definition[1]
                )

    def _parse_data_type(self, data_type):
        data_type = data_type.lower()
        is_float = data_type.startswith('float')
        signed = data_type.startswith('float') or data_type.startswith('int')
        try:
            if data_type == 'byte':
                numbits = 8
            else:
                numbits = int(
                    re.search(r'[a-zA-Z]+(\d*)', data_type).groups()[0]
                )
        except ValueError:
            numbits = None
        except AttributeError:
            raise CommandError('Invalid data type description %r' % data_type)
        return numbits, signed, is_float
