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
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
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
    """ Command to manage product types. This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')

        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'name', nargs=1, help='The product type name. Mandatory.'
            )

        create_parser.add_argument(
            '--coverage-type', '-c',
            action='append', dest='coverage_type_names', default=[],
            help=(
            )
        )
        create_parser.add_argument(
            '--mask-type', '-m',
            action='append', dest='mask_type_names', default=[],
            help=(
            )
        )
        create_parser.add_argument(
            '--validity-mask-type',
            action='append', dest='validity_mask_type_names', default=[],
            help=(
            )
        )
        create_parser.add_argument(
            '--browse-type', '-b',
            action='append', dest='browse_type_names', default=[],
            help=(
            )
        )

        delete_parser.add_argument(
            '--force', '-f', action='store_true', default=False,
            help='Also remove all products associated with that type.'
        )

        list_parser.add_argument(
            '--no-detail', action="store_false", default=True, dest='detail',
            help="Disable the printing of details of the product type."
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, list.
        """
        if subcommand == "create":
            self.handle_create(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(kwargs.pop('name')[0], *args, **kwargs)
        elif subcommand == "list":
            self.handle_list(*args, **kwargs)

    def handle_create(self, name, coverage_type_names, mask_type_names,
                      validity_mask_type_names, browse_type_names,
                      *args, **kwargs):
        """ Handle the creation of a new product type.
        """

        product_type = models.ProductType.objects.create(name=name)

        for coverage_type_name in coverage_type_names:
            try:
                coverage_type = models.CoverageType.objects.get(
                    name=coverage_type_name
                )
                product_type.allowed_coverage_types.add(coverage_type)
            except models.CoverageType.DoesNotExist:
                raise CommandError(
                    'Coverage type %r does not exist' % coverage_type_name
                )

        for mask_type_name in mask_type_names:
            models.MaskType.objects.create(
                name=mask_type_name, product_type=product_type
            )

        for mask_type_name in validity_mask_type_names:
            models.MaskType.objects.create(
                name=mask_type_name, product_type=product_type,
                validity=True
            )

        for browse_type_name in browse_type_names:
            models.BrowseType.objects.create(
                name=browse_type_name, product_type=product_type
            )

        print('Successfully created product type %r' % name)

    def handle_delete(self, name, force, **kwargs):
        """ Handle the deletion of a product type
        """

        try:
            product_type = models.ProductType.objects.get(name=name)
        except models.ProductType.DoesNotExist:
            raise CommandError('No such product type %r' % name)

        if force:
            products = models.Product.objects.filter(product_type=product_type)
            for product in products:
                product.delete()

        product_type.delete()
        # TODO force
        print('Successfully deleted product type %r' % name)

    def handle_list(self, detail, *args, **kwargs):
        """ Handle the listing of product types
        """
        for product_type in models.ProductType.objects.all():
            print(product_type.name)
            if detail:
                for coverage_type in product_type.allowed_coverage_types.all():
                    print("\t%s" % coverage_type.name)
