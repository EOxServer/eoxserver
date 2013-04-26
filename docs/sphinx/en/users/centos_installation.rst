.. CentOSInstallation
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
  #          Marko Locher <marko.locher@eox.at>
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
    single: Installation on CentOS

.. _CentOSInstallation:

Installation on CentOS
======================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

This section describes specific installation procedure for EOxServer 
on `CentOS <http://www.centos.org/>`_ GNU/Linux based operating systems. 
In this example, a raw CentOS 6.4 minimal image is used.

This guide is assumed (but not tested) to be applicable also for equivalent
versions of the prominent North American Enterprise Linux and its clones.

.. seealso:: 

    * :ref:`Installation`
            generic installation procedure for GNU/Linux operating systems.
    * :ref:`InstanceCreation` 
            to configure an instance of EOxServer after successful installation.
    * :ref:`OperationalInstallation` 
            to configure an operational EOxServer installation.

Prerequisites
-------------

This example requires a running CentOS installation with superuser privileges
available.

.. _CentOSInstallation_repos:


Installation from RPM Packages
------------------------------

Preparation of RPM Repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default repositories of CentOS do not provide all software packages
required for EOxServer, and some packages are only provided in out-dated
versions. Thus several further repositories have to be added to the system's
list.

The first one is the `ELGIS (Enterprise Linux GIS)
<http://wiki.osgeo.org/wiki/Enterprise_Linux_GIS>`_ repository which can be
added with the following `yum` command::

    sudo rpm -Uvh http://elgis.argeo.org/repos/6/elgis-release-6-6_0.noarch.rpm

The second repository to be added is `EPEL (Extra Packages for Enterprise
Linux) <http://fedoraproject.org/wiki/EPEL>`_ again via a simple `yum` command::

    sudo rpm -Uvh http://download.fedoraproject.org/pub/epel/6/x86_64/epel-release-6-8.noarch.rpm

Finally EOxServer is available from the yum repository at `packages.eox.at 
<http://packages.eox.at>`_. This repository offers current versions of 
packages like `MapServer <http://mapserver.org/>`_ as well as custom built 
ones with extra drivers enabled like `GDAL <http://gdal.org/>`_ and/or with 
patches applied like `libxml2 <http://xmlsoft.org/>`_. It is not mandatory 
to use this repository as detailed below but it is highly recommended in 
order for all features of EOxServer to work correctly. The repository is 
again easily added via a single `yum` command::

    sudo rpm -Uvh http://yum.packages.eox.at/el/eox-release-6-2.noarch.rpm


.. _centos-installing-eoxserver-yum:

.. _CentOSInstallation_rpm:

Installing EOxServer
~~~~~~~~~~~~~~~~~~~~

Once the RPM repositories are configured EOxServer and all its dependencies 
are installed via a single command::

    sudo yum install EOxServer

To update EOxServer simply run the above command again or update the whole 
system with::

    sudo yum update

Please carefully follow the :ref:`migration/update procedure <Migration>` 
corresponding to your version numbers for any configured EOxServer instances 
in case of a major version upgrade.

Further packages may be required if additional features (e.g: a full DBMS) 
are desired. The following command for example installs all packages needed 
when using SQLite::

    sudo yum install sqlite libspatialite python-pysqlite python-pyspatialite

Alternatively the PosgreSQL DBMS can be installed as follows::

    sudo yum install postgresql postgresql-server postgis python-psycopg2

To run EOxServer behind the Apache web server requires the installation of this
web server::

    sudo yum install httpd mod_wsgi
    
Now that EOxServer is properly installed the next step is to :ref:`create and
configure a service instance <InstanceCreation>`. 

.. _CentOSInstallation_pip:

Alternate installation method using *pip*
-----------------------------------------

Required Software Packages
~~~~~~~~~~~~~~~~~~~~~~~~~~

The installation via pip builds EOxServer from its source. Thus there are 
some additional packages required which can be installed using::

    sudo yum install gdal gdal-python gdal-devel mapserver mapserver-python \
                     libxml2 libxml2-python python-lxml python-pip \
                     python-devel gcc

Installing EOxServer
~~~~~~~~~~~~~~~~~~~~

For the installation of Python packages `pip <http://www.pip-installer.org/>`_ 
is used, which itself was installed in the previous step. It automatically 
resolves and installs all dependencies. So a simple::

    sudo pip-python install eoxserver

suffices to install EOxServer itself.

To upgrade an existing installation of EOxServer simply add the ``--upgrade``
switch to your pip command::

  sudo pip-python install --upgrade eoxserver

Please don't forget to follow the update procedure for any configured 
EOxServer instances in case of a major version upgrade.

Now that EOxServer is properly installed the next step is to :ref:`create and
configure a service instance <InstanceCreation>`. 


Special *pysqlite* considerations
---------------------------------

When used with `spatialite <http://www.gaia-gis.it/spatialite/>`_ EOxServer 
also requires `pysqlite <http://code.google.com/p/pysqlite/>`_ and 
`pyspatialite` which can be either installed as RPMs from `packages.eox.at 
<http://packages.eox.at>`_ (see :ref:`centos-installing-eoxserver-yum` 
above) or from source.

If installing from source please make sure to adjust the 
`SQLITE_OMIT_LOAD_EXTENSION` parameter in ``setup.cfg`` which is set by 
default but not allowed for EOxServer. The following provides a complete 
installation procedure::

    sudo yum install libspatialite-devel geos-devel proj-devel
    sudo pip-python install pyspatialite
    wget https://pysqlite.googlecode.com/files/pysqlite-2.6.3.tar.gz
    tar xzf pysqlite-2.6.3.tar.gz
    cd pysqlite-2.6.3
    sed -e '/^define=SQLITE_OMIT_LOAD_EXTENSION$/d' -i setup.cfg
    sudo python setup.py install

If the installation is rerun the ``--upgrade`` respectively the ``--force`` 
flag have to be added to the ``pip-python`` and ``python`` commands in order 
to actually redo the installation::

    sudo pip-python install --upgrade pyspatialite
    sudo python setup.py install --force
