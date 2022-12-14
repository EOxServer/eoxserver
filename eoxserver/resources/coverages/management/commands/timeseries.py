# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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


from django.core.management.base import BaseCommand
from django.db import transaction

from eoxserver.resources.coverages.registration.timeseries import register_time_series
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn,
    SubParserMixIn,
)


def parse_collection(identifier):
    try:
        return models.Collection.objects.get(identifier=identifier)
    except models.Collection.DoesNotExist:
        raise ValueError(f'No collection with identifier "{identifier}" found.')


def parse_coverage_type_mapping(mapping):
    # raises value error if not exactly 1 ":"
    dim, coverage_type_name = mapping.split(":")
    return (dim, coverage_type_name)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """Command to manage time series. This command uses sub-commands for the
    specific tasks: register, deregister
    """

    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, "register")
        deregister_parser = self.add_subparser(parser, "deregister")

        register_parser.add_argument(
            "--collection",
            "--collection-identifier",
            "-c",
            dest="collection",
            required=True,
            type=parse_collection,
            help="Register timeseries for this collection",
        )
        register_parser.add_argument(
            "--storage",
            help="The storage to use",
        )
        register_parser.add_argument(
            "--path",
            required=True,
            help="Path to timeseries file",
        )
        register_parser.add_argument(
            "--product-type-name",
            required=True,
            help="The product type name",
        )
        register_parser.add_argument(
            "--coverage-type-mapping",
            action="append",
            type=parse_coverage_type_mapping,
            required=True,
            help="Which dimension to map to which coverage type. "
            'Use : as separator, e.g. --coverage-type-mapping "/Band1:b1"',
        )
        register_parser.add_argument(
            "--x-dim-name",
            required=True,
            help="Name of the X dimension",
        )
        register_parser.add_argument(
            "--y-dim-name",
            required=True,
            help="Name of the Y dimension",
        )
        register_parser.add_argument(
            "--time-dim-name",
            required=True,
            help="Name of the time dimension",
        )
        register_parser.add_argument(
            "--product-template",
            required=True,
            help="Format string for product identifier. "
            "Can use the following template variables: "
            "collection_identifier, file_identifier, index, "
            "product_type, begin_time, end_time",
        )
        register_parser.add_argument(
            "--replace",
            "-r",
            dest="replace",
            action="store_true",
            default=False,
            help=(
                "Optional. If the time series with the given identifier already "
                "exists, replace it. Without this flag, this would result in "
                "an error."
            ),
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """Dispatch sub-commands: register, deregister."""
        if subcommand == "register":
            self.handle_register(*args, **kwargs)
        elif subcommand == "deregister":
            self.handle_deregister(*args, **kwargs)

    def handle_register(
        self,
        collection,
        storage,
        path,
        product_type_name,
        coverage_type_mapping,
        x_dim_name,
        y_dim_name,
        time_dim_name,
        product_template,
        replace,
        **kwargs,
    ):
        timeseries_path, replaced = register_time_series(
            collection=collection,
            storage=storage,
            path=path,
            product_type_name=product_type_name,
            coverage_type_mapping=dict(coverage_type_mapping),
            x_dim_name=x_dim_name,
            y_dim_name=y_dim_name,
            time_dim_name=time_dim_name,
            product_template=product_template,
            replace=replace,
        )

        self.print_msg(
            (
                f"Successfully {'replaced' if replaced else 'registered'}"
                f" timeseries {timeseries_path}"
            )
        )

    def handle_deregister(self, **kwargs):
        raise NotImplementedError()
