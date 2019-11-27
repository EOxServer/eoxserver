#-------------------------------------------------------------------------------
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

import csv
from django.core.management import call_command
from django.core.management.base import CommandError, BaseCommand
from django.db import transaction
from eoxserver.resources.coverages.management.commands import (
    CommandOutputMixIn, nested_commit_on_success
)

SIMPLE_PARAMS = set((
    "identifier", "range_type_name", "extent",
    "size", "srid", "projection", "begin_time", "end_time",
    "coverage_type"
))
BOOLEAN_PARAMS = set((
    "visible", "ignore_missing_collection", "replace"
))
TRUTHY = set(("true", "1", "yes", "t", "y"))


class Command(CommandOutputMixIn, BaseCommand):

    help = """
        Perform a batch registration of datasets.

        A batch registration iterates over one or more CSV files and performs
        registration for each dataset record. The meaning of each record field
        is defined by either the actual CSV file header or via the '--header'
        option.

        For parameters that can be used multiple times, such as 'data' or
        'metadata' or 'collection' a unique suffix must be used for each column.
        E.g: 'data-1','data-2'.
    """

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument("filename", nargs="+")
        parser.add_argument(
            "--delimiter", dest="delimiter", default=",", help=(
                "Optional. The delimiter to use for the input files. "
                "Defaults to ','."
            )
        )
        parser.add_argument(
            "--header", dest="header", help=(
                "Optional. A comma separated list of header values. "
                "By default the first line of each input file is used as "
                "header. Valid header fields are 'identifier', 'data', "
                "'metadata', 'range_type_name', 'extent', 'size', 'srid', "
                "'projection', 'footprint', 'begin_time', 'end_time', "
                "'coverage_type', 'visible', 'collection' and "
                "'ignore_missing_collection'. See the "
                "'eoxs_dataset_register' command for details."
            )
        )
        parser.add_argument(
            "--on-error", dest="on_error",
            choices=["rollback", "ignore", "stop"], default="rollback",
            help="Optional. Decides what shall be done in case of an error."
        )

    @nested_commit_on_success
    def handle(self, *args, **kwargs):

        filenames = kwargs['filename']
        delimiter = kwargs["delimiter"]
        header = kwargs["header"]
        if header:
            header = header.split(",")

        sum_successful = 0
        sum_failed = 0

        for filename in filenames:
            with open(filename) as file_:
                self.print_msg("Processing batch file '%s'." % filename)
                reader = csv.DictReader(
                    file_, fieldnames=header, delimiter=delimiter
                )
                successful, failed = self.handle_file(reader, filename, kwargs)
                self.print_msg(
                    "Finished processing batch file '%s'. Processed %d "
                    "datasets (%d successful, %d failed)" % (
                        filename, successful + failed, successful, failed
                    )
                )
                sum_successful += successful
                sum_failed += failed

        self.print_msg(
            "Finished processing %d batch file%s. Processed %d datasets "
            "(%d successful, %d failed)" % (
                len(filenames), "s" if len(filenames) > 1 else "",
                sum_successful + sum_failed, sum_successful, sum_failed
            )
        )

    def handle_file(self, reader, filename, kwargs):
        sid = None
        on_error = kwargs["on_error"]
        traceback = kwargs["traceback"]
        verbosity = kwargs["verbosity"]

        successful = 0
        failed = 0

        for i, row in enumerate(reader):
            params = self._translate_params(row)
            if on_error != "rollback":
                sid = transaction.savepoint()
            try:
                call_command(
                    "eoxs_dataset_register", traceback=traceback,
                    verbosity=verbosity, **params
                )
                if sid:
                    transaction.savepoint_commit(sid)
                successful += 1
            except BaseException:  # need to catch SystemExit aswell
                self.print_err(
                    "Failed to register line %d of file '%s." % (i, filename)
                )
                transaction.savepoint_rollback(sid)
                if on_error == "ignore":
                    failed += 1
                    continue
                elif on_error == "stop":
                    transaction.commit()
                raise

        return successful, failed

    @staticmethod
    def _translate_params(params):
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
