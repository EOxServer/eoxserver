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

from pprint import pprint

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
from django.db.models import Q

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)
from eoxserver.resources.coverages.registration.registrators.gdal import (
    GDALRegistrator
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage coverages. This command uses sub-commands for the
        specific tasks: register, deregister
    """
    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        deregister_parser = self.add_subparser(parser, 'deregister')

        register_parser.add_argument(
            "--data", "--data-location", "-d",
            dest="data_locations", nargs="+", action="append", default=[],
            help=(
                "Add a data location to the coverage. In the form "
                "[[... storage] storage] path"
            )
        )
        register_parser.add_argument(
            "--meta-data", "--meta-data-location", "-m",
            dest="metadata_locations", nargs="+", action="append", default=[],
            help=(
                "Add a meta-data file to the coverage. In the form "
                "[[... storage] storage] path"
            )
        )
        register_parser.add_argument(
            '--type', '--coverage-type', '-t',
            dest='coverage_type_name', default=None,
            help=(
                'The name of the coverage type to associate the coverage with.'
            )
        )
        register_parser.add_argument(
            '--grid', '-g',
            dest='grid', default=None,
            help='The name of the grid to associate the coverage with.'
        )
        register_parser.add_argument(
            "--size", "-s",
            dest="size", default=None, nargs="+",
            help="Override size."
        )
        register_parser.add_argument(
            "--origin", "-o", dest="origin", default=None, nargs="+",
            help="Override origin."
        )
        register_parser.add_argument(
            "--highest-resolution",
            dest="highest_resolution", action="store_true", default=False,
            help=(
                "Optional. If the coverage is comprised of raster files of "
                "different resolutions, the highest resolution is used, and "
                "all raster files of a lower resolution will be resampled."
            )
        )
        register_parser.add_argument(
            "--footprint", "-f",
            dest="footprint", default=None,
            help=(
                "Override footprint. Must be supplied as WKT Polygons or "
                "MultiPolygons."
            )
        )
        register_parser.add_argument(
            "--footprint-from-extent",
            dest="footprint_from_extent", action="store_true", default=False,
            help=(
                "Create the footprint from the coverages extent, reprojected "
                "to WGS 84"
            )
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
            "--identifier", "-i",
            dest="identifier", default=None,
            help="Override identifier."
        )
        register_parser.add_argument(
            "--identifier-template",
            dest="identifier_template", default=None,
            help="Add a template to construct the final identifier."
        )
        register_parser.add_argument(
            "--begin-time", "-b",
            dest="begin_time", default=None, type=parse_iso8601,
            help="Override begin time. Format is ISO8601 datetime strings."
        )
        register_parser.add_argument(
            "--end-time", "-e",
            dest="end_time", default=None, type=parse_iso8601,
            help="Override end time. Format is ISO8601 datetime strings."
        )
        register_parser.add_argument(
            "--product", "--product-identifier", "-p",
            dest="product_identifier", default=None,
            help="Add the coverage to the specified product."
        )
        register_parser.add_argument(
            "--collection", "--collection-identifier", "-c",
            dest="collection_identifiers", action="append", default=[],
            help="Add the coverage to the specified collection."
        )
        register_parser.add_argument(
            "--replace", "-r",
            dest="replace", action="store_true", default=False,
            help=(
                "Optional. If the coverage with the given identifier already "
                "exists, replace it. Without this flag, this would result in "
                "an error."
            )
        )
        register_parser.add_argument(
            "--use-subdatasets", "--subdatasets",
            dest="use_subdatasets", action="store_true", default=False,
            help=(
                "Optional. Tell the registrator to interpret colons in the "
                "filename as subdataset specifiers. Default is False."
            )
        )
        register_parser.add_argument(
            '--print-identifier', dest='print_identifier',
            default=False, action='store_true',
            help=(
                'When this flag is set, only the identifier of the registered '
                'coverage will be printed to stdout.'
            )
        )

        deregister_parser.add_argument(
            '--all', '-a', action="store_true",
            default=False, dest='all_coverages',
            help='When this flag is set, all the coverage are selected to be deregisterd'
        )


        deregister_parser.add_argument(
                'identifier', default=None, nargs='?',
                help='The identifier of the coverage to deregister.'
            )

        deregister_parser.add_argument(
            '--not-refresh-collections', dest='not_refresh_collections',
            default=False, action='store_true',
            help=(
                'When this flag is set, the collections and mosaics this '
                'coverage is part of will not have their metadata refreshed.'
            )
        )

    @transaction.atomic
    def handle(self, subcommand, *args, **kwargs):
        """ Dispatch sub-commands: register, deregister.
        """
        if subcommand == "register":
            self.handle_register(*args, **kwargs)
        elif subcommand == "deregister":
            self.handle_deregister(*args, **kwargs)

    def handle_register(self, coverage_type_name,
                        data_locations, metadata_locations,
                        **kwargs):
        """ Handle the creation of a new coverage.
        """
        overrides = {
            key: kwargs[key]
            for key in [
                'begin_time', 'end_time', 'footprint', 'identifier',
                'origin', 'size', 'grid'
            ]
            if kwargs.get(key)
        }

        report = GDALRegistrator().register(
            data_locations=data_locations,
            metadata_locations=metadata_locations,
            coverage_type_name=coverage_type_name,
            footprint_from_extent=kwargs['footprint_from_extent'],
            overrides=overrides,
            identifier_template=kwargs['identifier_template'],
            highest_resolution=kwargs['highest_resolution'],
            replace=kwargs['replace'],
            use_subdatasets=kwargs['use_subdatasets'],
            simplify_footprint_tolerance=kwargs.get(
                'simplify_footprint_tolerance'
            ),
        )

        product_identifier = kwargs['product_identifier']
        if product_identifier:
            product_identifier = product_identifier.format(
                identifier=report.coverage.identifier
            )
            try:
                product = models.Product.objects.get(
                    identifier=product_identifier
                )
            except models.Product.DoesNotExist:
                raise CommandError('No such product %r' % product_identifier)
            models.product_add_coverage(product, report.coverage)

        for collection_identifier in kwargs['collection_identifiers']:
            try:
                collection = models.Collection.objects.get(
                    identifier=collection_identifier
                )
            except models.Collection.DoesNotExist:
                raise CommandError(
                    'No such collection %r' % collection_identifier
                )
            models.collection_insert_eo_object(collection, report.coverage)

        if kwargs['print_identifier']:
            print(report.coverage.identifier)

        else:
            self.print_msg(
                'Successfully registered coverage %s'
                % report.coverage.identifier
            )

            if int(kwargs.get('verbosity', 0)) > 1:
                pprint(report.metadata_parsers)
                pprint(report.retrieved_metadata)

    def handle_deregister(self, identifier, not_refresh_collections, all_coverages, **kwargs):
        """ Handle the deregistration a coverage
        """
        if not all_coverages and not identifier:
            raise CommandError('please specify a coverage/s to remove')
        else:
            if all_coverages:
                coverages = models.Coverage.objects.all()
            elif identifier:
                coverages = [models.Coverage.objects.get(identifier=identifier)]
            for coverage in coverages:
                try:
                    collections = list(coverage.collections.all())
                    mosaics = list(coverage.mosaics.all())
                    grid = coverage.grid

                    if not not_refresh_collections:
                        for collection in collections:
                            models.collection_exclude_eo_object(collection, coverage)

                        for mosaic in mosaics:
                            models.mosaic_exclude_coverage(mosaic, coverage)
                    coverage_id = coverage.identifier
                    coverage.delete()

                    grid_used = models.EOObject.objects.filter(
                        Q(coverage__grid=grid) | Q(mosaic__grid=grid),
                    ).exists()

                    # clean up grid as well, if it is not referenced anymore
                    # but saving named (user defined) grids
                    if grid and not grid.name and not grid_used:
                        grid.delete()

                    self.print_msg(
                        'Successfully deregistered coverage %s' % coverage_id
                    )

                except models.Coverage.DoesNotExist:
                    raise CommandError('No such Coverage %r' % identifier)
