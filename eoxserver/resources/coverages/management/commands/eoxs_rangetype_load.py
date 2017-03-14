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
from eoxserver.contrib.gdal import NAME_TO_GDT, NAME_TO_GCI
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success,
)
from eoxserver.resources.coverages.models import (
    RangeType, Band, NilValueSet, NilValue,
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-i', '--input', dest='filename', action='store', type='string',
            default='-', help=(
                "Optional. Read input from a file rather than from the "
                "default standard input."
            )
        ),
        make_option(
            '-u', '--update', dest='update', action='store_true', default=False,
            help=(
                "Optional. Update the existing range-types. By default the "
                "range type updates are not allowed."
            )
        ),
    )

    help = """
    Load range-types stored in JSON format from standard input (default) or from
    a file (-i option).

    NOTE: This command supports JSON formats produced by both the new
          (>=v0.4) and old (<0.4) versions of EOxServer.
          It is thus possible to export range-types from an older EOxServer
          instances and import them to a new one.
    """

    def _error(self, rt_name, message):
        self.print_err(
            "Failed to register range-type '%s'! %s" % (rt_name, message)
        )

    def handle(self, *args, **options):
        # Collect parameters
        self.traceback = bool(options.get("traceback", False))
        self.verbosity = int(options.get('verbosity', 1))
        filename = options.get('filename', '-')
        update = options.get('update', False)


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
                    if update:
                        # update the existing range-type object
                        update_range_type_from_dict(range_type)
                        self.print_msg("Range type '%s' updated." % rt_name)
                    else:
                        # update is not allowed
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


@nested_commit_on_success
def create_range_type_from_dict(range_type_dict):
    """ Create new range-type from a JSON serializable dictionary.
    """
    range_type = RangeType.objects.create(name=range_type_dict['name'])

    # compatibility with the old range-type JSON format
    global_data_type = range_type_dict.get('data_type', None)

    for idx, band_dict in enumerate(range_type_dict['bands']):
        _create_band_from_dict(band_dict, idx, range_type, global_data_type)

    return range_type


@nested_commit_on_success
def update_range_type_from_dict(range_type_dict):
    """ Create new range-type from a JSON serializable dictionary.
    """
    range_type = RangeType.objects.get(name=range_type_dict['name'])

    # remove all current bands
    range_type.bands.all().delete()

    # compatibility with the old range-type JSON format
    global_data_type = range_type_dict.get('data_type', None)

    for idx, band_dict in enumerate(range_type_dict['bands']):
        _create_band_from_dict(band_dict, idx, range_type, global_data_type)

    return range_type


def _create_band_from_dict(band_dict, index, range_type, global_data_type=None):
    """ Create new range-type from a JSON serializable dictionary.
    """
    # compatibility with the old range-type JSON format
    data_type = global_data_type if global_data_type else band_dict['data_type']
    color_interpretation = band_dict[
        'gdal_interpretation' if 'gdal_interpretation' in band_dict else
        'color_interpretation'
    ]

    # convert strings to GDAL codes
    data_type_code = NAME_TO_GDT[data_type.lower()]
    color_interpretation_code = NAME_TO_GCI[color_interpretation.lower()]

    # prepare nil-value set
    if band_dict['nil_values']:
        nil_value_set = NilValueSet.objects.create(
            name="__%s_%2.2d__" % (range_type.name, index),
            data_type=data_type_code
        )

        for nil_value in band_dict['nil_values']:
            NilValue.objects.create(
                reason=nil_value['reason'],
                raw_value=str(nil_value['value']),
                nil_value_set=nil_value_set,
            )
    else:
        nil_value_set = None

    return Band.objects.create(
        index=index,
        name=band_dict['name'],
        identifier=band_dict['identifier'],
        data_type=data_type_code,
        description=band_dict['description'],
        definition=band_dict['definition'],
        uom=band_dict['uom'],
        color_interpretation=color_interpretation_code,
        range_type=range_type,
        nil_value_set=nil_value_set,
        raw_value_min=band_dict.get("value_min"),
        raw_value_max=band_dict.get("value_max")
    )
