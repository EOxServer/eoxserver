.. RFC 12: Backends for the Data Access Layer
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
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

.. _rfc_12:

RFC 12: Backends for the Data Access Layer
==========================================

:Author: Stephan Krause
:Created: 2011-08-31
:Last Edit: $Date$
:Status: ACCEPTED
:Discussion: http://eoxserver.org/wiki/DiscussionRfc12

This RFC proposes the implementation of different backends that provide common
interfaces for data stored in different ways. It describes the first version
of the Data Access Layer implementation as well as changes to the Data
Integration Layer that are caused by the changes to the data model.

Introduction
------------

:doc:`rfc1` introduced the Data Access Layer as an abstraction layer for
access to different kinds of data storages. These are most notably:

* data stored on the local file system
* data stored on a remote file system that can be accessed using FTP
* data stored in a rasdaman database

The term *backend* has been coined for the part of the software implementing
data access to different storages.

This RFC discusses an architecture for these backends which is based on the
extension mechanisms discussed in :doc:`rfc2`. After the :ref:`rfc12_reqs`
section the architecture of the Data Access Layer is presented. It is structured
into a section describing the :ref:`rfc12_dal_model` which consists basically
of :ref:`rfc12_dal_storages` and :ref:`rfc12_dal_locations`.

Furthermore, the necessary changes to the Data Integration Layer are explained.
On the one hand these affect the :ref:`Data Model <rfc12_dil_model>` which is
altered considerably. On the other hand new structures
(:ref:`rfc12_dil_data_sources` and :ref:`rfc12_dil_data_packages`) that
provide more flexible solutions for data handling by the Data Integration Layer
and the layers that build on it.

.. _rfc12_reqs:

Requirements
------------

We may refer here to the :ref:`Backends Requirements<rfc1_req_backend>`
section as well as the description of the
:ref:`Data Access Layer<rfc1_dacc_lyr>` in :doc:`rfc1`. These state the need
for different backends to access local and remote data in different ways and
thus are the incentive for this RFC and the respective implementation.

.. _rfc12_dal_model:

Data Access Layer Data Model
----------------------------

The new database model for the Data Access Layer is shown in the figure below:

.. figure:: resources/rfc12/model_backends.png
   :width: 75%
   
   Data Access Layer Database Model

The core element of the Data Access Layer data model is the :class:`~.Location`.
A location designates a piece of data or metadata, actually any object that can
be stored in one of the :class:`~.Storage` facilities supported. Each backend
defines its own subclasses of :class:`~.Location` and :class:`~.Storage` to
represent repositories, databases, directories and objects stored therein.

The database model is embedded in wrappers that add logic to the model and 
provide common interfaces to access the data and metadata of the objects in
the backend. Internally, they make use of the extension mechanism of 
:doc:`RFC2 <rfc2>` to allow to find and get the right model records and
wrappers.

Last but not least, there is a :ref:`rfc12_dal_cache` for storing files
retrieved from remote hosts. The locations of the cache files are stored in
the database so EOxServer can keep track of them and implement an intelligent
cleanup process.

.. _rfc12_dal_storages:

Storages
--------

The :class:`~.Storage` subclasses represent different types of storage
facilities. In the database model, only FTP and rasdaman backends have their own
models defined that contain the information how to connect to the server. This
is not needed for locally mounted file systems, so the local backend does not
have a representation in the database.

The wrapper layer constructed on top of the database model on the other hand
knows three classes of storages that provide a common interface to access their
data:

* :class:`~.LocalStorage` which implements access to locally mounted file
  systems
* :class:`~eoxserver.backends.ftp.FTPStorage` which implements access to a
  remote FTP server
* :class:`~eoxserver.backends.rasdaman.RasdamanStorage` which implements access
  to a rasdaman database

Each of these storage classes is associated to a certain type of location.

The common interface for storages allows to retrieve their type and their
capabilities. Depending on these capabilities the storage classes also
provide methods for getting a local copy of the data and retrieving the size
of an object as well as scanning a directory for files. At the moment these
three methods are implemented by file-based backends only
(:class:`~.LocalStorage` and :class:`~eoxserver.backends.ftp.FTPStorage`).

.. _rfc12_dal_locations:

Locations
---------

Locations represent the points where to access single objects on a storage
facility. At the moment three types of locations corresponding to the three
storage types are implemented:

* :class:`~.LocalPath` defines a path on the locally mounted file system
* :class:`~.RemotePath` defines a path on a remote server reachable via FTP
* :class:`~.RasdamanLocation` defines a collection (database table) and oid
  corresponding to a single rasdaman array

Locations share a common interface that is closely related to the storage
interface. So, given the storage capabilities, it is possible to fetch a local
copy, retrieve the size of an object and scan the location for files. The
:class:`~.LocationWrapper` subclasses extend these interfaces to make storage
specific location information (e.g. host name for remote storages) accessible.

.. _rfc12_dal_cache:

File Cache
----------

With the :class:`~.CacheFileWrapper` class the Data Access Layer provides a
very simple file cache implementation at the moment that serves to cache 
remote files retrieved via FTP. The cache keeps track of the files it contains
using the :class:`~.CacheFile` model in the database.

So far, no synchronization for data access is implemented, i.e. threads
that are processing requests have no possibility to lock a cache file in order
to prevent it from being removed by another thread or process (e.g. periodical
cleanup process). This is foreseen for the future.

.. _rfc12_dil_model:

Changes to Data Integration Layer Data Model
--------------------------------------------

In order to use the new possibilities brought by the implementation of the Data
Access Layer, the Data Integration Layer had to be revised and changed
considerably. Up until now there has been a strong link between the type of 
coverage and the way it was stored. Datasets had to be stored as files in the
local file system whereas mosaics were stored in tile indexes. This strong link
had to be weakened to allow for new combinations.

The solution is a compromise between flexibility and simplicity. Although one
can think of many more combinations, we introduce three classes of so-called
:class:`~.DataPackage` objects. A data package combines a data resource with an
accompanying metadata resource. Both resources are referred to by
:class:`~.Location` subclass instances. Now the three data package classes are:

* :class:`~.LocalDataPackage` which combines a local data file with a local
  metadata file
* :class:`~.RemoteDataPackage` which combines a remote data file with a 
  remote metadata file (both reachable via FTP); it contains a
  :class:`~.CacheFile` reference for data in the local cache
* :class:`~.RasdamanDataPackage` which combines a rasdaman array with a local
  metadata file

Furthermore, the concept of data directories where to look up datasets
automatically had to be revised in order to use the new capabilities of the
Data Access Layer. They were replaced by a concept called data sources which
includes local and remote repositories. The :class:`~.DataSource` model combines
a local or remote :class:`~.Location` with a search pattern for dataset names.
Automatic lookup of rasdaman arrays is not foreseen at the moment.

Like most database objects, data packages and data sources are accessible using
wrappers that provide a common interface and add application logic to the data
model.

.. _rfc12_dil_data_packages:

Data Packages
-------------

The :class:`~.DataPackageInterface` defines methods for high-level and low-level
data access and for metadata extraction from the underlying datasets. It is
implemented by wrappers for local, remote and rasdaman data packages
(:class:`~.LocalDataPackageWrapper`, :class:`~.RemoteDataPackageWrapper` and
:class:`~.RasdamanDataPackageWrapper` respectively).

The implementation of the data package wrappers is based on the
`GDAL <http://www.gdal.org/>`_ library and its Python binding for data access
as well as for geospatial metadata extraction. It contains an
:meth:`~.DataPackageWrapper.open` method that returns a GDAL dataset providing
a uniform interface for raster data from different sources and formats. For
low-level data access a :meth:`~.DataPackageWrapper.getGDALDatasetIdentifier`
method is provided which allows to retrieve the correct connection string
for GDAL and thus to configure MapServer.

Geospatial metadata is read from the datasets themselves at the moment. Note
that this is not possible for rasdaman arrays so far, so automatic detection
and ingestion of these is not enabled.

EO Metadata is read from the accompanying metadata file and translated into the
internal data model of EOxServer. The existing metadata extraction classes have
been revised in order to comply with the extensible architecture presented in
:doc:`RFC 1 <rfc1>` and :doc:`RFC 2 <rfc2>`.

.. _rfc12_dil_data_sources:

Data Sources
------------

The wrappers for data sources (:class:`~.DataSourceWrapper`) provide the
capability to search a local or remote location for datasets. At the moment
only file lookup is implemented whereas automatic rasdaman array lookup has
been omitted. This is mostly due to the fact that rasdaman arrays do not
contain geospatial metadata and a separate mechanism has to be found to retrieve
this vital information.

The wrapper implementations provide a :class:`~.DataSourceWrapper.detect`
method that returns a list of :class:`~.DataPackageWrapper` objects with
which coverages are initialized (using the geospatial and EO metadata read from
the data package).

.. _rfc12_dil_ingest:

Ingestion and Synchronization
-----------------------------

The :class:`~.Synchronizer` implementation in
:mod:`eoxserver.resources.coverages.synchronize` has to be revised according to
the changes in the Data Access Layer and Data Integration Layer.

The implementations for containers, i.e. Rectified Stitched Mosaics and Dataset
Series, shall retrieve the data sources associated with a coverage and
use its :class:`~.DataSourceWrapper.detect` method to obtain the data packages
included in it. Rectified or Referenceable Datasets are constructed from these.
The interfaces of both should not change.

The interface of :class:`~.RectifiedDatasetSynchronizer` on the other hand will
have to change in order to allow for remote files to be ingested. In detail,
the :meth:`~.RectifiedDatasetSynchronizer.create` and
:meth:`~.RectifiedDatasetSynchronizer.update` methods will not expect a file
name any more, but a location wrapper instance (either
:class:`~.LocalPathWrapper` or :class:`~.RemotePathWrapper`). These can be
generated by a call to the :class:`~.LocationFactory` like this::

    from eoxserver.core.system import System
    
    factory = System.getRegistry.bind("backends.factories.LocationFactory")
    
    location = factory.create(
        type = "local",
        path = "<path/to/file>"
    )
    
    ...

Voting History
--------------

:Motion: To accept RFC 12
:Voting Start: 2011-09-06
:Voting End: 2011-09-15
:Result: +5 for ACCEPTED (including 1 +0)

Traceability
------------

:Requirements: N/A
:Tickets: N/A
