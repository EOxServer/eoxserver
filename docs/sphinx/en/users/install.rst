.. Installation
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2011 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a copy
  # of this software and associated documentation files (the "Software"), to
  # deal in the Software without restriction, including without limitation the
  # rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
  # sell copies of the Software, and to permit persons to whom the Software is
  # furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
  # IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

.. index::
    single: EOxServer Installation
    single: Installation

.. _Installation:

Installation
============

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Before you can use EOxServer, you’ll need to get it installed. Following this
guide will give you a simple, minimal though working installation.

A guide for the :ref:`CentOSInstallation` is also available.

.. index::
    single: EOxServer Dependencies
    single: Dependencies

.. _install_hw:

Hardware Requirements
---------------------

EOxServer has been deployed on a variety of different computers and virtual
machines with commonplace hardware configurations. The typical setup is:

* a dual-core or quad-core CPU
* 1 to 4 GB of RAM

The image processing operations required for certain OGC Web Service requests
(subsetting, reprojection, resampling) may be quite expensive in terms of
CPU load and memory consumption, so adding more RAM or an additional core (for
VMs) may increase the performance of the service. Bear in mind however, that
disk I/O speed is often a bottleneck.

EOxServer itself requires about 15 MB of disk space. Usually, the data
to be served has a magnitude of 10-100 GB or larger. So, this will be the
determining factor when choosing the appropriate disk size. Note that
for Rectified Stitched Mosaics, EOxServer will generate mosaic tiles from the
original data which requires additional disk space up to the space occupied by
the composing Rectified Datasets (depending on how much they overlap).

EOxServer itself does not have any GUI other than the Web Administration Client
and Web Map Client and thus no graphics support is required on the server.

Running (parts of) the Identity Management System (see :doc:`idm/index`) on the
same machine as EOxServer puts additional load on the server. Usually, running
the Tomcat server will require about 512 MB of RAM. Note that the different
components of the IDM may be deployed on different machines. The additional
network latency for checking a remote PDP on every incoming request may have a
considerable impact on the performance of the services (in particular WMS),
though, and thus it may be preferable to run the PDP on the same machine as
EOxServer.

Dependencies
------------

EOxServer depends on some external software. Table:
":ref:`table_eoxserver_dependencies`" below shows the minimal required software
to run EOxServer.

.. _table_eoxserver_dependencies:
.. table:: EOxServer Dependencies

    +-----------+------------------+-------------------------------------------+
    | Software  | Required Version | Description                               |
    +===========+==================+===========================================+
    | Python    | >= 2.5, < 3.0    | Scripting language                        |
    +-----------+------------------+-------------------------------------------+
    | Django    | >= 1.3           | Web development framework written in      |
    |           |                  | Python including the GeoDjango extension  |
    |           |                  | for geospatial database back-ends.        |
    +-----------+------------------+-------------------------------------------+
    | GDAL      | >= 1.8.0         | Geospatial Data Abstraction Library       |
    |           | (for rasdaman    | providing common interfaces for accessing |
    |           | support)         | various kinds of raster and vector data   |
    |           |                  | formats and including a Python binding    |
    |           |                  | which is used by EOxServer                |
    +-----------+------------------+-------------------------------------------+
    | MapServer | >= 6.0           | Server software implementing various OGC  |
    |           |                  | Web Service interfaces including WCS and  |
    |           |                  | WMS. Includes a Python binding which is   |
    |           |                  | used by EOxServer.                        |
    +-----------+------------------+-------------------------------------------+


EOxServer is written in `Python <http://www.python.org/>`_ and uses the
`Django <https://www.djangoproject.com>`_ framework which requires a
Python version from 2.4 to 2.7. Due to backwards incompatibilities in Python
3.0, Django and thus EOxServer does not currently work with Python 3.0.

EOxServer makes heavy usage of the `OSGeo <http://osgeo.org>`_ projects
`GDAL <http://www.gdal.org>`_ and `MapServer <http://mapserver.org>`_.

EOxServer also requires a database to store its internal data objects. Since it
is built on Django, EOxServer is mostly database agnostic, which means you can
choose from various database systems. Since EOxServer requires the database to
have geospatial enablement, the according extensions to that database have to
be installed. We suggest you use one of the following:

 * For testing environments or small amounts of data, the `SQLite
   <http://sqlite.org/>`_ database provides a lightweight and easy-to-use
   system.
 * However, if you'd like to work with a "large" database engine in an
   operational environment we recommend installing `PostgreSQL
   <http://www.postgresql.org/>`_.

For more and detailed information about database backends please refer to
`Django database notes <https://docs.djangoproject.com/en/1.3/ref/databases/>`_
and `GeoDjango installation
<https://docs.djangoproject.com/en/1.3/ref/contrib/gis/install/>`_.

.. _table_eoxserver_db_dependencies:
.. table:: Database Dependencies

    +------------+------------------+------------------------------------------+
    | Backend    | Required Version | Required extensions/software             |
    +============+==================+==========================================+
    | SQLite     | >= 3.6           | spatialite (>= 2.3), pysqlite2 (>= 2.5), |
    |            |                  | GEOS (>= 3.0), GDAL (>= 1.4),            |
    |            |                  | PROJ.4 (>= 4.4)                          |
    +------------+------------------+------------------------------------------+
    | PostgreSQL | >= 8.1           | PostGIS (>= 1.3), GEOS (>= 3.0),         |
    |            |                  | PROJ.4 (>= 4.4), psycopg2 (== 2.4.1)     |
    +------------+------------------+------------------------------------------+


Installing EOxServer
--------------------

There are several easy options to install EOxServer:

* Install an official release of EOxServer, the best approach for users who
  want a stable version and aren't concerned about running a slightly older
  version of EOxServer. You can install EOxServer either from

  * `PyPI - the Python Package Index <http://pypi.python.org/pypi>`_ using
    `pip <http://www.pip-installer.org/en/latest/index.html>`_:
    ::

      sudo pip install eoxserver

  * Or from the `EOxServer download page <http://eoxserver.org/wiki/Download>`_
    using pip:
    ::

      sudo pip install http://eoxserver.org/export/head/downloads/EOxServer-<version>.tar.gz

    or manual:
    ::

      wget http://eoxserver.org/export/head/downloads/EOxServer_full-<version>.tar.gz .
      tar xvfz EOxServer-<version>.tar.gz
      cd EOxServer-<version>
      sudo python setup.py install

* Install the latest development version, the best option for users who
  want the latest-and-greatest features and aren't afraid of running
  brand-new code. Make sure you have `Subversion
  <http://subversion.tigris.org/>`_ installed and install EOxServer's
  main development branch (the trunk) using pip:
  ::

    sudo pip install svn+http://eoxserver.org/svn/trunk

  or manual:
  ::

    svn co http://eoxserver.org/svn/trunk/ eoxserver-trunk
    cd eoxserver-trunk
    sudo python setup.py install

If the directory EOxServer is installed to is not on the Python path, you will
have to configure the deployed instances accordingly, see
:ref:`EOxServer Deployment` below.

The successful installation of EOxServer can be tested using the
:ref:`autotest instance <Autotest>` which is described in more detail in the
:ref:`EOxServer Developers' Guide`.

.. index::
    single: EOxServer Instance Creation
    single: Instance Creation

Upgrading EOxServer
-------------------

To upgrade an existing installation of EOxServer simply add the `--upgrade`
switch to your pip command e.g.:
::

  sudo pip install --upgrade eoxserver

or rerun the manual installation as explained above.

Please follow the update procedure for any configured EOxServer instances in
case of a major version upgrade.

.. _Creating an Instance:

Creating an Instance
--------------------

Speaking of EOxServer we distinguish the EOxServer distribution (the code that
implements the different services the software provides) and EOxServer
instances (a collection of data and configuration files that enables deployment
of the software.

We recommend to use the :file:`eoxserver-admin.py` script that comes with
EOxServer. It provides the command `create_instance` in order to create an
EOxServer instance:

    Usage: ``eoxserver-admin.py create_instance [options] INSTANCE_ID``

    Create a new EOxServer instance ``INSTANCE_ID`` in the root directory with
    name ``INSTANCE_ID`` in the given (optional) directory. If the
    ``--init_spatialite`` flag is set, then an initial sqlite database will be
    created and initialized.

    Options:

    -h, --help           show help message and exit
    -d DIR, --dir=DIR    Optional base directory. Defaults to the current
                         directory.
    --initial_data=DIR   Location of the initial data. Must be JSON.
    --init_spatialite    Flag to initialize the sqlite database.

.. index::
    single: EOxServer Configuration
    single: Configuration

Configuration
~~~~~~~~~~~~~

Every EOxServer instance has three configuration files:

* ``settings.py`` - `template
  <http://eoxserver.org/browser/trunk/eoxserver/conf/TEMPLATE_settings.py>`__
* ``conf/eoxserver.conf`` - `template
  <http://eoxserver.org/browser/trunk/eoxserver/conf/TEMPLATE_eoxserver.conf>`__
* ``conf/template.map`` - `template
  <http://eoxserver.org/browser/trunk/eoxserver/conf/TEMPLATE_template.map>`__

For each of them there is a template in the ``eoxserver/conf`` directory of the
EOxServer distribution (referenced above) which is copied and adjusted by the
`create_instance` command of the :file:`eoxserver-admin.py` script to the
instance directory. If you create an EOxServer instance without the script you
can copy those files and edit them yourself.

The file ``settings.py`` contains the Django configuration. Settings that need
to be customized:

* ``PROJECT_DIR``: Absolute path to the instance directory.
* ``DATABASES``: The database connection details. For detailed information see
  `Database Setup`_

You can also customize further settings, for a complete reference please refer
to the `Django settings overview
<https://docs.djangoproject.com/en/1.3/topics/settings/>`_.

Please especially consider the setting of the 'TIME_ZONE
<https://docs.djangoproject.com/en/1.3/ref/settings/#std:setting-TIME_ZONE>`_
parameter and read the Notes provided in the ``settings.py`` file.


The file ``conf/eoxserver.conf`` contains EOxServer specific settings. Please
refer to the inline documentation for details.

The file ``conf/template.map`` contains basic metadata for the OGC Web Services
used by MapServer. For more information on metadata supported please refer to
the `MapServer Mapfile documentation
<http://mapserver.org/mapfile/index.html>`_.

Once you have created an instance, you have to configure and synchronize the
database. If using the `create_instance` command of the
:file:`eoxserver-admin.py` script with the ``--init_spatialite`` flag, all you
have to do is:

* Make sure EOxServer is on your ``PYTHONPATH`` environment variable
* run in your instance directory
  ::

    python manage.py syncdb

.. TODO: Logfile handling: configuration in settings.py and eoxserver.conf logrotate, etc.

.. _Database Setup:

Database Setup
~~~~~~~~~~~~~~

This section is only needed if the ``--init_spatialite`` flag was not used
during instance creation or a PostgreSQL/PostGIS database back-end shall be
used. Before proceeding, please make sure that you have installed all required
software for the database system of your choice.

Using a SQLite database, all you have to do is to copy the
``TEMPLATE_config.sqlite`` and place it somewhere in your instance directory.
Now you have to edit the ``DATABASES`` of your ``settings.py`` file with the
following lines:
::

    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': '/path/to/config.sqlite',
        }
    }


Using a PostgreSQL/PostGIS database back-end configuration for EOxServer is a
little bit more complex. Setting up a PostgreSQL database requires also
installing the PostGIS extensions (the following example is an installation
based on a Debian system):
::

    sudo su - postgres
    POSTGIS_DB_NAME=eoxserver_db
    POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib/postgis-1.5
    createdb $POSTGIS_DB_NAME
    createlang plpgsql $POSTGIS_DB_NAME
    psql -d $POSTGIS_DB_NAME -f $POSTGIS_SQL_PATH/postgis.sql
    psql -d $POSTGIS_DB_NAME -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
    psql -d $POSTGIS_DB_NAME -f `pg_config --sharedir`/contrib/hstore-new.sql
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

This creates the database and installs the PostGIS extensions within the
database. Now a user with password can be set with the following line:
::

    createuser -d -R -P -S eoxserver-admin

In the ``settings.py`` the following entry has to be added:
::

    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'eoxserver_db',
            'USER': 'eoxserver-admin',
            'PASSWORD': 'eoxserver',
            'HOST': 'localhost',    # or the URL of your server hosting the DB
            'PORT': '',
        }
    }

Please refer to `GeoDjango Database API
<https://docs.djangoproject.com/en/1.3/ref/contrib/gis/db-api/>`_ for more
instructions.

.. index::
    single: EOxServer Deployment
    single: Deployment

.. _EOxServer Deployment:

Deployment
~~~~~~~~~~

EOxServer is deployed using the Python WSGI interface standard as any other
`Django application <https://docs.djangoproject.com/en/1.3/howto/deployment/>`_.
The WSGI endpoint accepts HTTP requests passed from the web server and
processes them synchronously. Each request is executed independently.

In the following we present the way to deploy it using the `Apache2 Web Server
<http://httpd.apache.org>`_ and its `mod_wsgi
<http://code.google.com/p/modwsgi/>`_ extension module.

The deployment procedure consists of the following:

* create a ``deployment`` subdirectory in your instance
* copy ``TEMPLATE_wsgi.py`` from the EOxServer distribution ``eoxserver/conf``
  directory there under the name ``wsgi.py``
* Customize ``wsgi.py``
* Customize the Apache2 configuration file
* Restart the Web Server

In ``wsgi.py``, two items need to be customized. First, the Python path has to
be set properly and second, the Django settings module (``settings.py``) has to
be configured. The places where to fill in the right names are indicated in the
file.

In the Apache2 configuration file for your server, e.g.
``/etc/apache2/sites-enabled/000-default``, please add the following lines:
::

    Alias /<url> <absolute path to instance dir>/deployment/wsgi.py
    <Directory "<absolute path to instance dir>/deployment">
            AllowOverride None
            Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
            AddHandler wsgi-script .py
            Order Allow,Deny
            Allow from all
    </Directory>

This setup will deploy your instance under the URL ``<url>`` and make it
publicly accessible.

Now that the public URL is known don't forget to adjust the configuration in
``conf/eoxserver.conf``::

    [services.owscommon]
    http_service_url=http://<url>/ows

.. _Data Registration:

Data Registration
~~~~~~~~~~~~~~~~~

To insert data into an EOxServer instance there are several ways. One is the
admin interface, which is explained in detail in the :ref:`ops_admin` section.

Another convenient way to register datasets is the command line interface to
EOxServer. As a Django application, the instance can be configured using the
`manage.py <https://docs.djangoproject.com/en/dev/ref/django-admin/>`_ script.

EOxServer provides a specific command to insert datasets into the instance,
called ``eoxs_register_dataset``. It is invoked from command line from your
instance base folder:
::

    python manage.py eoxs_register_dataset --data-file DATAFILES --rangetype RANGETYPE

The mandatory parameter ``--data-file`` is a list of at least one path to a
file containing the raster data for the dataset to be inserted. The files
can be in any compliant (GDAL readable) format. When inserting datasets
located in a Rasdaman database, this parameter defines the `collection` the
dataset is contained in.

Also mandatory is the parameter ``--rangetype``, the name of a range type
which has to be already present in the instance's database.

For each data file there may be given one metadata file containing earth
observation specific metadata. The optional parameter ``--metadata-file``
shall contain a list of paths to these files, where the items of this list
refer to the data files with the same index of the according option. A
metadata file for each data file is assumed with the same path, but with an
`.xml` extension when this parameter is omitted. However, it is only used
when it actually exists. Otherwise the data file itself is used to retrieve
the metadata values. When this is not possible either, the default values
are used as described below or the insertion is aborted.

When inserting datasets located in a Rasdaman database, this parameter is
mandatory, since the metadata cannot be retrieved from within the rasdaman
database and must be locally accessible.

For each dataset a coverage ID can be specified with the ``--coverage-id``
parameter. As with the ``--metadata-file`` option, the items of the list refer
to the items of the ``--data-file`` list. If omitted, an ID is generated using
the data file name.

The parameters ``--dataset-series`` and ``--stitched-mosaic`` allow to insert
the dataset into all dataset series and rectified stitched mosaics specified
by their EO IDs.

The ``--mode`` parameter specifies the location of the data and metadata files
as they may be located on a FTP server or in a Rasdaman database. This can
either be `local`, `ftp` or `rasdaman`, whereas the default is `local`.

When the mode is set to either `ftp` or `rasdaman` the following options
define the location of the dataset and the connection to it more
thoroughly: ``--host``, ``--port``, ``--user``, ``--password``, and
``--database`` (only for `rasdaman`). Only the ``--host`` parameter is
mandatory, all others are optional.

The ``--default-srid`` parameter is required when the SRID cannot be determined
automatically, as for example with rasdaman datasets.

For when you explicitly want to override the geospatial metadata of a dataset
you can use ``--default-size`` and ``--default-extent``. Both parameters need
to be used together and in combination with ``--default-srid``. This is
required for datasets registered in a rasdaman database or for any other
input method where the geospatial metadata cannot be retrieved.

For datasets that do not have any EO metadata associated and want to be
inserted anyways, the options ``--default-begin-time``, ``--default-end-time``
and ``--default-footprint`` have to be used. These meta data values will only
be used when no local meta data file is found (remote files are not checked).
All three options have to be used in combination, so it is, for example, not
possible to only provide the footprint via ``--default-footprint`` and let
EOxServer gather the rest. There is one exception: when only begin and end
dates are given, the footprint is generated using the image extent.

With the ``--visible`` option, all registered datasets can be marked as either
visible (``true``) or invisible (``false``). This effects the advertisment of
the dataset in e.g: GetCapabilities responses. By default, all datasets are
visible.

This is an example usage of the ``eoxs_register_dataset`` command::

    python manage.py eoxs_register_dataset --data-file data/meris/mosaic_MER_FRS_1P_RGB_reduced/*.tif --rangetype RGB \
        --dataset-series MER_FRS_1P_RGB_reduced --stitched-mosaic mosaic_MER_FRS_1P_RGB_reduced -v3

In this example, the parameter ``--metadata-file`` is omitted, since these files
are in the same location as the data files and only differ in their extension.
Also note that the ``--data-file`` parameter uses a shell wildcard `*.tif` which
expands to all files with `.tif` extension in that directory. This
funcitonality is not provided by EOxServer but by the operating system or the
executing shell and is most certainly platform dependant.

Here is another example including the ``--coverage-ids`` parameter which 
overwrites the default ids based on the data file names e.g. because they 
are not valid ``NCNames`` which is needed by the XML schemas::

    python manage.py eoxs_register_dataset --data-files 1.tif 2.tif 3.tif \
        --coverage-ids a b c --rangetype RGB  -v3

The registered dataset is also inserted to the given dataset series and
rectified stitched mosaic.

Here is the full list of available options:

  -v VERBOSITY, --verbosity=VERBOSITY
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=all output
  --settings=SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Print traceback on exception
  -d, --data-file, --data-files, --collection, --collections
                        Mandatory. One or more paths to a files containing the
                        image data. These paths can either be local, ftp
                        paths, or rasdaman collection names.
  -m, --metadata-file, --metadata-files
                        Optional. One or more paths to a local files
                        containing the image meta data. Defaults to the same
                        path as the data file with the ".xml" extension.
  -r RANGETYPE, --rangetype=RANGETYPE
                        Mandatory identifier of the rangetype used in the
                        dataset.
  --dataset-series      Optional. One or more eo ids of a dataset series in
                        which the created datasets shall be added.
  --stitched-mosaic     Optional. One or more eo ids of a rectified stitched
                        mosaic in which the dataset shall be added.
  -i, --coverage-id, --coverage-ids
                        Optional. One or more coverage identifier for each
                        dataset that shall be added. Defaults to the base
                        filename without extension.
  --mode=MODE           Optional. Defines the location of the datasets to be
                        registered. Can be 'local', 'ftp', or 'rasdaman'.
                        Defaults to 'local'.
  --host=HOST           Mandatory when mode is not 'local'. Defines the
                        ftp/rasdaman host to locate the dataset.
  --port=PORT           Optional. Defines the port for ftp/rasdaman host
                        connections.
  --user=USER           Optional. Defines the ftp/rasdaman user for the
                        ftp/rasdaman connection.
  --password=PASSWORD   Optional. Defines the ftp/rasdaman user password for
                        the ftp/rasdaman connection.
  --database=DATABASE   Optional. Defines the rasdaman database containing the
                        data.
  --oid, --oids         Optional. List of rasdaman oids for each dataset to be
                        inserted.
  --default-srid=DEFAULT_SRID
                        Optional. Default SRID, needed if it cannot be
                        determined automatically by GDAL.
  --default-size=DEFAULT_SIZE
                        Optional. Default size, needed if it cannot be
                        determined automatically by GDAL. Format:
                        <sizex>,<sizey>
  --default-extent=DEFAULT_EXTENT
                        Optional. Default extent, needed if it cannot be
                        determined automatically by GDAL. Format:
                        <minx>,<miny>,<maxx>,<maxy>
  --default-begin-time  Optional. Default begin timestamp when no other EO-
                        metadata is available. The format is ISO-8601.
  --default-end-time    Optional. Default end timestamp when no other EO-
                        metadata is available. The format is ISO-8601.
  --default-footprint   Optional. The default footprint in WKT format when no
                        other EO-metadata is available.s
  --visible=VISIBLE     Optional. Sets the visibility status of all datasets
                        to thegiven boolean value. Defaults to 'True'.
  --version             show program's version number and exit
  -h, --help            show this help message and exit
