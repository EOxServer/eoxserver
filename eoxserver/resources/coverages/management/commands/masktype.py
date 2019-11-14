# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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
    """ Command to manage mask types. This command uses sub-commands for the
        specific tasks: create, delete, list
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')

        for parser in [create_parser, delete_parser, list_parser]:
            parser.add_argument(
                'product_type_name', nargs=1,
                help='The product type name. Mandatory.'
            )

        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'mask_type_name', nargs=1,
                help='The mask type name. Mandatory.'
            )

        create_parser.add_argument(
            '--validity',
            dest='validity', action='store_true', default=False,
            help='Whether this mask is a validity mask or an invalidity mask. '
                 'Defaults to invalidity.'
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete.
        """
        if subcommand == "create":
            self.handle_create(
                kwargs.pop('product_type_name')[0],
                kwargs.pop('mask_type_name')[0],
                *args, **kwargs
            )
        elif subcommand == "delete":
            self.handle_delete(
                kwargs.pop('product_type_name')[0],
                kwargs.pop('mask_type_name')[0],
                *args, **kwargs
            )
        elif subcommand == "list":
            self.handle_list(
                kwargs.pop('product_type_name')[0], *args, **kwargs
            )

    def handle_create(self, product_type_name, mask_type_name, validity,
                      *args, **kwargs):
        """ Handle the creation of a new mask type.
        """

        try:
            product_type = models.ProductType.objects.get(name=product_type_name)
        except models.ProductType.DoesNotExist:
            raise CommandError(
                'Product type %r does not exist' % product_type_name
            )

        models.MaskType.objects.create(
            product_type=product_type,
            name=mask_type_name,
            validity=validity,
        )

        print(
            'Successfully created mask type %r for product type %r'
            % (mask_type_name, product_type_name)
        )

    def handle_delete(self, product_type_name, mask_type_name, **kwargs):
        """ Handle the deletion of a mask type
        """

        try:
            product_type = models.ProductType.objects.get(name=product_type_name)
        except models.ProductType.DoesNotExist:
            raise CommandError('No such product type %r' % product_type_name)

        mask_type = product_type.mask_types.get(name=mask_type_name)

        mask_type.delete()

        print(
            'Successfully deleted mask type %r for product type %r'
            % (mask_type_name, product_type_name)
        )

    def handle_list(self, product_type_name, *args, **kwargs):
        """ Handle the listing of mask types
        """
        try:
            product_type = models.ProductType.objects.get(name=product_type_name)
        except models.ProductType.DoesNotExist:
            raise CommandError('No such product type %r' % product_type_name)

        for mask_type in product_type.mask_types.all():
            print("%s %s" % (mask_type.name, '(validity)' if mask_type.validity else ''))
