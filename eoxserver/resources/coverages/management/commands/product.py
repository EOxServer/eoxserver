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

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.backends.storages import get_handler_class_for_model
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)
from eoxserver.resources.coverages.registration.product import ProductRegistrator
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
            '--footprint', default=None,
            help='Override the footprint of the to-be registered product.'
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
            '--metadata-file', dest='file_handles', default=[], action='append',
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
            '--mask', '-m', dest='mask_handles', default=[], action='append',
            help=(
                'Add a mask to associate with the product. List of items, '
                'first one is the mask name, the rest is the location '
                'definition. Can be specified multiple times.'
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
            '--package', default=None,
            help=(
                'The path to a storage (directory, ZIP-file, etc.).'
            )
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

        for parser in [deregister_parser, discover_parser]:
            parser.add_argument(
                'identifier', nargs=1,
                help='The identifier of the product to deregister.'
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
            self.handle_deregister(kwargs['identifier'][0])
        elif subcommand == "discover":
            self.handle_discover(kwargs.pop('identifier')[0], *args, **kwargs)

    def handle_register(self, **kwargs):
        """ Handle the creation of a new product
        """
        try:
            product, replaced = ProductRegistrator().register(
                kwargs['file_handles'], kwargs['mask_handles'],
                kwargs['package'],
                dict(
                    identifier=kwargs['identifier'],
                    footprint=kwargs['footprint'],
                    begin_time=kwargs['begin_time'],
                    end_time=kwargs['end_time'],
                ), kwargs['type_name'], kwargs['extended_metadata'],
                replace=kwargs['replace']
            )
        except RegistrationError as e:
            raise CommandError('Failed to register product. Error was %s' % e)

        if kwargs['print_identifier']:
            print(product.identifier)

    def handle_deregister(self, identifier, *args, **kwargs):
        """ Handle the deregistration a product
        """
        try:
            models.Product.objects.get(identifier=identifier).delete()
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
