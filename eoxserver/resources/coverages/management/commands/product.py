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
from eoxserver.resources.coverages.registration.product import ProductRegistrator


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage product types. This command uses sub-commands for the
        specific tasks: register, deregister
    """
    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        deregister_parser = self.add_subparser(parser, 'deregister')

        register_parser.add_argument(
            '--identifier', '-i', default=None,
            help='Override the identifier of the to-be registered product.'
        )

        register_parser.add_argument(
            '--footprint', default=None,
            help='Override the footprint of the to-be registered product.'
        )

        register_parser.add_argument(
            '--begin-time', default=None,
            help='Override the begin time of the to-be registered product.'
        )

        register_parser.add_argument(
            '--end-time', default=None,
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

        deregister_parser.add_argument(
            'identifier', nargs=1,
            help='The identifier of the product to deregister.'
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

    def handle_register(self, **kwargs):
        """ Handle the creation of a new product
        """

        ProductRegistrator().register(
            kwargs['file_handles'], kwargs['mask_handles'], kwargs['package'],
            dict(
                identifier=kwargs['identifier'],
                footprint=kwargs['footprint'],
                begin_time=kwargs['begin_time'],
                end_time=kwargs['end_time'],
            ), kwargs['type_name'], kwargs['extended_metadata']
        )

    def handle_deregister(self, identifier):
        """ Handle the deregistration a product
        """
        try:
            models.Product.objects.get(identifier=identifier).delete()
        except models.Product.DoesNotExist:
            raise CommandError('No such Product %r' % identifier)
