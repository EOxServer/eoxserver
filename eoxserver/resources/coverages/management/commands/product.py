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

import re

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
from django.db.models import Q
from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.backends.storages import get_handler_class_for_model
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)
from eoxserver.resources.coverages.registration.product import (
    ProductRegistrator
)
from eoxserver.resources.coverages.registration.exceptions import (
    RegistrationError
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage product types. This command uses sub-commands for the
        specific tasks: register, deregister
    """
    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        deregister_parser = self.add_subparser(parser, 'deregister')
        discover_parser = self.add_subparser(parser, 'discover')

        register_parser.add_argument(
            '--identifier', '-i', default=None,
            help='Override the identifier of the to-be registered product.'
        )

        register_parser.add_argument(
            "--identifier-template",
            dest="identifier_template", default=None,
            help="Add a template to construct the final identifier."
        )

        register_parser.add_argument(
            '--footprint', default=None,
            help='Override the footprint of the to-be registered product.'
        )

        register_parser.add_argument(
            '--simplify-footprint',
            dest='simplify_footprint_tolerance', nargs='?',
            default=None, type=float,
            help=(
                'Simplify the footprint. Optionally specify a tolerance value.'
            )
        )

        register_parser.add_argument(
            '--begin-time', default=None, type=parse_iso8601,
            help='Override the begin time of the to-be registered product.'
        )

        register_parser.add_argument(
            '--end-time', default=None, type=parse_iso8601,
            help='Override the end time of the to-be registered product.'
        )

        register_parser.add_argument(
            '--set', '-s', dest='set_overrides',
            nargs=2, default=[], action='append',
            help=(
                'Set (or override) additional metadata tags like '
                '"opt:cloudCover".'
            )
        )

        register_parser.add_argument(
            '--metadata-file',
            dest='metadata_locations', nargs='+', default=[], action='append',
            help=(
                'Add metadata file to associate with the product. '
                'List of items. Can be specified multiple times.'
            )
        )

        register_parser.add_argument(
            '--type', '--product-type', '-t', dest='type_name', default=None,
            help=(
                'The name of the product type to associate the product with. '
                'Optional.'
            )
        )

        register_parser.add_argument(
            '--mask', '-m', dest='mask_locations', default=[], action='append',
            nargs=2,
            help=(
                'Add a mask to associate with the product. List of items, '
                'first one is the mask name, the rest is the location '
                'definition. Can be specified multiple times.'
            )
        )

        register_parser.add_argument(
            '--mask-geometry', '-g', dest='mask_geometries', default=[],
            action='append', nargs=2,
            help=(
                'Add a mask to associate with the product. List of items, '
                'first one is the mask name, second is the mask geometry in '
                'WKT. Can be specified multiple times.'
            )
        )

        register_parser.add_argument(
            '--no-extended-metadata', dest='extended_metadata',
            default=True, action='store_false',
            help=(
                'When this flag is set, only the basic metadata (identifier, '
                'footprint, begin- and end-time) is stored.'
            )
        )

        register_parser.add_argument(
            '--no-masks', dest='discover_masks',
            default=True, action='store_false',
            help=(
                'When this flag is set, no masks will be discovered.'
            )
        )

        register_parser.add_argument(
            '--no-browses', dest='discover_browses',
            default=True, action='store_false',
            help=(
                'When this flag is set, no browses will be discovered.'
            )
        )

        register_parser.add_argument(
            '--no-metadata', dest='discover_metadata',
            default=True, action='store_false',
            help=(
                'When this flag is set, no metadata will be discovered.'
            )
        )

        register_parser.add_argument(
            '--package', '-p', default=None,
            help=(
                'The path to a storage (directory, ZIP-file, etc.).'
            )
        )

        register_parser.add_argument(
            "--collection", "--collection-identifier", "-c",
            dest="collection_identifiers", action="append", default=[],
            help="Add the product to the specified collection."
        )

        register_parser.add_argument(
            "--replace", "-r",
            dest="replace", action="store_true", default=False,
            help=(
                "Optional. If the product with the given identifier already "
                "exists, replace it. Without this flag, this would result in "
                "an error."
            )
        )

        register_parser.add_argument(
            '--print-identifier', dest='print_identifier',
            default=False, action='store_true',
            help=(
                'When this flag is set, only the identifier of the registered '
                'product will be printed to stdout.'
            )
        )
        deregister_parser.add_argument(
            '--all', '-a', action="store_true",
            default=False, dest='all_products',
            help=(
                'When this flag is set, all the products are selected to be '
                'derigestered'
            )
        )

        deregister_parser.add_argument(
                'identifier', default=None, nargs='?',
                help='The identifier of the product to deregister.'
            )

        discover_parser.add_argument(
                'identifier', default=None,
                help='The identifier of the product to descover.'
            )

        discover_parser.add_argument(
            'pattern', nargs='?', default=None,
            help='A glob path pattern to limit the search.'
        )

        # TODO: only via 'browse' command?
        # register_parser.add_argument(
        #     '--browse', '-b',
        #     dest='browse_handles', default=None, action='append',
        #     # help='The name of the grid to associate the product with.'
        # )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: register, deregister.
        """
        if subcommand == "register":
            self.handle_register(*args, **kwargs)
        elif subcommand == "deregister":
            self.handle_deregister(*args, **kwargs)
        elif subcommand == "discover":
            self.handle_discover(kwargs.pop('identifier')[0], *args, **kwargs)

    def handle_register(self, **kwargs):
        """ Handle the creation of a new product
        """
        try:
            overrides = dict(
                identifier=kwargs['identifier'],
                footprint=kwargs['footprint'],
                begin_time=kwargs['begin_time'],
                end_time=kwargs['end_time'],
            )

            for name, value in kwargs['set_overrides']:
                overrides[convert_name(name)] = value

            mask_locations = kwargs['mask_locations'] + [
                (name, GEOSGeometry(geom))
                for name, geom in kwargs['mask_geometries']
            ]

            product, replaced = ProductRegistrator().register(
                metadata_locations=kwargs['metadata_locations'],
                mask_locations=mask_locations,
                package_path=kwargs['package'],
                overrides=overrides,
                identifier_template=kwargs['identifier_template'],
                type_name=kwargs['type_name'],
                extended_metadata=kwargs['extended_metadata'],
                discover_masks=kwargs['discover_masks'],
                discover_browses=kwargs['discover_browses'],
                discover_metadata=kwargs['discover_metadata'],
                replace=kwargs['replace'],
                simplify_footprint_tolerance=kwargs.get(
                    'simplify_footprint_tolerance'
                ),
            )

            for collection_identifier in kwargs['collection_identifiers']:
                try:
                    collection = models.Collection.objects.get(
                        identifier=collection_identifier
                    )
                except models.Collection.DoesNotExist:
                    raise CommandError(
                        'No such collection %r' % collection_identifier
                    )
                models.collection_insert_eo_object(collection, product)

        except RegistrationError as e:
            raise CommandError('Failed to register product. Error was %s' % e)

        if kwargs['print_identifier']:
            print(product.identifier)
        else:
            self.print_msg(
                'Successfully registered product %r' % product.identifier
            )

    def handle_deregister(self, identifier, all_products, *args, **kwargs):
        """ Handle the deregistration a product
        """
        if not all_products and not identifier:
            raise CommandError('please specify a product/s to remove')
        else:
            if all_products:
                products = models.Product.objects.all()
            elif identifier:
                products = [models.Product.objects.get(identifier=identifier)]
            for product in products:
                try:
                    product_id = product.identifier
                    grids = list(models.Grid.objects.filter(
                        coverage__parent_product=product)
                    )
                    product.delete()

                    # clean up grids
                    for grid in grids:
                        grid_used = models.EOObject.objects.filter(
                            Q(coverage__grid=grid) | Q(mosaic__grid=grid),
                        ).exists()
                        # clean up grid as well, if it is not referenced
                        # anymore but saving named (user defined) grids
                        if grid and not grid.name and not grid_used:
                            grid.delete()

                    self.print_msg(
                        'Successfully deregistered product %r' % product_id
                    )
                except models.Product.DoesNotExist:
                    raise CommandError('No such Product %r' % identifier)

    def handle_discover(self, identifier, pattern, *args, **kwargs):
        try:
            product = models.Product.objects.get(identifier=identifier)
        except models.Product.DoesNotExist:
            raise CommandError('No such Product %r' % identifier)

        package = product.package
        if package:
            handler_cls = get_handler_class_for_model(package)
            if handler_cls:
                with handler_cls(package.url) as handler:
                    for item in handler.list_files(pattern):
                        print(item)


def camel_to_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def convert_name(name):
    namespace, _, sub_name = name.partition(':')
    if namespace in ('eop', 'opt', 'sar', 'alt'):
        return camel_to_underscore(sub_name)
    return camel_to_underscore(name)
