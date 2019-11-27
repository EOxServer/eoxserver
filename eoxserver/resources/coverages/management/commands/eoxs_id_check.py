#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
#-------------------------------------------------------------------------------

import sys
from django.core.management.base import CommandError, BaseCommand
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.resources.coverages import models


class Command(CommandOutputMixIn, BaseCommand):

    help = """
        Check whether one or more identifier are used by existing EOObjects or
        objects of a specified subtype.

        The existence is indicated by the returned exit-code. A non-zero value
        indicates that any of the supplied identifiers is already in use.
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("identifier", nargs="+")
        parser.add_argument(
            "-t", "--type", dest="type_name", default="EOObject",
            help="Optional. Restrict the listed identifiers to the given type."
        )

    def handle(self, *args, **kwargs):
        identifiers = kwargs["identifier"]
        type_name = kwargs["type_name"]

        try:
            # TODO: allow types residing in different apps
            object_model = getattr(models, type_name)
            if not issubclass(object_model, models.EOObject):
                raise CommandError("Unsupported type '%s'." % type_name)
        except AttributeError:
            raise CommandError("Unsupported type '%s'." % type_name)

        any_exits = False
        any_missing = False
        for identifier in identifiers:
            try:
                obj = object_model.objects.get(identifier=identifier)
                self.print_msg(
                    "The identifier '%s' is already in use by a '%s'."
                    % (identifier, obj.real_type.__name__)
                )
                any_exits = True
            except object_model.DoesNotExist:
                self.print_msg(
                    "The identifier '%s' is currently not in use." % identifier
                )
                any_missing = True

        sys.exit((2 if any_missing else 1) if any_exits else 0)
