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
    """ Command to manage browse types. This command uses sub-commands for the
        specific tasks: create, delete, list
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')

        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'product_type_name', nargs=1,
                help='The product type name. Mandatory.'
            )

            parser.add_argument(
                'browse_type_name', nargs='?', default='',
                help='The browse type name. Optional.'
            )

        create_parser.add_argument(
            '--red', '-r', '--grey',
            dest='red_or_grey_expression', default=None,
        )
        create_parser.add_argument(
            '--green', '-g',
            dest='green_expression', default=None,
        )
        create_parser.add_argument(
            '--blue', '-b',
            dest='blue_expression', default=None,
        )
        create_parser.add_argument(
            '--alpha', '-a',
            dest='alpha_expression', default=None,
        )

        create_parser.add_argument(
            '--red-range', '--grey-range', nargs=2, type=float,
            dest='red_or_grey_range', default=(None, None),
        )
        create_parser.add_argument(
            '--green-range', nargs=2, type=float,
            dest='green_range', default=(None, None),
        )
        create_parser.add_argument(
            '--blue-range', nargs=2, type=float,
            dest='blue_range', default=(None, None),
        )
        create_parser.add_argument(
            '--alpha-range', nargs=2, type=float,
            dest='alpha_range', default=(None, None),
        )

        create_parser.add_argument(
            '--red-nodata', '--grey-nodata', type=float,
            dest='red_or_grey_nodata', default=None,
        )
        create_parser.add_argument(
            '--green-nodata', type=float,
            dest='green_nodata', default=None,
        )
        create_parser.add_argument(
            '--blue-nodata', type=float,
            dest='blue_nodata', default=None,
        )
        create_parser.add_argument(
            '--alpha-nodata', type=float,
            dest='alpha_nodata', default=None,
        )

        list_parser.add_argument(
            'product_type_name', nargs=1,
            help='The product type name. Mandatory.'
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: create, delete.
        """
        if subcommand == "create":
            self.handle_create(
                kwargs.pop('product_type_name')[0], *args, **kwargs
            )
        elif subcommand == "delete":
            self.handle_delete(
                kwargs.pop('product_type_name')[0], *args, **kwargs
            )
        elif subcommand == "list":
            self.handle_list(
                kwargs.pop('product_type_name')[0], *args, **kwargs
            )

    def handle_create(self, product_type_name, browse_type_name,
                      red_or_grey_expression, green_expression,
                      blue_expression, alpha_expression,
                      red_or_grey_range=(None, None), green_range=(None, None),
                      blue_range=(None, None), alpha_range=(None, None),
                      red_or_grey_nodata=None, green_nodata=None,
                      blue_nodata=None, alpha_nodata=None,
                      *args, **kwargs):
        """ Handle the creation of a new browse type.
        """

        try:
            product_type = models.ProductType.objects.get(
                name=product_type_name
            )
        except models.ProductType.DoesNotExist:
            raise CommandError(
                'Product type %r does not exist' % product_type_name
            )

        red_min, red_max = red_or_grey_range
        green_min, green_max = green_range
        blue_min, blue_max = blue_range
        alpha_min, alpha_max = alpha_range

        models.BrowseType.objects.create(
            product_type=product_type,
            name=browse_type_name,
            red_or_grey_expression=red_or_grey_expression,
            green_expression=green_expression,
            blue_expression=blue_expression,
            alpha_expression=alpha_expression,
            red_or_grey_range_min=red_min,
            red_or_grey_range_max=red_max,
            green_range_min=green_min,
            green_range_max=green_max,
            blue_range_min=blue_min,
            blue_range_max=blue_max,
            alpha_range_min=alpha_min,
            alpha_range_max=alpha_max,
            red_or_grey_nodata_value=red_or_grey_nodata,
            green_nodata_value=green_nodata,
            blue_nodata_value=blue_nodata,
            alpha_nodata_value=alpha_nodata,
        )

        if not browse_type_name:
            print(
                'Successfully created default browse type for product_type %r'
                % product_type_name
            )
        else:
            print(
                'Successfully created browse type %r for product_type %r'
                % (browse_type_name, product_type_name)
            )

    def handle_delete(self, product_type_name, browse_type_name, **kwargs):
        """ Handle the deletion of a browse type
        """

        try:
            product_type = models.ProductType.objects.get(
                name=product_type_name
            )
        except models.ProductType.DoesNotExist:
            raise CommandError('No such product type %r' % product_type_name)

        browse_type = product_type.browse_types.get(name=browse_type_name)

        browse_type.delete()

        if not browse_type_name:
            print(
                'Successfully deleted default browse type for product_type %r'
                % product_type_name
            )
        else:
            print(
                'Successfully deleted browse type %r for product_type %r'
                % (browse_type_name, product_type_name)
            )

    def handle_list(self, product_type_name, *args, **kwargs):
        """ Handle the listing of browse types
        """
        try:
            product_type = models.ProductType.objects.get(
                name=product_type_name
            )
        except models.ProductType.DoesNotExist:
            raise CommandError('No such product type %r' % product_type_name)

        for browse_type in product_type.browse_types.all():
            print(browse_type.name or '(Default)')

            red = browse_type.red_or_grey_expression
            green = browse_type.green_expression
            blue = browse_type.blue_expression
            alpha = browse_type.alpha_expression

            if red and not green and not blue and not alpha:
                print('\tGrey: \'%s\'' % red)

            if red:
                print('\tRed: \'%s\'' % red)

            if green:
                print('\tGreen: \'%s\'' % green)

            if blue:
                print('\tBlue: \'%s\'' % blue)

            if alpha:
                print('\tAlpha: \'%s\'' % alpha)
