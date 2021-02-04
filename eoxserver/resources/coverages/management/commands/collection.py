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
    """ Command to manage collections. This command uses sub-commands for the
        specific tasks: create, delete, insert, exclude, purge.
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        insert_parser = self.add_subparser(parser, 'insert')
        exclude_parser = self.add_subparser(parser, 'exclude')
        purge_parser = self.add_subparser(parser, 'purge')
        summary_parser = self.add_subparser(parser, 'summary')
        parsers = [
            create_parser, insert_parser, exclude_parser,
            purge_parser, summary_parser
        ]

        # identifier is a common argument (except for delete it is optional,
        # if --all is tagged)
        for parser in parsers:
            parser.add_argument(
                'identifier', nargs=1, help='The collection identifier'
            )

        create_parser.add_argument(
            '--type', '-t', dest='type_name',
            help='The collection type name. Optional.'
        )
        create_parser.add_argument(
            '--grid', '-g', dest='grid_name', default=None,
            help='The optional grid name.'
        )
        create_parser.add_argument(
            '--set', '-s', dest='set_overrides',
            nargs=2, default=[], action='append',
            help=(
                'Set (or override) additional metadata tags like '
                '"platform".'
            )
        )
        delete_parser.add_argument(
            '--all', '-a', action="store_true",
            default=False, dest='all_collections',
            help=(
                'When this flag is set, all the collections are '
                'selected to be derigesterd'
            )
        )

        delete_parser.add_argument(
                'identifier', default=None, nargs='?',
                help='The identifier of the collection to delete.'
        )
        # common arguments for insertion/exclusion
        insert_parser.add_argument(
            'object_identifiers', nargs='+',
            help=(
                'The identifiers of the objects (Product or Coverage) '
                'to insert'
            )
        )
        insert_parser.add_argument(
            '--use-extent', action='store_true', default=False,
            help=(
                'Whether to simply collection the bounding box of the '
                'footprint as the collections footprint'
            )
        )
        exclude_parser.add_argument(
            'object_identifiers', nargs='+',
            help=(
                'The identifiers of the objects (Product or Coverage) '
                'to exclude'
            )
        )
        exclude_parser.add_argument(
            '--use-extent', action='store_true', default=False,
            help=(
                'Whether to simply collection the bounding box of the '
                'footprint as the collections footprint'
            )
        )

        summary_parser.add_argument(
            '--products', action='store_true', default=True,
            dest='product_summary',
            help=('Collect summary product metadata. Default.')
        )
        summary_parser.add_argument(
            '--no-products', action='store_false', default=True,
            dest='coverage_summary',
            help=("Don't collect summary product metadata.")
        )

        summary_parser.add_argument(
            '--coverages', action='store_true', default=True,
            dest='product_summary',
            help=('Collect summary coverage metadata. Default.')
        )
        summary_parser.add_argument(
            '--no-coverages', action='store_false', default=True,
            dest='coverage_summary',
            help=("Don't collect summary coverage metadata.")
        )

    @transaction.atomic
    def handle(self, subcommand, identifier, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, insert, exclude, purge.
        """
        if subcommand == "create":
            self.handle_create(identifier[0], *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(identifier, *args, **kwargs)
        elif subcommand == "insert":
            self.handle_insert(identifier[0], *args, **kwargs)
        elif subcommand == "exclude":
            self.handle_exclude(identifier[0], *args, **kwargs)
        elif subcommand == "purge":
            self.handle_purge(identifier[0], *args, **kwargs)
        elif subcommand == "summary":
            self.handle_summary(identifier[0], *args, **kwargs)

    def handle_create(self, identifier, type_name, grid_name, **kwargs):
        """ Handle the creation of a new collection.
        """
        if grid_name:
            try:
                grid = models.Grid.objects.get(name=grid_name)
            except models.Grid.DoesNotExist:
                raise CommandError("Grid %r does not exist." % grid_name)
        else:
            grid = None

        collection_type = None
        if type_name:
            try:
                collection_type = models.CollectionType.objects.get(
                    name=type_name
                )
            except models.CollectionType.DoesNotExist:
                raise CommandError(
                    "Collection type %r does not exist." % type_name
                )

        models.Collection.objects.create(
            identifier=identifier,
            collection_type=collection_type, grid=grid
        )

        print('Successfully created collection %r' % identifier)

    def handle_delete(self, identifier, all_collections, *args, **kwargs):
        """ Handle the deletion of a collection
        """
        if not all_collections and not identifier:
            raise CommandError('please specify a collection/s to remove')
        else:
            if all_collections:
                collections = models.Collection.objects.all()
            elif identifier:
                collections = [self.get_collection(identifier)]
            for collection in collections:
                try:
                    collection_id = collection.identifier
                    collection.delete()
                    self.print_msg(
                        'Successfully deregistered collection %r'
                        % collection_id
                    )
                except models.Collection.DoesNotExist:
                    raise CommandError('No such Collection %r' % identifier)

    def handle_insert(self, identifier, object_identifiers, **kwargs):
        """ Handle the insertion of arbitrary objects into a collection
        """
        collection = self.get_collection(identifier)

        objects = list(
            models.EOObject.objects.filter(
                identifier__in=object_identifiers
            ).select_subclasses()
        )

        if len(objects) != len(set(object_identifiers)):
            actual = set(obj.identifier for obj in objects)
            missing = set(object_identifiers) - actual
            raise CommandError(
                "No such object with ID%s: %s"
                % (len(missing) > 1, ", ".join(missing))
            )

        for eo_object in objects:
            try:
                models.collection_insert_eo_object(
                    collection, eo_object, kwargs.get('use_extent', False)
                )
            except Exception as e:
                raise CommandError(
                    "Could not insert object %r into collection %r. "
                    "Error was: %s"
                    % (eo_object.identifier, collection.identifier, e)
                )

            print(
                'Successfully inserted object %r into collection %r'
                % (eo_object.identifier, collection.identifier)
            )

    def handle_exclude(self, identifier, object_identifiers, **kwargs):
        """ Handle the exclusion of arbitrary objects from a collection
        """
        collection = self.get_collection(identifier)

        objects = list(
            models.EOObject.objects.filter(
                identifier__in=object_identifiers
            ).select_subclasses()
        )

        if len(objects) != len(set(object_identifiers)):
            actual = set(obj.identifier for obj in objects)
            missing = set(object_identifiers) - actual
            raise CommandError(
                "No such object with ID%s: %s"
                % (len(missing) > 1, ", ".join(missing))
            )

        for eo_object in objects:
            try:
                models.collection_exclude_eo_object(
                    collection, eo_object, kwargs.get('use_extent', False)
                )
            except Exception as e:
                raise CommandError(
                    "Could not exclude object %r from collection %r. "
                    "Error was: %s"
                    % (eo_object.identifier, collection.identifier, e)
                )

            print(
                'Successfully excluded object %r from collection %r'
                % (eo_object.identifier, collection.identifier)
            )

    def handle_purge(self, identifier, **kwargs):
        # TODO: implement
        raise CommandError(
            "Could not exclude purge collection %r: not implemented"
            % identifier
        )
        print('Successfully purged collection %r' % identifier)

    def handle_summary(self, identifier, product_summary, coverage_summary,
                       **kwargs):
        models.collection_collect_metadata(
            self.get_collection(identifier),
            False, False, False, product_summary, coverage_summary
        )
        print('Successfully collected metadata for collection %r' % identifier)

    def get_collection(self, identifier):
        """ Helper method to get a collection by identifier or raise a
            CommandError.
        """
        try:
            return models.Collection.objects.get(identifier=identifier)
        except models.Collection.DoesNotExist:
            raise CommandError("Collection %r does not exist." % identifier)
