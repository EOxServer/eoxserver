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

from sys import stdin
import traceback
import json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.utils.six import string_types
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success,
)
from eoxserver.resources.coverages.models import Coverage
from eoxserver.services.models import WMSRenderOptions


class Command(CommandOutputMixIn, BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '-i', '--input', dest='filename', action='store', type='string',
            default='-', help=(
                "Optional. Read input from a file rather than from the "
                "default standard input."
            )
        ),
    )

    help = """
    Load WMS options stored in JSON format from standard input (default) or from
    a file (-i option).
    """

    def handle(self, *args, **options):
        # Collect parameters
        self.traceback = bool(options.get("traceback", False))
        self.verbosity = int(options.get('verbosity', 1))
        filename = options.get('filename', '-')

        self.print_msg("Importing WMS options from %s ..." % (
            "standard input" if filename == "-" else "file %r" % filename
        ))

        # load and parse the input data
        try:
            with (stdin if filename == "-" else open(filename, "r")) as fin:
                wms_opts = json.load(fin)
        except IOError as exc:
            raise CommandError(
                "Failed to open the input file '%s'! %s " % (filename, str(exc))
            )

        # insert the range types to DB

        success_count = 0  # success counter - counts finished syncs

        for wms_opt in wms_opts:
            try:
                eoid = wms_opt['coverage_identifier']
                insert_or_update_wms_opt(eoid, wms_opt)
            except Exception as exc:
                if self.traceback:
                    self.print_msg(traceback.format_exc())
                self.print_err("Failed to load options of %s! %s" % (
                    eoid, "%s: %s" % (type(exc).__name__, str(exc))
                ))
                continue
            else:
                success_count += 1  # increment success counter

        # print the final summary
        count = len(wms_opts)
        error_count = count - success_count

        if success_count > 0:
            self.print_msg(
                "Successfully loaded %d of %s WMS option records." %
                (success_count, count), 1
            )
        else:
            self.print_msg("No WMS option record loaded.")

        if error_count > 0:
            raise CommandError(
                "Failed to load %d WMS option records." % error_count
            )


@nested_commit_on_success
def insert_or_update_wms_opt(eoid, wms_opt):
    """ Insert or update one WMS option record. """
    try:
        # try to get an existing object
        wms_opt_obj = WMSRenderOptions.objects.get(coverage__identifier=eoid)
    except WMSRenderOptions.DoesNotExist:
        try:
            # locate the related coverage
            coverage = Coverage.objects.get(identifier=eoid)
        except Coverage.DoesNotExist:
            raise CommandError("Invalid coverage identifier %s!" % eoid)
        # create a new object
        wms_opt_obj = WMSRenderOptions(coverage=coverage)

    # set the record
    set_from_dict(wms_opt_obj, wms_opt).save()


def set_from_dict(wms_opt_obj, options):
    """ Set object from a JSON serializable dictionary. """

    _int = lambda v: v if v is None else int(v)

    wms_opt_obj.default_red = _int(options.get('red', None))
    wms_opt_obj.default_green = _int(options.get('green', None))
    wms_opt_obj.default_blue = _int(options.get('blue', None))
    wms_opt_obj.default_alpha = _int(options.get('alpha', None))
    wms_opt_obj.resampling = options.get('resampling', None)
    wms_opt_obj.scale_auto = options.get('scale_auto', False)
    wms_opt_obj.scale_min = _int(options.get('scale_min', None))
    wms_opt_obj.scale_max = _int(options.get('scale_max', None))

    def _scales(scales):
        if scales is None:
            return None
        if isinstance(scales, string_types):
            scales = scales.split(',')
        return ",".join(str(int(round(float(v)))) for v in scales)

    wms_opt_obj.bands_scale_min = _scales(options.get('bands_scale_min', None))
    wms_opt_obj.bands_scale_max = _scales(options.get('bands_scale_max', None))

    return wms_opt_obj
