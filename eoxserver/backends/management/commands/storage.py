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

from eoxserver.backends import models as backends
from eoxserver.backends.storages import (
    get_handler_by_test, get_handler_class_by_name
)
from eoxserver.backends.util import resolve_storage_and_path, resolve_storage
from eoxserver.backends.access import vsi_list_storage, get_vsi_env
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage storages. This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')
        list_parser = self.add_subparser(parser, 'list')
        env_parser = self.add_subparser(parser, 'env')

        # name is a common argument
        for parser in [create_parser, delete_parser, list_parser, env_parser]:
            parser.add_argument(
                'name', nargs=1, help='The storage name'
            )

        create_parser.add_argument(
            'url', nargs=1,
            help='The storage location in a URL format. Mandatory.'
        )
        create_parser.add_argument(
            '--type', '-t', dest='type_name', default=None,
            help='The storage type. Optional. Default is auto-detect the type.'
        )
        create_parser.add_argument(
            '--parent', '-p', dest='parent_name', default=None,
            help='The name of the parent storage. Optional.'
        )
        create_parser.add_argument(
            '--storage-auth', '--storage-auth-name', '--auth', '-a',
            dest='storage_auth_name', default=None,
            help='The name of the storage auth to use. Optional',
        )

        for parser in [list_parser, env_parser]:
            parser.add_argument(
                'paths', nargs='*', default=None,
                help=(
                    'Possible sub-path on that storage. This may include '
                    'specifiers for sub-storages'
                )
            )

        list_parser.add_argument(
            '--pattern', '--glob', '-p', '-g',
            dest='pattern', default=None,
            help='A glob pattern to filter the listing of files. Optional.'
        )

    @transaction.atomic
    def handle(self, subcommand, name, *args, **kwargs):
        """ Dispatch sub-commands: create, delete, insert, exclude, purge.
        """
        name = name[0]
        if subcommand == "create":
            self.handle_create(name, *args, **kwargs)
        elif subcommand == "delete":
            self.handle_delete(name, *args, **kwargs)
        elif subcommand == "list":
            self.handle_list(name, *args, **kwargs)
        elif subcommand == "env":
            self.handle_env(name, *args, **kwargs)

    def handle_create(self, name, url, type_name, parent_name,
                      storage_auth_name, **kwargs):
        """ Handle the creation of a new storage.
        """
        url = url[0]
        parent = None

        if type_name:
            handler = get_handler_class_by_name(type_name)
            if not handler:
                raise CommandError(
                    'Storage type %r is not supported' % type_name
                )
        else:
            handler = get_handler_by_test(url)
            if handler:
                type_name = handler.name
            else:
                raise CommandError(
                    'Could not determine type for storage location %r' % url
                )

        if parent_name:
            try:
                parent = backends.Storage.objects.get(name=parent_name)
            except backends.Storage.DoesNotExist:
                raise CommandError(
                    'No such storage with name %r' % parent_name
                )

        if storage_auth_name:
            storage_auth = backends.StorageAuth.objects.get(
                name=storage_auth_name
            )
        else:
            storage_auth = None

        backends.Storage.objects.create(
            name=name, url=url, storage_type=type_name, parent=parent,
            storage_auth=storage_auth,
        )

        self.print_msg(
            'Successfully created storage %s (%s)' % (
                name or url, type_name
            )
        )

    def handle_delete(self, name, **kwargs):
        """ Handle the deletion of a storage
        """
        try:
            storage = backends.Storage.objects.get(name=name)
        except backends.Storage.DoesNotExist:
            raise CommandError('No such storage with name %r' % name)

        type_name = storage.storage_type
        storage.delete()

        self.print_msg(
            'Successfully deleted storage %s (%s)' % (name, type_name)
        )

    def handle_list(self, name, paths=None, pattern=None, **kwargs):
        storage, path = resolve_storage_and_path(
            [name] + paths or [], save=False
        )
        files = vsi_list_storage(storage, path, pattern)
        for filename in files:
            print(filename)

    def handle_env(self, name, paths, **kwargs):
        storage = resolve_storage([name] + paths or [], save=False)
        for key, value in get_vsi_env(storage).items():
            print('%s="%s"' % (key, value))
