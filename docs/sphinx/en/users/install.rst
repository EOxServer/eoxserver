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

To use EOxServer it must be installed first. Following this guide will
give you a working software installation. 

.. seealso:: 

    * :ref:`CentOSInstallation`
            for specific installation on CentOS.
    * :ref:`InstanceCreation` 
            to configure an instance of EOxServer after successful installation.
    * :ref:`OperationalInstallation` 
            to configure an operational EOxServer installation.

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

  +-----------+------------------+---------------------------------------------+
  | Software  | Required Version | Description                                 |
  +===========+==================+=============================================+
  | Python    | >= 2.5, < 3.0    | Scripting language                          |
  |           | (>=2.6.5 for     |                                             |
  |           | Django 1.5)      |                                             |
  +-----------+------------------+---------------------------------------------+
  | Django    | >= 1.4 (1.5 for  | Web development framework written in        |
  |           | PostGIS 2.0      | Python including the GeoDjango extension    |
  |           | support)         | for geospatial database back-ends.          |
  +-----------+------------------+---------------------------------------------+
  | GDAL      | >= 1.7.0 (1.8.0  | Geospatial Data Abstraction Library         |
  |           | for rasdaman     | providing common interfaces for accessing   |
  |           | support)         | various kinds of raster and vector data     |
  |           |                  | formats and including a Python binding      |
  |           |                  | which is used by EOxServer                  |
  +-----------+------------------+---------------------------------------------+
  | GEOS      | >= 3.0           | GEOS (Geometry Engine - Open Source) is a   |
  |           |                  | C++ port of the  Java Topology Suite (JTS). |
  +-----------+------------------+---------------------------------------------+
  | libxml2   | >= 2.7           | Libxml2 is the XML C parser and toolkit     |
  |           |                  | developed for the Gnome project.            |
  +-----------+------------------+---------------------------------------------+
  | lxml      | >= 2.2           | The lxml XML toolkit is a Pythonic binding  |
  |           |                  | for the C libraries libxml2 and libxslt.    |
  +-----------+------------------+---------------------------------------------+
  | MapServer | >= 6.2           | Server software implementing various OGC    |
  |           | (works partly    | Web Service interfaces including WCS and    |
  |           | with 6.0)        | WMS. Includes a Python binding which is     |
  |           |                  | used by EOxServer.                          |
  +-----------+------------------+---------------------------------------------+

The Python bindings of the GDAL, MapServer (MapScript) and libxml2 libraries are
required as well. 

EOxServer is written in `Python <http://www.python.org/>`_ and uses the
`Django <https://www.djangoproject.com>`_ framework which requires a
Python version from 2.5 to 2.7. Due to backwards incompatibilities in Python
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
`Django database notes <https://docs.djangoproject.com/en/1.4/ref/databases/>`_
and `GeoDjango installation
<https://docs.djangoproject.com/en/1.4/ref/contrib/gis/install/>`_.

.. _table_eoxserver_db_dependencies:
.. table:: Database Dependencies

    +------------+------------------+------------------------------------------+
    | Backend    | Required Version | Required extensions/software             |
    +============+==================+==========================================+
    | SQLite     | >= 3.6           | spatialite (>= 2.3), pysqlite2 (>= 2.5), |
    |            |                  | GEOS (>= 3.0), PROJ.4 (>= 4.4)           |
    +------------+------------------+------------------------------------------+
    | PostgreSQL | >= 8.1           | PostGIS (>= 1.3), GEOS (>= 3.0),         |
    |            |                  | PROJ.4 (>= 4.4), psycopg2 (== 2.4.1)     |
    +------------+------------------+------------------------------------------+

.. _install_sw:

.. _installing_eoxserver:

Installing EOxServer
--------------------

There are several easy options to install EOxServer:

* Install an official release of EOxServer, the best approach for users who
  want a stable version and aren't concerned about running a slightly older
  version of EOxServer. You can install EOxServer either from

  * `PyPI - the Python Package Index <http://pypi.python.org/pypi>`_ using
    `pip <http://www.pip-installer.org/en/latest/index.html>`_::

      sudo pip install eoxserver

  * or from the `EOxServer download page <http://eoxserver.org/wiki/Download>`_
    using pip::

      sudo pip install http://eoxserver.org/export/head/downloads/EOxServer-<version>.tar.gz

    or manual::

      wget http://eoxserver.org/export/head/downloads/EOxServer_full-<version>.tar.gz .
      tar xvfz EOxServer-<version>.tar.gz
      cd EOxServer-<version>
      sudo python setup.py install

  * or binaries provided by your operating system distribution e.g. 
    :ref:`CentOS <CentOSInstallation>`.

* Install the latest development version, the best option for users who
  want the latest-and-greatest features and aren't afraid of running
  brand-new code. Make sure you have `Subversion
  <http://subversion.tigris.org/>`_ installed and install EOxServer's
  main development branch (the trunk) using pip::

    sudo pip install svn+http://eoxserver.org/svn/trunk

  or manual::

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

Now that EOxServer is properly installed the next step is to :ref:`create and
configure a service instance <InstanceCreation>`. 

Upgrading EOxServer
-------------------

To upgrade an existing installation of EOxServer simply add the `--upgrade`
switch to your pip command e.g.::

  sudo pip install --upgrade eoxserver

or rerun the manual installation as explained above.

Please carefully follow the :ref:`migration/update procedure <Migration>` 
corresponding to your version numbers for any configured EOxServer instances 
in case of a major version upgrade.
