.. CentOSInstallation
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
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

This article describes the installation procedure for EOxServer on a `CentOS
<http://www.centos.org/>`_ system. In this example, a raw CentOS 6.2 minimal
image is used.

This installation example is complementary to the standard :ref:`Installation`
manual.


Prerequisites
-------------

This example requires a running CentOS installation with superuser privileges
available.


Preparation of RPM repositories
-------------------------------

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

    sudo rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-5.noarch.rpm

EOxServer requires several adjustments to existing packages to work correctly 
which can be easily obtained from the yum repository at `packages.eox.at 
<http://packages.eox.at>`_. This repository offers current versions of packages 
like `MapServer <http://mapserver.org/>`_ as well as custom built ones with 
extra drivers enabled like `GDAL <http://gdal.org/>`_ and/or with patches 
applied like `libxml2 <http://xmlsoft.org/>`_. It is not mandatory to use this
repository but it is highly recommended in order for all features of EOxServer 
to work correctly.

The repository is easily installed::

    cd /etc/yum.repos.d/
    sudo wget http://packages.eox.at/eox.repo
    sudo rpm --import http://packages.eox.at/eox-package-maintainers.gpg
    sudo yum update


Installation of required software packages
------------------------------------------

Now the required packages can be installed with only one command::

    sudo yum install gcc gdal gdal-devel gdal-python libxml2 libxml2-python \
                     mapserver mapserver-python sqlite sqlite-devel \
                     python-lxml python-pip python-devel

Further packages may be required if additional features (e.g: a full DBMS) are
desired.


Installing EOxServer
--------------------

For installation of Python packages `pip <http://www.pip-installer.org/>`_ is 
used, which iself was installed in the previous step. It automatically resolves 
and installs all dependencies. So a simple
::

    sudo pip-python install eoxserver

suffices to install EOxServer itself.

Upgrading EOxServer
-------------------

To upgrade an existing installation of EOxServer simply add the `--upgrade` 
switch to your pip command::

  sudo pip-python install --upgrade eoxserver

When used with `spatialite <http://www.gaia-gis.it/spatialite/>`_ make sure 
to rerun the manual pysqlite installation as explained below after every 
upgrade.

It might be a good idea to update the whole system which might include updates of required software packages such as MapServer::

    sudo yum update

Please follow the update procedure for any configured EOxServer instances in 
case of a major version upgrade.

spatialite usage
----------------

When used with `spatialite <http://www.gaia-gis.it/spatialite/>`_ EOxServer
also requires `pysqlite <http://code.google.com/p/pysqlite/>`_. Unfortunately
pysqlite is built by default without a required parameter. Thus it has to be
installed manually::

    wget https://pysqlite.googlecode.com/files/pysqlite-2.6.3.tar.gz
    tar xzf pysqlite-2.6.3.tar.gz
    cd pysqlite-2.6.3

Now `setup.cfg` needs to be opened with a text editor (like `vi`) and the line
::

    define=SQLITE_OMIT_LOAD_EXTENSION

has to be deleted or commented. Pysqlite can now be installed with::

    sudo python setup.py install

If the installation is rerun you will need to add the ``--force`` flag to 
actually redo the installation::

    sudo python setup.py install --force

The ``--init_spatialite`` flag of the ``create_instance`` command of the 
``eoxserver-admin.py`` script used to initialize a sqlite database needs 
pyspatialite::

    sudo yum install libspatialite-devel geos-devel proj-devel
    sudo pip-python install pyspatialite

Now that EOxServer is properly install the next step is to :ref:`create and configure
an instance <Creating an Instance>`. 
