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


from os.path import join, isfile, dirname, abspath
import sys
from ctypes.util import find_library

from django.core.management import call_command

import eoxserver


def create_instance(instance_id, target=None, init_spatialite=False,
                    verbosity=None, traceback=False):
    """ Creates a new EOxServer instance with all necessary files and
        folder structure. Optionally, a SQLite database is initiated.
    """
    # Locate instance template
    instance_template_dir = join(
        dirname(eoxserver.__file__), "instance_template"
    )
    if not isfile(join(instance_template_dir, "manage.py")):
        instance_template_dir = join(sys.prefix, "eoxserver/instance_template")
        if not isfile(join(instance_template_dir,  "manage.py")):
            raise RuntimeError("Error: EOxServer instance template not found.")

    # Add template and extension to options
    options = {
        'template': instance_template_dir,
        'extensions': ["conf", "py"],
        'verbosity': verbosity,
        'traceback': traceback
    }

    args = [instance_id]
    if target is not None:
        args.append(target)

    # create the initial django folder structure
    print("Initializing django project folder.")
    call_command("startproject", *args, **options)

    if init_spatialite:
        _init_spatialite(instance_id, target)


def _init_spatialite(instance_id, target):
    # initialize the spatialite database file
    if target is None:
        dst_data_dir = join(instance_id, instance_id, "data")
        print(dst_data_dir)
    else:
        dst_data_dir = join(abspath(target), instance_id, "data")

    db_name = join(dst_data_dir, "config.sqlite")
    print("Setting up initial database.")
    try:
        from pyspatialite import dbapi2 as db
        conn = db.connect(db_name)
        print("Using pyspatialite.")
    except ImportError:
        try:
            from pysqlite2 import dbapi2 as db
            print("Using pysqlite.")
        except ImportError:
            from sqlite3 import dbapi2 as db
            print("Using sqlite3.")

        conn = db.connect(db_name)
        try:
            conn.enable_load_extension(True)
        except:
            raise Exception(
                "SQLite API does not allow loading of extensions."
            )

        spatialite_lib = find_library('spatialite')
        try:
            print("Trying to load extension module '%s'." % spatialite_lib)
            conn.execute("SELECT load_extension('%s')" % (spatialite_lib,))
        except Exception as msg:
            raise Exception(
                'Unable to load the SpatiaLite library extension '
                '"%s" because: %s' % (spatialite_lib, msg)
            )

    rs = conn.execute('SELECT spatialite_version()')
    rs = rs.fetchone()[0].split(".")
    if (int(rs[0]), int(rs[1])) >= (2, 4):
        print("SpatiaLite found, initializing using "
              "'InitSpatialMetadata()'.")
        # Since spatialite 4.1, InitSpatialMetadata() is not longer run
        # automatically in a transaction. It has to be triggered
        # explicitly.
        if (int(rs[0]), int(rs[1])) >= (4, 1):
            conn.execute("SELECT InitSpatialMetadata(1)")
        else:
            conn.execute("SELECT InitSpatialMetadata()")
    else:
        print("SpatiaLite version <2.4 found, trying to "
              "initialize using 'init_spatialite-2.3.sql'.")
        init_sql_path = "init_spatialite-2.3.sql"
        with open(init_sql_path, 'r') as init_sql_file:
            conn.executescript(init_sql_file.read())
    conn.commit()
    conn.close()
