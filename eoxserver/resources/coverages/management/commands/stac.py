# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2020 EOX IT Services GmbH
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

import sys
import json

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.resources.coverages.registration.stac import (
    create_product_type_from_stac_item, register_stac_product
)
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to import or export EOxServer type schemas, consisting of
        coverage types, product types, collection types, mask types and
        browse types.
    """

    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        # export_parser = self.add_subparser(parser, 'export')
        types_parser = self.add_subparser(parser, 'types')

        for parser in (register_parser, types_parser):
            parser.add_argument(
                'location', nargs=1,
                help='The location of the STAC Items. Mandatory.'
            )
            parser.add_argument(
                '--in', dest='stdin', action="store_true", default=False,
                help='Read the STAC Item from stdin instead from a file.'
            )

        register_parser.add_argument(
            '--type', '--product-type', '-t', dest='type_name', default=None,
            help=(
                'The name of the product type to associate the product with. '
                'Optional.'
            )
        )
        register_parser.add_argument(
            '--create-type', '-c', dest='create_type',
            action="store_true", default=False,
            help=(
                'Whether to automatically create a product type from the STAC '
                'Item. Optional.'
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

        types_parser.add_argument(
            '--type', '--product-type', '-t', dest='type_name', default=None,
            help=(
                'The name of the new product type. Optional.'
            )
        )
        types_parser.add_argument(
            "--ignore-existing", "-i",
            dest="ignore_existing", action="store_true", default=False,
            help=(
                "Optional. Ignore the case when a product type already "
                "existed. Otherwise, an error is raised."
            )
        )

        # import_parser.add_argument(
        #     '--ignore-existing', action="store_true", default=False,
        #     help='Ignore already existing types.'
        # )

        # export_parser.add_argument(
        #     '--out', '-o', default=None,
        #     help=(
        #         'Write the exported schema to the provided file. By default '
        #         'the schema is written to stdout.'
        #     )
        # )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        if subcommand == "register":
            self.handle_register(*args, **kwargs)
        elif subcommand == "types":
            self.handle_types(*args, **kwargs)

    def handle_register(self, location, stdin, type_name, create_type, replace,
                        *args, **kw):
        if stdin:
            location = '.'
            values = [json.load(sys.stdin)]
        else:
            location = location[0]
            with open(location) as f:
                values = json.load(f)

        if create_type:
            product_type, is_new = \
                create_product_type_from_stac_item(values, type_name)
            self.print_msg("Created new product type %s" % product_type.name)
            type_name = product_type.name

        product, replaced = register_stac_product(
            values, type_name, replace=replace,
            file_href=location if not stdin else None,
        )
        self.print_msg(
            "Successfully %s product %s" % (
                'replaced' if replaced else 'registered',
                product.identifier
            )
        )

    def handle_types(self, location, stdin, type_name, ignore_existing,
                     *args, **kwargs):
        if stdin:
            values = json.load(sys.stdin)
        else:
            with open(location[0]) as f:
                values = json.load(f)

        product_type, created = create_product_type_from_stac_item(
            values, type_name, ignore_existing
        )
        if created:
            self.print_msg(
                "Successfully created product type %s" % product_type.name
            )
        else:
            self.print_msg(
                "Product type %s already existed" % product_type.name
            )
