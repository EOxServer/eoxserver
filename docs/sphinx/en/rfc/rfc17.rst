.. RFC 17
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
.. _rfc_17:

RFC 17: Configuration of Supported Output Formats and CRSes
===========================================================

:Author: Stephan Krauses
:Created: 2012-05-08
:Last Edit: $Date$
:Status: PENDING
:Discussion: n/a

In this RFC, modifications to the EOxServer data model shall be discussed which
allow to configure

* the supported output formats for WMS and WCS
* the supported CRSes for WMS and WCS



Introduction
------------

The supported formats and CRSes shall be reported in the GetCapabilities metadata
of the services and in coverage descriptions.

At the moment, only the native CRS of a coverage is reported in the metadata,
and only a few hard-coded output formats (JPEG2000, HDF4, netCDF and GeoTIFF for
WCS) are supported. Note that MapServer does not return OWS exceptions, however,
if a CRS is requested that has not been reported in the metadata; so the goal of
this RFC is primarily to assure standards compliance, interoperability and
configurability of the services.

The proposed solution adds configuration items for global settings and some
database fields for individual configuration of coverages.

Compatibility with the WCS 2.0.1 corrigendum and the upcoming WCS 2.0 CRS
extension shall be assured.

Supported CRSes and Output Formats in OGC Web Services
------------------------------------------------------

The table below gives an overview over the support for reporting CRS and
output format metadata in different standards implemented by EOxServer.

.. table:: Support for CRS and output format metadata

    +---------------------+---------------+-------------------+
    | Service and Version | Supported CRS | Supported Formats |
    +=====================+===============+===================+
    | WMS 1.1.0           | per layer     | per service       |
    +---------------------+---------------+-------------------+
    | WMS 1.1.1           | per layer     | per service       |
    +---------------------+---------------+-------------------+
    | WMS 1.3.0           | per layer     | per service       |
    +---------------------+---------------+-------------------+
    | WCS 1.1.2           | per coverage  | per coverage      |
    +---------------------+---------------+-------------------+
    | WCS 2.0.0           | n/a           | n/a               |
    +---------------------+---------------+-------------------+
    | WCS 2.0.1           | per service   | per service       |
    +---------------------+---------------+-------------------+

All services but the WCS 2.0 CRS extension (listed under WCS 2.0.1) allow for
reporting CRSes for each coverage / layer individually; the CRS extension could
still be amended, though.

On the other hand, only WCS 1.1.2 allows output format specification on a per
coverage basis whereas all others only report supported formats in the global
service metadata.

In WCS 2.0.1, there is also the concept of native CRSes and formats which are
reported in the coverage descriptions. The native CRS is the one the domain set
uses. The native format has been introduced with the corrigendum.

Somewhat contrary to what one might expect, the WCS 2.0.1 native format is not
necessarily the one stored on the disk as the WCS service might not be able to
deliver the data in that format (e.g. ENVISAT .N1). Instead, it is  the default
format in which the data will delivered if the ``FORMAT`` parameter is omitted.
The standard states that this format should return the data unaltered.

Supported Output Formats and WCS 2.0.1 Native Format
----------------------------------------------------

As most services (all but WCS 1.1.2) allow output format configuration only
per service instance, the list of supported formats shall be kept in the
global configuration. At the moment, this is most easily done by adding
settings to the configuration file ``conf/eoxserver.conf``.

Due to the nature of the data transmitted by the different services, the
configuration should be separate for WMS and WCS.

The EOxServer implementation for WCS 2.0 and EO-WCS expects three parameters
for each output format:

* the MIME type
* the name of the GDAL driver
* the default file extension

The use of MapServer/GDAL restricts the possible choices to formats with
write support in GDAL. These can be found at
http://www.gdal.org/formats_list.html.

The native format has to be determined for each coverage individually. Although
this could be done at runtime, storing the native format in the database at
registration time is preferrable for performance reasons. Note that the format
stored in the database is not necessarily the one reported as native format
in the WCS 2.0.1 coverage descriptions, as only writable formats can be
reported. In case the original data format is read-only, a global default
shall be used instead. This, too, shall be a configuration item in
``conf/eoxserver.conf``.

The implementation of the native format reporting for WCS 2.0.1 requires that
EOxServer know which formats are writable and which are read-only. This
depends on the GDAL version used and also on the individual installation as
some drivers are only optional and depend on external libraries. So, this
list has to be configurable as well, but EOxServer should provide a default.

Supported CRSes
---------------

All services but WCS 2.0.1 support per-coverage or per-layer reporting of
CRSes. The WCS 2.0 CRS extension is not yet finished and it is suggested that
it, too, should allow for CRS metadata being reported in the coverage
description.

The EOxServer implementation of WMS and WCS does already set the
``ows_srs`` MapServer parameter to the original CRS of a coverage. The question
is which additional CRSes shall be supplied.

The proposed solution is to introduce global configuration items for WCS and WMS
respectively that allow to define additional CRSes that are always reported
alongside the native CRS. These should also be used for layers corresponding to
DatasetSeries in the EO-WMS implementation.

In order to be able to report a native CRS for Referenceable Grid Coverages,
the data model shall be changed to include the SRID of the GCP projection of
ReferenceableDatasets.

Implementation Details
----------------------

Changes to the Data Model
~~~~~~~~~~~~~~~~~~~~~~~~~

For implementing the native format reporting in WCS 2.0.1, an additional
field ``gdal_driver_name`` on the :class:`~.LocalDataPackage` and
:class:`~.RemoteDataPackage` model shall be added. For the
:class:`~.RasdamanDataPackage` model, a dedicated database field is not
necessary as the GDAL driver is already known because of the nature of the
data package. The driver name should be provided by the
:class:`~.DataPackageWrapper` implementation.

In order to report the native CRS of Referenceable Datasets, a ``srid`` field
shall be added to the :class:`~.ReferenceableDatasetRecord` model.

Changes to the Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following new configuration settings are needed for output format handling:

* a list of GDAL formats with MIME types and a flag indicating if the format
  is writable or read-only
* a list of MIME types to be reported as supported formats in WMS
* a list of MIME types to be reported as supported formats in WCS
* a default format MIME type to be used for native format reporting in WCS 2.0.1

The list of GDAL formats shall be configured in a CSV-like separate
configuration file in ``conf/formats.conf``. Each line in the file shall
correspond to a given format. The syntax is as follows::

  <GDAL driver name>,<MIME type>,<either "rw" for writable or "ro" for read-only formats>,<default file extension>
  
e.g.::

  GTiff,image/tiff,rw,tiff

Lines starting with ``#`` shall be ignored.

A default configuration (``default_formats.conf``) and a template
(``TEMPLATE_formats.conf``) shall be included in the ``eoxserver/conf``
directory. The default configuration shall only be used as a fallback if no
``formats.conf`` file is available in the instance ``conf`` directory.

The other configuration settings shall be defined in ``conf/eoxserver.conf``::

  [services.ows.wcs]
  supported_formats=<MIME type>[,<MIME type>,...]
  
  [services.ows.wms]
  supported_formats=<MIME type>[,<MIME type>,...]

  [services.ows.wcs.wcs20]
  default_native_format=<MIME type>

The following new configuration settings are needed for CRS handling:

* a list of supported CRS IDs (SRIDs) for WMS layers
* a list of supported CRS IDs (SRIDs) for WCS coverages

The respective entries in ``conf/eoxserver.conf``::

  [services.ows.wcs]
  supported_crs=<SRID>[,<SRID>,...]
  
  [services.ows.wms]
  supported_crs=<SRID>[,<SRID>,...]

Default settings shall be defined in ``eoxserver/conf/default.conf``.

Module eoxserver.resources.coverages.formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to support output format handling a dedicated module shall be
implemented that

* reads the list of GDAL formats from the configuration files
* translates GDAL driver names to MIME types and vice versa
* returns the default file extensions for a given MIME type / format

Changes to the Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The WMS and WCS modules need to be altered to use the new global settings in
the service and layer / coverage configuration. The hard-coded format settings
in WCS 2.0
(:mod:`eoxserver.services.ows.wcs.wcs20.getcov` module) need to be replaced.

For WCS 2.0.1 native format reporting the GDAL driver name obtained from the
:class:`~.DataPackageWrapper` implementation should be translated at runtime to
the respective MIME type reported in the service metadata using the global
settings provided in the configuration file (and using the functions or methods
defined in the :mod:`eoxserver.resources.coverages.formats` module). If it
cannot be found there or if the format is read-only, the default format defined
in the configuration file (``default_native_format`` setting) shall be used.

Changes to the Administration Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``create_instance`` command shall copy the template format configuration
file to the ``conf`` directory of the instance.

The Coverage Managers shall store the GDAL driver name of the native format in
the database.

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
