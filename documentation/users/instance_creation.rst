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

To create an instance, we recommend to use the :file:`eoxserver-instance.py`
script that comes with EOxServer:

    Usage: ``eoxserver-instance.py [options] INSTANCE_ID [Optional destination directory]``

    Creates a new EOxServer instance with name ``INSTANCE_ID`` in the current
    or optionally given directory with all necessary files and folder
    structure. If the ``--init-spatialite`` flag is set, then an initial
    sqlite database will be created and initialized.

    Options:

    -h, --help           show this help message and exit
    --init-spatialite    Flag to initialize the sqlite database.

.. index::
    single: EOxServer Configuration
    single: Configuration

Instance Configuration
----------------------

Every EOxServer instance has various configuration files:

* ``settings.py`` - `template
  <https://github.com/EOxServer/eoxserver/blob/0.4/eoxserver/instance_template/project_name/settings.py>`__
* `urls.py`` - `template
  <https://github.com/EOxServer/eoxserver/blob/0.4/eoxserver/instance_template/project_name/urls.py>`__
* ``conf/eoxserver.conf`` - `template
  <https://github.com/EOxServer/eoxserver/blob/0.4/eoxserver/instance_template/project_name/conf/eoxserver.conf>`__

For each of them there is a template in the ``eoxserver/instance_template``
directory of the EOxServer distribution (referenced above) which is copied and
adjusted by the :file:`eoxserver-instance.py` script to the instance directory.
If you create an EOxServer instance without the script you can copy those files
and edit them yourself.

The file ``settings.py`` contains the Django configuration. Settings that need
to be customized:

* ``PROJECT_DIR``: Absolute path to the instance directory.
* ``DATABASES``: The database connection details. For detailed information see
  `Database Setup`_
* ``COMPONENTS``: The EOxServer components enabled for this instance. This is
  the main way how the active functionality of EOxServer is controlled, and also
  a way to extend the existing capabilities with extensions. Please refer to the
  :ref:`Plugins` section to see how this is done. By default all available components
  are enabled.
* ``LOGGING``: what and how logs are prcessed and stored. EOxServer provides a
  very basic configuration that stores logfiles in the instace directory, but
  they will probably not be suitable for every instance.

You can also customize further settings, for a complete reference please refer
to the `Django settings overview
<https://docs.djangoproject.com/en/1.11/topics/settings/>`_.

Please especially consider the setting of the `TIME_ZONE
<https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-TIME_ZONE>`_
parameter and read the Notes provided in the ``settings.py`` file.

The file ``conf/eoxserver.conf`` contains EOxServer specific settings. Please
refer to the `configuration options section <ConfigurationOptions>`_ for details.

Once you have created an instance, you have to configure and synchronize the
database. If you are using the :file:`eoxserver-instance.py` script with the
``--init-spatialite`` flag, all you have to do is:

* Make sure EOxServer is on your ``PYTHONPATH`` environment variable
* run in your instance directory::

    python manage.py syncdb

This script will also create an administration user if you want to. Note the
username and password you provide. You'll need it to log in to the admin client.

You can always create a user at a later time by running
``python manage.py createsuperuser``.

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
<https://docs.djangoproject.com/en/1.11/ref/contrib/gis/db-api/>`_ for more
instructions.

.. index::
    single: EOxServer Deployment
    single: Deployment

.. _EOxServer Deployment:

Deployment
----------

EOxServer is deployed using the Python WSGI interface standard as any other
`Django application <https://docs.djangoproject.com/en/1.11/howto/deployment/>`_.
The WSGI endpoint accepts HTTP requests passed from the web server and
processes them synchronously. Each request is executed independently.

In the `deployment git repository <https://github.com/EOxServer/deployment>`_
we collect snippets for various deployment scenarios.

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
`manage.py <https://docs.djangoproject.com/en/1.11/ref/django-admin/>`_ script.

EOxServer provides a specific command and a subcommand to insert datasets into the instance,
called ``coverage register``. It is invoked from command line from your
instance base folder::

    python manage.py coverage register --data DATAFILES --coverage-type COVERAGETYPE    

The mandatory parameter ``--data`` is a path to a file containing the raster
data for the dataset to be inserted. If the file resides in a package (a ZIP or
TAR archive) then the location must be preceeded with the following:
``<package-type>:<package-location>``. It also possible to chain multiple
packages, e.g a ZIP file in a ZIP file containing the actual raster data.
In conjunction to packages, it is also possible to state the storage of the
data files. By default it is assumed that the data is available locally, but
other storages (such as FTP or HTTP backends) are also possible. If used, it
must be declared as first item in the aforementioned in the chain.

For each ``--data`` item a ``--semantic`` can be stated. The semantic defines\]
how this data item is being used. For example a semantic of ``"bands[1:3]"``
defines that the first three bands of the dataset is in the first data item.

The same rules also apply for files declared via the ``--meta-data`` directive.
This basically creates a ``--data`` item with ``"metadata"`` semantic. Also,
these files are preferred when trying to determine the mandatory metadata of a
dataset.

To specify the Coverage Type of the dataset, the ``--coverage-type`` parameter is
mandatory to specify the name of a previously registered Coverage Type.

The following options are used to supply metadata values that are either not
possible to retrieve automatically or are to overwrite values automatically
collected:

  * ``--identifier``: the main identifier of the dataset
  * ``--grid GRID``: the name of the grid to associate the coverage with.
  * ``--size``: the pixel size of the dataset (size_x,size_y)
  * ``--footprint-from-extent``: the footprint from the coverages extent, reprojected to WGS 84
  * ``--footprint``: the footprint (multi-) polygon in WKT format
  * ``--begin-time`` and ``--end-time``: the datasets time span
  * ``--coverage-type``: the type of the dataset

When this dataset shall be inserted into a collection, use the ``--collection``
option with the collections identifier. This option can be set multiple times
for different collections.
