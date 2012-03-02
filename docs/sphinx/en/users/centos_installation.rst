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

Example Installation on a CentOS system
=======================================

This article describes an example installation of EOxServer on a `CentOS
<http://www.centos.org/>`_ system. In this example, a raw CentOS 6.2 minimal
image was used.

This installation example is complementary to the standard installation manual.
#### TODO link


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
added with the following `yum` command:
::

    sudo rpm -Uvh http://elgis.argeo.org/repos/5/elgis-release-5-5_0.noarch.rpm

The second repository to be added is `EPEL (Extra Packages for Enterprise
Linux) <http://fedoraproject.org/wiki/EPEL>`_ which can also be added by a
simple `yum` command:
::

    rpm -Uvh http://download.fedoraproject.org/pub/epel/6/i386/epel-release-6-5.noarch.rpm

Since EOxServer requires several adjustments to existing packages to work
correctly, eoxserver.org provides its own software package repository. It
contains the latest versions of packages like `MapServer
<http://mapserver.org/>`_, offers custom built `GDAL <http://gdal.org/>`_
packages with extra drivers enabled and provides bug-fixes for some libraries
including `libxml2 <http://xmlsoft.org/>`_. This repository is not mandatory,
but is highly recommended for all features of EOxServer to work correctly.

The repository is installed with the following commands:
::

    cd /etc/yum.repos.d/
    wget http://packages.eox.at/eox.repo
    rpm --import http://packages.eox.at/eox-package-maintainers.gpg
    yum update


Installation of required software packages
------------------------------------------

Now the required packages can be installed with this command:
::

    yum install gcc gdal gdal-devel gdal-python mapserver mapserver-python \
                libxml2 libxml2-python python-lxml sqlite sqlite-devel \
                python-pip

Further packages may be required if additional features (e.g: a full DBMS) are
desired.

When used with `spatialite <http://www.gaia-gis.it/spatialite/>`_ EOxServer
also requires `pysqlite <http://code.google.com/p/pysqlite/>`_. Unfortunately
pysqlite is built by default without a required parameter, thus it has to be
installed manually:
::

    wget http://pysqlite.googlecode.com/files/pysqlite-2.6.0.tar.gz
    tar xzf pysqlite-2.6.0.tar.gz
    cd pysqlite-2.6.0

Now `setup.cfg` needs to be opened with a text editor (like `vi`) and the line
::

    define=SQLITE_OMIT_LOAD_EXTENSION

has to be deleted or commented. Pysqlite can now be installed with:
::

    python setup.py install

For installation of Python packages `pip <www.pip-installer.org/>`_ is used,
which iself was installed in the previous step. It automatically resolves and
installs all of its dependencies, so a simple
::

    pip-python install eoxserver

suffices to install EOxServer itself.


Further Reading
---------------

#### link to autotest installation


