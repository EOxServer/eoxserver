#!/usr/bin/python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


"""
Create a new EOxServer instance. This instance will create a root directory
with the instance name in the given (optional) directory.
"""

import sys
from argparse import ArgumentParser
import textwrap

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style

import eoxserver
from eoxserver.core.instance import create_instance


def main():

    parser = ArgumentParser(
        description=(
            "Create a new EOxServer instance with all necessary files and "
            "folder structure. Optionally, a new SQLite database is initiated."
        ),
    )
    parser.add_argument("instance-name")
    parser.add_argument("target-directory", nargs="?")
    parser.add_argument(
        '-i', '--init-spatialite', dest='init_spatialite',
        action='store_true', default=False,
        help='Flag to initialize the sqlite database.'
    )
    parser.add_argument(
        '-v', '--verbosity', dest='verbosity', type=int, choices=[0, 1, 2, 3],
        default=1,
    )
    parser.add_argument(
        '--traceback', action='store_true', help='Raise on exception'
    )

    options = vars(parser.parse_args())
    name = options.pop('instance-name')
    target = options.pop('target-directory')

    try:
        create_instance(name, target, **options)
    except Exception as error:
        if options['traceback']:
            raise
        error_stream = OutputWrapper(sys.stderr, color_style().ERROR)
        error_stream.write("%s: %s\n" % (error.__class__.__name__, error))

if __name__ == "__main__":
    main()
