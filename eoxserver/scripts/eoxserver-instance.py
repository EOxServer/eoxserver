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
from optparse import OptionParser
import textwrap

from django.core.management.base import OutputWrapper
from django.core.management.color import color_style

import eoxserver
from eoxserver.core.instance import create_instance


def main():
    parser = OptionParser(
        usage=textwrap.dedent("""\
            %prog [options] <instance-name> [<target-directory>]

            Creates a new EOxServer instance with all necessary files and
            folder structure. Optionally, a SQLite database is initiated.
        """),
        version=eoxserver.get_version()
    )
    parser.add_option('-i', '--init-spatialite', '--init_spatialite',
        dest='init_spatialite', action='store_true', default=False,
        help='Flag to initialize the sqlite database.'
    )
    parser.add_option('-v', '--verbosity',
        action='store', dest='verbosity', default='1',
        type='choice', choices=['0', '1', '2', '3']
    )
    parser.add_option('--traceback',
        action='store_true', help='Raise on exception'
    )

    options, args = parser.parse_args()

    error_stream = OutputWrapper(sys.stderr, color_style().ERROR)

    if not args:
        error_stream.write("Mandatory argument 'instance-name' not given.\n")
        sys.exit(1)

    name = args[0]
    try:
        target = args[1]
    except IndexError:
        target = None

    try:
        options = options.__dict__
        options['verbosity'] = int(options['verbosity'])
        create_instance(name, target, **options)
    except Exception as e:
        if options.traceback:
            raise
        error_stream.write("%s: %s\n" % (e.__class__.__name__, e))

if __name__ == "__main__":
    main()
