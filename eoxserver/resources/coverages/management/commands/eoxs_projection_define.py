#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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

from optparse import make_option

from django.core.exceptions import ValidationError
from django.core.management.base import CommandError, BaseCommand
from django.db import IntegrityError

from eoxserver.contrib import osr
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-n", "--name",
            dest="name", action="store", default=None,
            help=("The name of the projection to be defined.")
        ),
        make_option("-f", "--format",
            dest="frmt", action="store", default=None,
            help=("Optional. The format of the projection definition. "
                  "Default is a smart guess. If given, must be one of "
                  "'WKT', 'PROJ', 'XML', 'URL'.")
        ),
        make_option("-d", "--delete",
            dest="delete", action="store_true", default=False,
            help=("Optional. Delete a previously defined projection.")
        ),
    )

    args = (
        "-n <name> ([-f <format>] <projection-definition>) | -d"
    )

    help = """
        Define a projection and register it under a given name. The projection
        can be defined in the following formats: 'WKT', 'PROJ', 'XML', 'URL'.
        Before it is registered, the projection is checked for validity.

        Alternatively, the projection can be deleted using the '-d' switch.
    """

    @nested_commit_on_success
    def handle(self, *args, **kwargs):
        name = kwargs['name']
        if not name:
            raise CommandError("Missing the mandatory projection name.")

        # if delete switch was used, just delete the existing projection, if
        # it exists.
        if kwargs.get("delete"):
            try:
                projection = models.Projection.objects.get(name=name)
                projection.delete()
                self.print_msg(
                    "Successfully removed projection definition '%s'." % name
                )
                return
            except models.Projection.DoesNotExist:
                raise CommandError("No projection with name '%s' found." % name)

        # continue with defining a new projection by checking command arguments
        if len(args) != 1:
            raise CommandError("Invalid projection specification.")

        definition = args[0]
        frmt = kwargs["frmt"]

        sr = osr.SpatialReference()
        methods = {
            "XML": sr.ImportFromXML,
            "WKT": sr.ImportFromWkt,
            "PROJ": sr.ImportFromProj4,
            "URL": sr.ImportFromUrl
        }

        # if no format is explicitly specified, loop over all possible formats
        # and deduct the format from the input
        if frmt is None:
            for frmt, importer in methods.items():
                try:
                    importer(definition)
                    break
                except RuntimeError:
                    pass
            else:
                raise CommandError(
                    "Could not deduct projection definition format."
                )

        # validate the projection definition
        try:
            methods[frmt.upper()](definition)
        except RuntimeError as e:
            raise CommandError(
                "Could not parse projection definition, error was: %s" % e
            )
        except KeyError:
            raise CommandError("Unsupported projection format '%s'." % frmt)

        # actually insert a new projection definition
        try:
            projection = models.Projection(
                name=name, format=frmt.upper(), definition=definition
            )
            projection.full_clean()
            projection.save()
        except ValidationError as e:
            raise CommandError(
                "Error inserting new projection definition: %s"
                % ". ".join(
                    "%s: %s" % (key, ", ".join(values))
                    for key, values in e.message_dict.items()
                )
            )
        except IntegrityError:
            raise CommandError(
                "A projection with the name '%s' already exists" % name
            )

        self.print_msg(
            "Successfully defined projection '%s' with format '%s'."
            % (name, frmt)
        )
