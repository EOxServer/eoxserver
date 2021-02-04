#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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
try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict
from django.utils.six import string_types
from django.core.management.base import BaseCommand, CommandError
from eoxserver.resources.coverages.management.commands import CommandOutputMixIn
from eoxserver.services.models import WMSRenderOptions

JSON_OPTIONS = {
    "indent": None,
    "separators": (', ', ': '),
    "sort_keys": False,
}

class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
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

    args = "[<eo-id> [<eo-id> ...]]"

    help = """
    Print WMS options for listed coverages or all coverages. If the coverage
    does not exist or if it exists but it has WMS option record no options
    are printed.
    """

    def handle(self, *args, **options):
        # collect input parameters
        self.verbosity = int(options.get('verbosity', 1))
        print_json = bool(options.get('json_dump', False))
        filename = options.get('filename', '-')

        # get the range types
        wms_opts = WMSRenderOptions.objects.select_related('coverage')
        if args:
            wms_opts = wms_opts.filter(coverage__identifier__in=args)
        else:
            wms_opts = wms_opts.all()

        # select the right output formatter
        if print_json:
            output_formatter = output_json
        else:
            output_formatter = output_detailed

        # write the output
        try:
            with (stdout if filename == "-" else open(filename, "w")) as fout:
                for item in output_formatter(wms_opts):
                    fout.write(item)
        except IOError as exc:
            raise CommandError(
                "Failed to write the output file %r! %s" % (filename, str(exc))
            )


def output_detailed(wms_opts):
    """ Detailed range-type output (includes brief bands' info). """
    for wms_opt in wms_opts:
        yield "%s\n" % wms_opt.coverage.identifier
        for key, val in wms_opt_to_dict(wms_opt).items():
            if hasattr(val, '__len__') and not isinstance(val, string_types):
                val = ",".join(str(v) for v in val)
            if key == "coverage_identifier":
                continue
            if key == "scale_auto" and not val:
                continue
            yield "    %s: %s\n" % (key, val)
        yield "\n"


def output_json(wms_opts):
    """ Full JSON range-type dump. """
    yield '['
    delimiter = ''
    for wms_opt in wms_opts:
        yield delimiter
        yield json.dumps(wms_opt_to_dict(wms_opt), **JSON_OPTIONS)
        delimiter = ',\n'
    yield ']\n'


def wms_opt_to_dict(wms_opt):
    """ Dump objects object to a JSON serializable dictionary. """
    options = OrderedDict()
    options['coverage_identifier'] = wms_opt.coverage.identifier
    if wms_opt.default_red is not None:
        options['red'] = wms_opt.default_red
    if wms_opt.default_green is not None:
        options['green'] = wms_opt.default_green
    if wms_opt.default_blue is not None:
        options['blue'] = wms_opt.default_blue
    if wms_opt.default_alpha is not None:
        options['alpha'] = wms_opt.default_alpha
    if wms_opt.resampling is not None:
        options['resampling'] = wms_opt.resampling
    if wms_opt.scale_auto:
        options['scale_auto'] = wms_opt.scale_auto
    if wms_opt.scale_min is not None:
        options['scale_min'] = wms_opt.scale_min
    if wms_opt.scale_max is not None:
        options['scale_max'] = wms_opt.scale_max
    if wms_opt.bands_scale_min is not None:
        options['bands_scale_min'] = [
            int(v) for v in wms_opt.bands_scale_min.split(',')
        ]
    if wms_opt.bands_scale_max is not None:
        options['bands_scale_max'] = [
            int(v) for v in wms_opt.bands_scale_max.split(',')
        ]
    return options
