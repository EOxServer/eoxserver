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
from eoxserver.contrib.gdal import GDT_TO_NAME
from eoxserver.resources.coverages.models import RangeType
from eoxserver.resources.coverages.rangetype import (
    range_type_to_dict,
)
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn

JSON_OPTIONS = {
    "indent": 4,
    "separators": (',', ': '),
    "sort_keys": True,
}


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

        # get the range types
        if args:
            range_types = RangeType.objects.filter(name__in=args)
        else:
            range_types = RangeType.objects.all()

        # select the right output formatter
        if print_json:
            output_formatter = output_json
        elif print_details:
            output_formatter = output_detailed
        else:
            output_formatter = output_brief

        # write the output
        try:
            with (stdout if filename == "-" else open(filename, "w")) as fout:
                for item in output_formatter(range_types):
                    fout.write(item)
        except IOError as exc:
            raise CommandError(
                "Failed to write the output file %r! %s" % (filename, str(exc))
            )


# output formatters ...

def output_brief(range_types):
    """ Brief range-type name output. """
    for range_type in range_types:
        yield "%s\n" % range_type.name


def output_detailed(range_types):
    """ Detailed range-type output (includes brief bands' info). """
    for range_type in range_types:
        name = range_type.name
        bands = list(range_type.bands.all())
        nbands = len(bands)
        yield "%s (%d band%s)\n" % (name, nbands, "" if nbands == 1 else "s")
        for band in bands:
            data_type = GDT_TO_NAME.get(band.data_type, 'Invalid')
            yield "    %-8s %s\n" % (data_type, band.identifier)
        yield "\n"

def output_json(range_types):
    """ Full JSON range-type dump. """
    range_types = iter(range_types)
    yield '['
    try:
        yield json.dumps(range_type_to_dict(range_types.next()), **JSON_OPTIONS)
    except StopIteration:
        pass
    for range_type in range_types:
        yield ',\n'
        yield json.dumps(range_type_to_dict(range_type), **JSON_OPTIONS)
    yield ']\n'
