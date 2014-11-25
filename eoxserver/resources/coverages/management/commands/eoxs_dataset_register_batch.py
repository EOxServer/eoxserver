#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from optparse import make_option
import csv

from django.core.management import call_command
from django.core.management.base import CommandError, BaseCommand
from django.db import transaction

from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)


class Command(CommandOutputMixIn, BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("--delimiter", dest="delimiter",
            action="store", default=",",
            help=("Optional. The delimiter to use for the input files. "
                  "Defaults to ','.")
        ),
        make_option("--header", dest="header",
            action="store", default=None,
            help=("Optional. A comma separated list of header values. "
                  "By default the first line of each input file is used as "
                  "header. Valid header fields are 'identifier', 'data', "
                  "'metadata', 'range_type_name', 'extent', 'size', 'srid', "
                  "'projection', 'footprint', 'begin_time', 'end_time', "
                  "'coverage_type', 'visible', 'collection' and "
                  "'ignore_missing_collection'. See the "
                  "'eoxs_dataset_register' command for details.")
        ),
        make_option("--on-error", dest="on_error",
            type="choice", action="store",
            choices=["rollback", "ignore", "stop"], default="rollback",
            help="Optional. Decides what shall be done in case of an error."
        )
    )

    args = (
        "input-file-1.csv [input-file-2.csv] [...] "
        "[--header header-field-A,header-field-B,...] "
        "[--delimiter ; ] "
        "[--on-error rollback|ignore|stop ] "
    )

    help = """
        Starts a batch registration of datasets.

        A batch registration iterates over one or more CSV files and starts a
        registration for each line. The meaning of each line is specified by
        either the actual file header line or a given '--header'.

        For parameters that can be used multiple times, such as 'data' or
        'metadata' or 'collection' a uniqe suffix must be used for each column.
        E.g: 'data-1','data-2'.
    """

    @nested_commit_on_success
    def handle(self, *args, **kwargs):
        if not args:
            raise CommandError("Missing input files.")

        delimiter = kwargs["delimiter"]
        header = kwargs["header"]
        if header:
            header = header.split(",")

        for filename in args:
            with open(filename) as f:
                self.print_msg("Processing batch file '%s'." % filename)
                reader = csv.DictReader(
                    f, fieldnames=header, delimiter=delimiter
                )
                self.handle_file(reader, kwargs)
                self.print_msg(
                    "Finished processing batch file '%s'." % filename
                )

    def handle_file(self, reader, kwargs):
        sid = None
        on_error = kwargs["on_error"]

        for row in reader:
            if on_error != "rollback":
                sid = transaction.savepoint()
            try:
                call_command("eoxs_dataset_register",
                    **self._translate_params(row)
                )
                if sid:
                    transaction.savepoint_commit(sid)
            except:
                transaction.savepoint_rollback(sid)
                if on_error == "ignore":
                    continue
                elif on_error == "stop":
                    transaction.commit()
                raise

    def _translate_params(self, params):
        out = {}
        for key, value in params.items():
            if key in SIMPLE_PARAMS:
                out[key] = value
            elif key in BOOLEAN_PARAMS:
                out[key] = (value.lower() in TRUTHY)

            elif key.startswith("data"):
                out.setdefault("data", []).append(value.split())
            elif key.startswith("metadata"):
                out.setdefault("metadata", []).append(value.split())

            elif key.startswith("collection"):
                out.setdefault("collection_ids", []).append(value)
            elif key.startswith("semantic"):
                out.setdefault("semantics", []).append(value)
            else:
                raise CommandError("Invalid header field '%s'." % key)

        return out


SIMPLE_PARAMS = set((
    "identifier", "range_type_name", "extent",
    "size", "srid", "projection", "begin_time", "end_time",
    "coverage_type"
))
BOOLEAN_PARAMS = set((
    "visible", "ignore_missing_collection", "replace"
))
TRUTHY = set(("true", "1", "yes", "t", "y"))
