.. EOxServer Operators' Guide
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

.. _EOxServer Operators' Guide:

EOxServer Operators' Guide
===========================

Basic Concepts
--------------

EOxServer is all about coverages - see the :doc:`basics` for a short
description.

In the language of the OGC Abstract Specification, coverages are mappings from
a domain set that is related to some area of the earth to a range set. So, the
data model for coverages contains information about the structure of the
domain set and of the range set (the so-called Range Type).

In the :ref:`ops_coverages` section below you find more detailed information
about what data and metadata is stored by EOxServer.

The actual data EOxServer deals with can be stored in different ways. These
storage facilities are discussed below in the section on
:ref:`ops_storage_backends`.

Operators have different possibilities to ingest data into the system. Using
the :ref:`ops_admin`, you can edit the contents of the EOxServer database.
Especially for batch processing using the :ref:`ops_cli` may be preferable.

.. _ops_storage_backends:

Storage Backends
----------------

EOxServer supports different kinds of data stores for coverage data:

* as an image file stored on the local file system
* as an image file stored on a remote FTP server
* as a raster array in a `rasdaman <http://www.rasdaman.org>`_ database

These different ways of storing data are called Storage Backends. Internally,
EOxServer uses the term Location as an abstraction for the different ways
access to the data is described. Each storage backend has its own type of
Locations that is described in the following subsections.

Local
~~~~~

A path on the local filesystem is the most straightforward way to define the
location of a resource. You can use relative paths as well as absolute paths.
Please keep in mind that relative paths are interpreted as being relative to
the working directory of the process EOxServer runs in. For Apache processes,
for instance, this is usually the root directory ``/``.

FTP Repositories
~~~~~~~~~~~~~~~~

EOxServer allows to define locations on a remote FTP server. This is useful
if you do not want to transfer a whole large archive to the machine EOxServer
runs on. In that case you can define a remote path that consists of information
about the FTP server and the path relative to the root directory of the
FTP repository.

An FTP Storage record - as it is called in EOxServer - contains the URL of the
server and optional port, username and password entries.

Resources stored on an FTP ...

Rasdaman Databases
~~~~~~~~~~~~~~~~~~

.. _ops_coverages:

Coverages
---------

Range Types
~~~~~~~~~~~

Rectified Datasets
~~~~~~~~~~~~~~~~~~

Referenceable Datasets
~~~~~~~~~~~~~~~~~~~~~~

Rectified Stitched Mosaics
~~~~~~~~~~~~~~~~~~~~~~~~~~

Dataset Series
~~~~~~~~~~~~~~

.. _ops_admin:

Admin Client
------------

.. _ops_cli:

Command Line Tools
------------------
