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

Resources stored on an FTP server are transferred only when they are needed.
There is however a cache for transferred files on the machine EOxServer runs on.

Rasdaman Databases
~~~~~~~~~~~~~~~~~~

The third backend supported at the moment are
`rasdaman <http://www.rasdaman.org>`_ databases. A rasdaman location consists
of rasdaman database connection information and the collection of the
corresponding resource.

The rasdaman storage records contain hostname, port, database name, user and
password entries.

The data is retrieved from the database using the rasdaman GDAL driver (see
:doc:`install` for further information).

.. _ops_coverages:

Coverages
---------

EOxServer coverages fall into three main categories:

* :ref:`ops_rect_ds`
* :ref:`ops_ref_ds`
* :ref:`ops_rect_mosaics`

In addition there is the :ref:`ops_ds_series` type which corresponds to an
inhomogeneous collection of coverages.

.. _ops_range_types:

Range Types
~~~~~~~~~~~

Every coverage has a ramge type that describes the structure of the data.
Each range type has a given data type; the following data types are supported:

============== ===============
Data Type Name Data Type Value
============== ===============
Unknown        0
Byte           1
UInt16         2
Int16          3
UInt32         4
Int32          5
Float32        6
Float64        7
CInt16         8
CInt32         9
CFloat32       10
CFloat64       11
============== ===============

A range type contains one or more bands. For each band you may specify a name,
an identifier and a definition that describes the property measured
(e.g. radiation). Furthermore, you can define nil values for each band (i.e.
values that indicate that there is no measurement at the given position).

This range type metadata is used in the coverage description metadata that is
returned by WCS operations and for configuring WMS layers.

.. _ops_eo_md:

EO Metadata
~~~~~~~~~~~

Earth Observation (EO) metadata records are stored for each EO coverage
and Dataset Series. They contain the acquisition begin and end time as well
as the footprint of the coverage. The footprint is a polygon that describes the
outlines of the area covered by the coverage.

.. _ops_rect_ds:

Rectified Datasets
~~~~~~~~~~~~~~~~~~

Rectified Datasets are EO coverages whose domain set is a rectified grid. In
practice, this applies to ortho-rectified satellite data. The rectified grid
is described by the EPSG SRID of the coordinate reference system, the extent
and pixel size of the coverage.

Rectified Datasets can be added to Dataset Series and Rectified Stitched
Mosaics.

.. _ops_ref_ds:

Referenceable Datasets
~~~~~~~~~~~~~~~~~~~~~~

Referenceale Datasets are EO coverages whose domain set is a referenceable grid.
That means that there is some general transformation betweem the grid cell
coordinates and coordinates in an earth-bound spatial reference system. This
applies for satellite data in its original geometry.

At the moment, EOxServer supports only referenceable datasets that contain
ground control points (GCPs) in the data files. Simple approximative
transformations based on these GCPs are used to generate rectified views on the
data for WMS and to calculate subset bounds for WCS GetCoverage requests. Note
that these transformations can be very inaccurate in comparison to an actual
ortho-rectification of the coverage.

.. _ops_rect_mosaics:

Rectified Stitched Mosaics
~~~~~~~~~~~~~~~~~~~~~~~~~~

Rectified Stitched Mosaics are EO coverages that are composed of a set of
homogeneous Rectified Datasets. That means, the datasets must have the same
range type and their domain sets must be subsets of the same rectified grid.

When creating a Rectified Stitched Mosaic a homogeneous coverage is generated
from the contained Rectified Datasets. Where datasets overlap the most recent
one as indicated by the acquisition timestamps in the EO metadata is shown on
top hiding the others.

.. ops_ds_series:

Dataset Series
~~~~~~~~~~~~~~

.. _ops_admin:

Admin Client
------------

.. _ops_cli:

Command Line Tools
------------------
