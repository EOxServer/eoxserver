#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from sys import stdin
import traceback
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.resources.coverages.models import RangeType
from eoxserver.resources.coverages.rangetype import (
    create_range_type_from_dict,
)


class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '-i', '--input',
            dest='filename',
            action='store', type='string',
            default='-',
            help=("Optional. Read input from a file rather than from the "
                  "default standard input.")
        ),
    )

    help = """
    Load rangetypes stored in JSON format from standard input (default) or from
    a file (-i option).

    NOTE: This command supports JSON formats produced by both the new
          (>=v0.4) and old (<0.4) versions of EOxServer.
          It is thus possible to export rangetypes from an older EOxServer
          instances and import them to a new one.
    """

    def _error(self, rt_name, message):
        self.print_err(
            "Failed to register rangetype '%s'! %s" % (rt_name, message)
        )

    def handle(self, *args, **options):
        # Collect parameters
        self.traceback = bool(options.get("traceback", False))
        self.verbosity = int(options.get('verbosity', 1))
        filename = options.get('filename', '-')


        self.print_msg("Importing range type from %s ..." % (
            "standard input" if filename == "-" else "file %r" % filename
        ))

        # load and parse the input data
        try:
            with (stdin if filename == "-" else open(filename, "r")) as fin:
                range_types = json.load(fin)
        except IOError as exc:
            raise CommandError(
                "Failed to open the input file '%s'! %s " % (filename, str(exc))
            )

        # allow single range-type objects
        if isinstance(range_types, dict):
            range_types = [range_types]

        # insert the range types to DB

        success_count = 0  # success counter - counts finished syncs

        for idx, range_type in enumerate(range_types):

            # check range-type name
            rt_name = range_type.get('name', None)
            if not isinstance(rt_name, basestring) or not rt_name:
                self.print_err(
                    "Range type #%d rejected as it has no valid name." %
                    (idx + 1)
                )
                continue

            try:
                if RangeType.objects.filter(name=rt_name).exists():
                    self.print_err(
                        "The name '%s' is already used by another "
                        "range type! Import of range type #%d aborted!" %
                        (rt_name, (idx + 1))
                    )
                    continue

                else:
                    # create new range-type object
                    create_range_type_from_dict(range_type)
                    self.print_msg("Range type '%s' loaded." % rt_name)

            except Exception as exc:
                if self.traceback:
                    self.print_msg(traceback.format_exc())
                self._error(rt_name, "%s: %s" % (type(exc).__name__, str(exc)))
                continue

            else:
                success_count += 1  # increment success counter

        # print the final summary
        count = len(range_types)
        error_count = count - success_count

        if error_count > 0:
            self.print_msg("Failed to load %d range types." % error_count, 1)

        if success_count > 0:
            self.print_msg(
                "Successfully loaded %d of %s range types." %
                (success_count, count), 1
            )
        else:
            self.print_msg("No range type loaded.")
