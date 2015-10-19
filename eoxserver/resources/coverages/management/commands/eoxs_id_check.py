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
from optparse import make_option

from django.core.management.base import CommandError, BaseCommand

from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn
)

from eoxserver.resources.coverages import models


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-t", "--type",
            dest="type_name", action="store", default="EOObject",
            help=("Optional. Restrict the listed identifiers to given type.")
        ),
    )

    args = "<id> [<id> ...] [-t <type>]"

    help = """
        Check whether one or more identifier are used by existing EOObjects or
        objects of a specified subtype.

        The existence is indicated by the returned exit-code. A non-zero value
        indicates that any of the supplied identifiers is already in use.
    """

    def handle(self, *identifiers, **kwargs):
        if not identifiers:
            raise CommandError("Missing the mandatory identifier(s).")

        type_name = kwargs["type_name"]

        try:
            # TODO: allow types residing in different apps
            ObjectType = getattr(models, type_name)
            if not issubclass(ObjectType, models.EOObject):
                raise CommandError("Unsupported type '%s'." % type_name)
        except AttributeError:
            raise CommandError("Unsupported type '%s'." % type_name)

        used = False
        for identifier in identifiers:
            try:
                obj = ObjectType.objects.get(identifier=identifier)
                self.print_msg(
                    "The identifier '%s' is already in use by a '%s'."
                    % (identifier, obj.real_type.__name__)
                )
                used = True
            except ObjectType.DoesNotExist:
                self.print_msg(
                    "The identifier '%s' is currently not in use." % identifier
                )

        if used:
            sys.exit(1)
