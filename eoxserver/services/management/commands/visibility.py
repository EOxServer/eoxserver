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

import itertools

from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.resources.coverages import models
from eoxserver.services import models as service_models
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn


class Command(CommandOutputMixIn, BaseCommand):
    """ Command to manage service visibility for EOObjects (Collections, Mosaics,
        Products and Coverages).
    """
    def add_arguments(self, parser):
        """
        """

        service_choices = service_models.ServiceVisibility.SERVICE_CHOICES

        parser.add_argument(
            'identifiers', nargs='+', metavar='identifier',
            help='List of identifiers to change the visibility of.'
        )

        parser.add_argument(
            '--service', dest='services', action='append', default=[],
            help=(
                'Add a service to change the visibility of for the given objects. '
                'Possible values are: %s' % ', '.join(
                    '%s (%s)' % choice
                    for choice in service_choices
                )
            )
        )

        for key, name in service_choices:
            parser.add_argument(
                '--%s' % key, dest='services', action='append_const', const=key,
                help=(
                    'Add the service %s to change the visibility of for the given '
                    'objects.' % name
                )
            )

        parser.add_argument(
            '--all', dest='services', action='store_const',
            const=[choice[0] for choice in service_choices],
            help='Change the visibility for all available services.'
        )

        parser.add_argument(
            '--hide', dest='visibility', default=True, action='store_false',
            help='Set the visibility to False.'
        )

        parser.add_argument(
            '--show', dest='visibility', default=True, action='store_true',
            help='Set the visibility to True (the default).'
        )

    @transaction.atomic
    def handle(self, identifiers, services, visibility, *args, **kwargs):
        """
        """
        if not identifiers:
            raise CommandError('No identifiers specified.')

        if not services:
            raise CommandError('No services specified.')

        for identifier, service in itertools.product(identifiers, services):
            try:
                eo_object = models.EOObject.objects.get(identifier=identifier)
            except models.EOObject.DoesNotExist:
                raise CommandError('No such EOObject %s' % identifier)

            service_visibility, _ = service_models.ServiceVisibility.objects.get_or_create(
                eo_object=eo_object, service=service,
            )

            service_visibility.visibility = visibility
            service_visibility.full_clean()
            service_visibility.save()

        self.print_msg(
            'Successfully changed visibility of %d objects for the services: %s' % (
                len(identifiers), ', '.join(services)
            )
        )
