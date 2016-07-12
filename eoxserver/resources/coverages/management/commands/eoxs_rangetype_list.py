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
# pylint: disable=missing-docstring

from sys import stdout
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from eoxserver.resources.coverages.rangetype import (
    getAllRangeTypeNames, isRangeTypeName, getRangeType
)
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn


class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--details', dest='details', action='store_true', default=False,
            help="Optional. Print details of the reangetypes."
        ),
        make_option(
            '--json', dest='json_dump', action='store_true', default=False,
            help=(
                "Optional. Dump rangetype(s) in JSON format. This JSON "
                "dump can be loaded by another instance of EOxServer."
            )
        ),
        make_option(
            '-o', '--output', dest='filename', action='store', type='string',
            default='-', help=(
                "Optional. Write output to a file rather than to the default"
                " standard output."
            )
        ),
    )

    args = "[<rt-id> [<rt-id> ...]]"

    help = """
    Print either list of all rangetype indentifiers and their details.
    When the range-type identifiers are specified than only these rangetypes
    are selected. In addition complete rangetypes cans be dumped in JSON
    format which can be then loaded by another EOxServer instance.

    NOTE: JSON format of the range-types has slightly changed with the new
          range-type data model introduced in the EOxServer version v0.4.
          The produced JSON is not backward comatible and cannot be loaded
          to EOxServer 0.3.* and earlier.
    """


    def handle(self, *args, **options):
        # collect input parameters
        self.verbosity = int(options.get('verbosity', 1))
        print_details = bool(options.get('details', False))
        print_json = bool(options.get('json_dump', False))
        filename = options.get('filename', '-')
        range_types = args

        # check the input range-type names

        if not range_types:
            # if no identifier is specified get all identifiers
            range_types = getAllRangeTypeNames()

        else:
            # filter existing range-type names
            def _is_range_type(rt_name):
                flag = isRangeTypeName(rt_name)
                if not flag:
                    self.print_err(
                        "Invalid range-type identifier '%s' !" % rt_name
                    )
                return flag

            range_types = (rt for rt in range_types if _is_range_type(rt))

        # select the right output formatter
        if print_json:
            output_formatter = OutputJSON
        elif print_details:
            output_formatter = OutputDetailed
        else:
            output_formatter = OutputBrief

        # write the output
        try:
            with (stdout if filename == "-" else open(filename, "w")) as fout:
                fout.write(output_formatter.lead())
                for idx, rt_name in enumerate(range_types):
                    if idx > 0:
                        fout.write(output_formatter.separator())
                    fout.write(output_formatter.object(rt_name))
                fout.write(output_formatter.trail())
        except IOError as exc:
            raise CommandError(
                "Failed to write the output file %r! %s" % (filename, str(exc))
            )


# output formatters ...

class OutputBase(object):
    """ base output formatter class class """

    @classmethod
    def lead(cls):
        return ""

    @classmethod
    def object(cls, name):
        return name

    @classmethod
    def trail(cls):
        return ""

    @classmethod
    def separator(cls):
        return ", "


class OutputBrief(OutputBase):
    """ brief text output - RT name only """

    @classmethod

    def separator(cls):
        return "\n"

    @classmethod
    def trail(cls):
        return "\n"


class OutputDetailed(OutputBase):
    """ detailed text output """

    @classmethod
    def lead(cls):
        return "\n"

    @classmethod
    def trail(cls):
        return "\n\n"

    @classmethod
    def separator(cls):
        return "\n\n"

    @classmethod
    def object(cls, name):

        def _output_(range_type):
            bands = range_type['bands']
            yield "%s (%d band%s)" % (
                range_type['name'], len(bands), "s" if len(bands) != 1 else ""
            )
            for band in bands:
                yield "    %-8s %s" % (band['data_type'], band['identifier'])

        return "\n".join(_output_(getRangeType(name)))


class OutputJSON(OutputBase):
    """ JSON output """

    @classmethod
    def lead(cls):
        return "["

    @classmethod
    def trail(cls):
        return "]\n"

    @classmethod
    def separator(cls):
        return ",\n"

    @classmethod
    def object(cls, name):
        # get range-type as dictionary and dump the JSON
        return json.dumps(
            getRangeType(name), indent=4, separators=(',', ': '), sort_keys=True
        )
