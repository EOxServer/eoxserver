#!/usr/bin/env python
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""
Create a new EOxServer instance. This instance will create a root directory
with the instance name in the given (optional) directory.
"""

from optparse import make_option

from django.core.management.base import CommandError

from eoxserver.core.management import EOxServerAdminCommand
from eoxserver.core.instance import create_instance


class Command(EOxServerAdminCommand):
    def add_arguments(self, parser):
        parser.add_argument('instance_id',
            metavar='INSTANCE_ID', nargs=1,
            help='The instance idnetifier.'
        )
        parser.add_argument('target',
            metavar='DEST_DIRECTORY', nargs='?',
            help='Optional. The destination directory.'
        )
        parser.add_argument('--init_spatialite', '--init-spatialite',
            action='store_true', help='Flag to initialize the sqlite database.'
        )

    args = "INSTANCE_ID [Optional destination directory] [--init-spatialite]"
    help = ("Creates a new EOxServer instance with all necessary files and "
            "folder structure. Optionally, a SQLite database is initiated")

    def handle(self, instance_id, target=None, *args, **options):
        if not instance_id:
            raise CommandError("Instance ID not given.")

        init_spatialite = options["init_spatialite"]
        verbosity = options["verbosity"]
        traceback = options.get("traceback")

        create_instance(
            instance_id[0], target, init_spatialite, verbosity, traceback
        )
