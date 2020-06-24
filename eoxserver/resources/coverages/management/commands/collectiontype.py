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


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage collection types. This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')

        # identifier is a common argument
        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'name', nargs=1, help='The collection type name. Mandatory.'
            )

        create_parser.add_argument(
            '--coverage-type', '-c', action='append', default=[],
            dest='allowed_coverage_type_names',
            help=(
                'Specify a coverage type that is allowed in collections of this '
                'type.'
            )
        )
        create_parser.add_argument(
            '--product-type', '-p', action='append', default=[],
            dest='allowed_product_type_names',
            help=(
                'Specify a product type that is allowed in collections of this '
                'type.'
            )
        )

        delete_parser.add_argument(
            '--force', '-f', action='store_true', default=False,
            help='Also remove all collections associated with that type.'
        )

        list_parser.add_argument(
            '--no-detail', action="store_false", default=True, dest='detail',
            help="Disable the printing of details of the collection type."
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, insert and exclude.
        """
        if subcommand == "create":
            self.handle_create(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "list":
            self.handle_list(*args, **kwargs)

    def handle_create(self, name, allowed_coverage_type_names,
                      allowed_product_type_names, **kwargs):
        """ Handle the creation of a new collection type.
        """

        collection_type = models.CollectionType.objects.create(name=name)

        for allowed_coverage_type_name in allowed_coverage_type_names:
            try:
                collection_type.allowed_coverage_types.add(
                    models.CoverageType.objects.get(
                        name=allowed_coverage_type_name
                    )
                )
            except models.CoverageType.DoesNotExist:
                raise CommandError(
                    'Coverage type %r does not exist.' %
                    allowed_coverage_type_name
                )

        for allowed_product_type_name in allowed_product_type_names:
            try:
                collection_type.allowed_product_types.add(
                    models.ProductType.objects.get(
                        name=allowed_product_type_name
                    )
                )
            except models.ProductType.DoesNotExist:
                raise CommandError(
                    'Product type %r does not exist.' %
                    allowed_product_type_name
                )

        print('Successfully created collection type %r' % name)

    def handle_delete(self, name, force, **kwargs):
        """ Handle the deletion of a collection type
        """
        collection_type = models.CollectionType.objects.get(name=name)
        collection_type.delete()
        # TODO: force

        print('Successfully deleted collection type %r' % name)

    def handle_list(self, detail, *args, **kwargs):
        """ Handle the listing of product types
        """
        for collection_type in models.CollectionType.objects.all():
            print(collection_type.name)
            # if detail:
            #     for coverage_type in collection_type.allowed_coverage_types.all():
            #         print("\t%s" % coverage_type.name)
