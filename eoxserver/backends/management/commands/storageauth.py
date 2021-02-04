# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

import json

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.backends import models as backends
from eoxserver.backends.storage_auths import get_handler_for_model
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, SubParserMixIn
)


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage storages authorizations.
        This command uses sub-commands for the
        specific tasks: create, delete
    """
    def add_arguments(self, parser):
        create_parser = self.add_subparser(parser, 'create')
        delete_parser = self.add_subparser(parser, 'delete')

        # name is a common argument
        for parser in [create_parser, delete_parser]:
            parser.add_argument(
                'name', nargs=1, help='The storage auth name'
            )

        create_parser.add_argument(
            'url', nargs=1,
            help='The storage auth location in a URL format. Mandatory.'
        )
        create_parser.add_argument(
            '--type', '-t', dest='type_name', default=None,
            help=(
                'The storage auth type. Optional. Default is auto-detect the '
                'type.'
            )
        )
        create_parser.add_argument(
            '--parameter', '-p', dest='parameters', default=None, nargs='+',
            action='append',
            help='Pass arguments for that specific storage auth item.',
        )

        create_parser.add_argument(
            '--check', dest='check', default=False, action='store_true',
            help='Check access to the storage auth.',
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

    def handle_create(self, name, url, type_name, parameters, check, **kwargs):
        """ Handle the creation of a new storage.
        """
        url = url[0]

        def parse_parameter(key, value=None, *extra):
            if extra:
                raise CommandError('Extra arguments for parameter found')

            if value is None:
                key, _, value = key.partition('=')

            return key.replace('-', '_'), value

        parameters = dict(
            parse_parameter(*param)
            for param in parameters
        )

        storage_auth = backends.StorageAuth(
            name=name,
            url=url,
            storage_auth_type=type_name,
            auth_parameters=json.dumps(parameters),
        )
        storage_auth.full_clean()
        storage_auth.save()

        if check:
            _ = get_handler_for_model(storage_auth)
            # TODO perform check

        self.print_msg(
            'Successfully created storage auth %s (%s)' % (name, type_name)
        )

    def handle_delete(self, name, **kwargs):
        """ Handle the deletion of a storage
        """
        try:
            storage_auth = backends.StorageAuth.objects.get(name=name)
        except backends.StorageAuth.DoesNotExist:
            raise CommandError('No such storage with name %r' % name)
        type_name = storage_auth.storage_auth_type
        storage_auth.delete()

        self.print_msg(
            'Successfully deleted storage auth %s (%s)' % (name, type_name)
        )
