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

from django.core.management.base import BaseCommand
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn,
)
from eoxserver.services.management.commands.wms_options_load import (
    insert_or_update_wms_opt,
)


class Command(CommandOutputMixIn, BaseCommand):

    help = """
    Set WMS options for a coverage.

    NOTE: Band indices are counted from 1.
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("coverage-id")
        parser.add_argument(
            "-i", "--identifier", "--coverage-id", dest="identifier",
            default=None,
            help="Mandatory coverage identifier."
        )
        parser.add_argument(
            "-r", "--red", dest="red", default=None,
            help="Band index of the red channel."
        )
        parser.add_argument(
            "-g", "--green", dest="green", default=None,
            help="Band index of the green channel."
        )
        parser.add_argument(
            "-b", "--blue", dest="blue", default=None,
            help="Band index of the blue channel."
        )
        parser.add_argument(
            "-a", "--alpha", dest="alpha", default=None,
            help="Band index of the alpha channel."
        )
        parser.add_argument(
            "--grey", "--grey-scale", dest="red", default=None,
            help="Index of the band displayed as a grey-scale image."
        )
        parser.add_argument(
            "--resampling", dest="resampling",
            default=None, choices=["NEAREST", "AVERAGE", "BILINEAR"],
            help="Set image resampling method."
        )
        parser.add_argument(
            "--min", "--scale-min", dest="scale_min",
            default=None,
            help=(
                "Range scale minimum value. Use a comma separated list "
                "if each band has a different value."
            )
        )
        parser.add_argument(
            "--max", "--scale-max", dest="scale_max",
            default=None,
            help=(
                "Range scale minimum value. Use a comma separated list "
                "if each band has a different value."
            )
        )
        parser.add_argument(
            "--auto-scale", dest="scale_auto", action="store_true",
            default=False,
            help="Enable automatic range scaling."
        )
        parser.add_argument(
            "--no-auto-scale", dest="scale_auto", action="store_false",
            help="Disable automatic range scaling."
        )


    def handle(self, *args, **options):
        self.traceback = bool(options.get("traceback", False))
        self.verbosity = int(options.get('verbosity', 1))

        coverage_id = options["coverage-id"]

        keys = set((
            'red', 'green', 'blue', 'alpha', 'resampling', 'scale_auto'
        ))
        wms_opts = dict(
            (key, val) for key, val in options.items() if key in keys
        )

        if options['scale_min']:
            if ',' in options['scale_min']:
                wms_opts['bands_scale_min'] = options['scale_min']
            else:
                wms_opts['scale_min'] = options['scale_min']

        if options['scale_max']:
            if ',' in options['scale_max']:
                wms_opts['bands_scale_max'] = options['scale_max']
            else:
                wms_opts['scale_max'] = options['scale_max']

        # write the options
        insert_or_update_wms_opt(coverage_id, wms_opts)
