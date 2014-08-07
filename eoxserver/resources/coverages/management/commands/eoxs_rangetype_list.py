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

import sys
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eoxserver.resources.coverages.rangetype import getAllRangeTypeNames
from eoxserver.resources.coverages.rangetype import isRangeTypeName
from eoxserver.resources.coverages.rangetype import getRangeType
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--json',
            dest='json_dump',
            action='store_true',
            default=False,
            help=("Optional. Dump rangetype(s) in JSON format. The JSON "
                  "dump can be loaded by another EOxServer instance.")
        ),
        make_option('-o', '--output',
            dest='filename',
            action='store', type='string',
            default='-',
            help=("Optional. Write output to a file rather than to the default"
                  " standard output.")
        ),
    )

    args = "[<rt-id> [<rt-id> ...]]"

    help = (
    """
    Print list of registered range-types.  The output and its format can be
    controlled.  By default, the program dupms a simple list of range-types'
    identifiers.
    If the range-type identifiers are specified than only these rangetypes
    are filtered.  In addition, complete rangetype definitions cans be dumped
    in the JSON format.  The JSON output can be directly loaded by another
    EOxServer instance.

    NOTE: JSON format of the range-types has slightly changed with the new
          range-type data model introduced in the EOxServer version v0.4.
          The produced JSON is not backward comatible and cannot be loaded
          to EOxServer 0.3.* and earlier.
    """
    )


    def handle(self, *args, **options):
        print_json = bool(options.get('json_dump', False))
        filename = options.get('filename', '-')
        rt_list = args # list of range-type identifiers

        if not rt_list:
            # if no range-type name specified get all of them
            rt_list = getAllRangeTypeNames()

        else:
            # filter existing range-type names
            def __checkRangeType(rt):
                rv = isRangeTypeName(rt)
                if not rv:
                    self.print_err("Invalid range-type identifier '%s' !"%rt)
                return rv
            rt_list = [rt for rt in rt_list if __checkRangeType(rt)]

        # select the right output format
        if print_json:
            output = OutputJSON
        else:
            output = OutputBrief

        def _write_out(fout):
            """ Write the output."""
            fout.write(output.lead())
            for i, rt_name in enumerate(rt_list):
                if i > 0:
                    fout.write(output.separator())
                fout.write(output.object(rt_name))
            fout.write(output.trail())

        try:
            if filename == "-":
                _write_out(sys.stdout)
            else:
                with open(filename, "w") as fout:
                    _write_out(fout)

        except IOError as exc:
            raise CommandError("Failed to write to file '%s'!"
                                " REASON: %s" % (filename, str(exc)))


class BaseOutput(object):
    """ base output class """
    @staticmethod
    def lead():
        return ""

    @staticmethod
    def object(rt_name):
        raise NotImplementedError

    @staticmethod
    def trail():
        return ""

    @staticmethod
    def separator():
        return ""


class OutputBrief(BaseOutput):
    """ brief text output - RT name only """
    @staticmethod
    def object(rt_name):
        return rt_name

    @staticmethod
    def separator():
        return "\n"

    @staticmethod
    def trail():
        return "\n"


class OutputJSON(BaseOutput):
    """ JSON output """
    @staticmethod
    def lead():
        return "["

    @staticmethod
    def trail():
        return "]\n"

    @staticmethod
    def separator():
        return ",\n"

    @staticmethod
    def object(rt_name):
        # get rangetype as a dict and dump the json
        return json.dumps(getRangeType(rt_name), indent=4,
                        separators=(',', ': '), sort_keys=True)


