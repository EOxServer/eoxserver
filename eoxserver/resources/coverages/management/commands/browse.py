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


class Command(CommandOutputMixIn, SubParserMixIn, BaseCommand):
    """ Command to manage browses. This command uses sub-commands for the
        specific tasks: register, deregister
    """
    def add_arguments(self, parser):
        register_parser = self.add_subparser(parser, 'register')
        generate_parser = self.add_subparser(parser, 'generate')
        deregister_parser = self.add_subparser(parser, 'deregister')

        for parser in [register_parser, generate_parser, deregister_parser]:
            parser.add_argument(
                'identifier', nargs=1, help='The associated product identifier'
            )

        register_parser.add_argument(
            '--type', '--coverage-type', '-t', dest='type_name', default=None,
            help='The name of the coverage type to associate the coverage with.'
        )

        register_parser.add_argument(
            '--grid', '-g', dest='grid_name', default=None,
            help='The name of the grid to associate the coverage with.'
        )

    @transaction.atomic
    def handle(self, subcommand, identifier, *args, **kwargs):
        """ Dispatch sub-commands: register, deregister.
        """
        identifier = identifier[0]
        if subcommand == "register":
            self.handle_register(identifier, *args, **kwargs)
        elif subcommand == "generate":
            self.handle_generate(identifier, *args, **kwargs)
        elif subcommand == "deregister":
            self.handle_deregister(identifier, *args, **kwargs)

    def handle_register(self, identifier, **kwargs):
        """ Handle the registration of an existing browse.
        """

    def handle_generate(self, identifier, **kwargs):
        """ Handle the generation of a new browse image
        """
        raise NotImplementedError

    def handle_deregister(self, identifier, **kwargs):
        """ Handle the deregistration a browse image
        """
        try:
            models.Coverage.objects.get(identifier=identifier).delete()
        except models.Coverage.DoesNotExist:
            raise CommandError('No such Coverage %r' % identifier)
        raise NotImplementedError
