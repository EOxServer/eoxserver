.. InstanceCreation
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Martin Paces <martin.paces@eox.at>
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
    single: EOxServer Service Instance Creation 
    single: Instance Creation

.. _Creating an Instance:
.. _InstanceCreation:

Service Instance Creation and Configuration
===========================================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Speaking of EOxServer we distinguish the common EOxServer installation (the 
installed code implementing the software functionality) and EOxServer 
instances. An instance is a collection of data and configuration files that 
enables the deployment of a specific service. A single server will typically 
contain a single software installation and one or more specific instances.

This section deals with the creation and configuration of EOxServer instances.

.. seealso:: 

    * :ref:`Installation`
            generic installation procedure for GNU/Linux operating systems.
    * :ref:`CentOSInstallation`
            for specific installation on CentOS.
    * :ref:`OperationalInstallation` 
            to configure an operational EOxServer installation.

Instance Creation 
-----------------

To create an instance, we recommend to use the :file:`eoxserver-admin.py` 
script that comes with EOxServer. The script provides the command 
`create_instance` in order to create an EOxServer instance:

    Usage: ``eoxserver-admin.py create_instance [options] INSTANCE_ID [Optional destination directory]``

    Creates a new EOxServer instance with name ``INSTANCE_ID`` in the current 
    or optionally given directory with all necessary files and folder 
    structure. If the ``--init_spatialite`` flag is set, then an initial 
    sqlite database will be created and initialized.

    Options:

    -h, --help           show this help message and exit
    --init_spatialite    Flag to initialize the sqlite database.

.. index::
    single: EOxServer Configuration
    single: Configuration

Instance Configuration
----------------------

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
<https://docs.djangoproject.com/en/1.4/topics/settings/>`_.

Please especially consider the setting of the `TIME_ZONE
<https://docs.djangoproject.com/en/1.4/ref/settings/#std:setting-TIME_ZONE>`_
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
* run in your instance directory::

    python manage.py syncdb

Note down the username and password you provide. You'll need it to log in to 
the admin client.

.. TODO: Logfile handling: configuration in settings.py and eoxserver.conf logrotate, etc.

.. _Database Setup:
.. _InstanceCreation_DBSetup:

Database Setup
--------------

This section is only needed if the ``--init_spatialite`` flag was not used
during instance creation or a PostgreSQL/PostGIS database back-end shall be
used. Before proceeding, please make sure that you have installed all required
software for the database system of your choice.

Using a SQLite database, all you have to do is to copy the
``TEMPLATE_config.sqlite`` and place it somewhere in your instance directory.
Now you have to edit the ``DATABASES`` of your ``settings.py`` file with the
following lines::

    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.spatialite',
            'NAME': '/path/to/config.sqlite',
        }
    }

.. note::

    By default the number of SQL variables (SQLITE_MAX_VARIABLE_NUMBER) in SQL
    is limited to 999. This leads to problems when having inserted 1000 
    datasets or more. In this case the limit could either be increased or 
    PostgreSQL/PostGIS must be used as a back-end database.

Using a PostgreSQL/PostGIS database back-end configuration for EOxServer is a
little bit more complex. Setting up a PostgreSQL database requires also
installing the PostGIS extensions (the following example is an installation
based on a Debian system)::

    sudo su - postgres
    POSTGIS_DB_NAME=eoxserver_db
    POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib/postgis-1.5
    createdb $POSTGIS_DB_NAME
    createlang plpgsql $POSTGIS_DB_NAME
    psql -d $POSTGIS_DB_NAME -f $POSTGIS_SQL_PATH/postgis.sql
    psql -d $POSTGIS_DB_NAME -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -d $POSTGIS_DB_NAME -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

This creates the database and installs the PostGIS extensions within the
database. Now a user with password can be set with the following line::

    createuser -d -R -P -S eoxserver-admin

Depending on the configuration of the system used there may be the need to 
enable access for the user in the ``pg_hba.conf``.

In the ``settings.py`` the following entry has to be added::

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
<https://docs.djangoproject.com/en/1.4/ref/contrib/gis/db-api/>`_ for more
instructions.

.. index::
    single: EOxServer Deployment
    single: Deployment

.. _EOxServer Deployment:

Deployment
----------

EOxServer is deployed using the Python WSGI interface standard as any other
`Django application <https://docs.djangoproject.com/en/1.4/howto/deployment/>`_.
The WSGI endpoint accepts HTTP requests passed from the web server and
processes them synchronously. Each request is executed independently.

In the following we present the way to deploy it using the `Apache2 Web Server
<http://httpd.apache.org>`_ and its `mod_wsgi
<http://code.google.com/p/modwsgi/>`_ extension module.

The deployment procedure consists of the following:

* Customize the Apache2 configuration file, e.g.
  ``/etc/apache2/sites-enabled/000-default``, by adding::

    Alias /<url> <absolute path to instance dir>/wsgi.py
    <Directory "<absolute path to instance dir>">
            AllowOverride None
            Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
            AddHandler wsgi-script .py
            Order Allow,Deny
            Allow from all
    </Directory>

* If using EOxServer < 0.3 customize ``wsgi.py`` in your EOxServer instance 
  and add::

    import sys

    path = "<absolute path to instance dir>"
    if path not in sys.path:
        sys.path.append(path)

  * If using Django < 1.4 please copy ``TEMPLATE_wsgi.py`` from the EOxServer 
    distribution ``eoxserver/conf`` directory in your instance under the name 
    ``wsgi.py`` and customize it at the two indicated places.

* Restart the Web Server

As a general good idea the number of threads can be limited using the 
following additional Apache2 configuration. In case an old version of 
MapServer, i.e. < 6.2 or < 6.0.4, is used the number of threads **needs** to be 
limited to 1 to avoid some `thread safety issues 
<https://github.com/mapserver/mapserver/issues/4369>`_::

    WSGIDaemonProcess ows processes=10 threads=1
    <Directory "<absolute path to instance dir>">
        ...
        WSGIProcessGroup ows
    </Directory>

This setup will deploy your instance under the URL ``<url>`` and make it
publicly accessible.

Now that the public URL is known don't forget to adjust the configuration in
``conf/eoxserver.conf``::

    [services.owscommon]
    http_service_url=http://<url>/ows

Finally all the static files need to be collected at the location configured 
by ``STATIC_ROOT`` in ``settings.py`` by using the following command from 
within your instance::

    python manage.py collectstatic

Don't forget to update the static files by re-running above command if needed.

.. _Data Registration:

Data Registration
-----------------

To insert data into an EOxServer instance there are several ways. One is the
admin interface, which is explained in detail in the :ref:`ops_admin` section.

Another convenient way to register datasets is the command line interface to
EOxServer. As a Django application, the instance can be configured using the
`manage.py <https://docs.djangoproject.com/en/1.4/ref/django-admin/>`_ script.

EOxServer provides a specific command to insert datasets into the instance,
called ``eoxs_register_dataset``. It is invoked from command line from your
instance base folder::

    python manage.py eoxs_register_dataset --data-file DATAFILES --rangetype RANGETYPE

The mandatory parameter ``--data-file`` is a list of at least one path to a
file containing the raster data for the dataset to be inserted. The files
can be in any compliant (GDAL readable) format. When inserting datasets
located in a Rasdaman database, this parameter defines the `collection` the
dataset is contained in.

Also mandatory is the parameter ``--rangetype``, the name of a range type
which has to be already present in the instance's database.

For each data file there may be given one metadata file containing Earth
Observation specific metadata. The optional parameter ``--metadata-file``
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
