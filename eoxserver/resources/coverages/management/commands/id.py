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

import sys
from itertools import chain

from django.core.management.base import CommandError, BaseCommand
from django.db.models import Q

from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    def add_arguments(self, parser):
        check_parser = self.add_subparser(parser, 'check')
        list_parser = self.add_subparser(parser, 'list')

        check_parser.add_argument(
            'identifiers', nargs='+',
            help='The identifiers of the objects to check for existence.'
        )
        check_parser.add_argument(
            '-t', '--type', dest="type_name", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        )

        list_parser.add_argument(
            'identifiers', nargs='*',
            help=('Optional. The identifiers of the objects to check for '
                  'existence.')
        )
        list_parser.add_argument(
            '-t', '--type', dest="type_name", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        )
        list_parser.add_argument(
            '-r', '--recursive',
            dest="recursive", action="store_true", default=False,
            help=("Optional. Recursive listing for collections/products.")
        ),
        list_parser.add_argument(
            '-s', '--suppress-type',
            dest="suppress_type", action="store_true", default=False,
            help=("Optional. Supress the output of the type. By default, the "
                  "type is also printed after the identifier.")
        )
        list_parser.add_argument(
            '-c', '--collection',
            dest="collections", action="append", default=None,
            help=("Optional. Specify a collection that objects must be part "
                  "of. Can be specified multiple times.")
        )

    def handle(self, subcommand, *args, **kwargs):
        if subcommand == "check":
            return self.handle_check(*args, **kwargs)
        elif subcommand == "list":
            return self.handle_list(*args, **kwargs)

    def handle_check(self, identifiers, type_name, *args, **kwargs):
        if not identifiers:
            raise CommandError("Missing the mandatory identifier(s).")

        base_qs = self.get_queryset(type_name)

        if type_name == "EOObject":
            base_qs = base_qs.select_subclasses()

        used = False
        for identifier in identifiers:
            try:
                obj = base_qs.get(identifier=identifier)
                self.print_msg(
                    "The identifier '%s' is already in use by a '%s'."
                    % (identifier, type(obj).__name__)
                )
                used = True
            except base_qs.model.DoesNotExist:
                self.print_msg(
                    "The identifier '%s' is currently not in use." % identifier
                )

        if used:
            sys.exit(1)

    def handle_list(self, identifiers, type_name, suppress_type, collections,
                    **kwargs):
        eo_objects = self.get_queryset(type_name)
        if type_name == 'EOObject':
            eo_objects = eo_objects.select_subclasses()

        if identifiers:
            eo_objects = eo_objects.filter(identifier__in=identifiers)

        if collections:
            eo_objects = eo_objects.filter(
                Q(coverage__collections__identifier__in=collections)
                | Q(product__collections__identifier__in=collections)
            )

        for eo_object in eo_objects:
            self.print_object(eo_object, kwargs["recursive"], suppress_type)

    def get_queryset(self, type_name):
        try:
            # TODO: allow types residing in different apps
            ObjectType = getattr(models, type_name)
            if not issubclass(ObjectType, models.EOObject):
                raise CommandError("Unsupported type '%s'." % type_name)
        except AttributeError:
            raise CommandError("Unsupported type '%s'." % type_name)

        return ObjectType.objects.all()

    def print_object(self, eo_object, recursive=False, suppress_type=False,
                     level=0):
        indent = "  " * level

        if not suppress_type:
            print("%s%s %s" % (indent, eo_object.identifier,
                               eo_object.__class__.__name__))
        else:
            print("%s%s" % (indent, eo_object.identifier))

        if recursive:
            products = []
            coverages = []
            if isinstance(eo_object, models.Collection):
                products = eo_object.products.all()
                coverages = eo_object.coverages.all()

            elif isinstance(eo_object, models.Product):
                coverages = eo_object.coverages.all()

            for sub_eo_object in chain(products, coverages):
                self.print_object(
                    sub_eo_object, recursive, suppress_type, level+1
                )
