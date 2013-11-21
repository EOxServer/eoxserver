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

:Author: Stephan Krauses, Martin Pačes
:Created: 2012-05-08
:Last Edit: $Date$
:Status: ACCEPTED 
:Discussion: n/a

This RFC proposes modifications of the EOxServer allowing configuration of

* the supported output formats for WMS and WCS
* the supported CRSes for WMS and WCS

The RFC presents the rationale and proposes data model changes and new global
configuration options. 


Introduction
------------

The reason for preparation of this RFC is the need to change the way 
how the supported (file) formats and CRSes (CRS - Coordinate Reference Systems) 
for raster data are handled by the EOxServer's WCS and WMS services to assure
compliance to OGC standards, interoperability and configurability of the
services. 

In case of WMS, the formats and CRSes shall be listed in the WMS Capabilities.

In case of WCS, the supported formats and CRSes shall be reported by the WCS
Capabilities  (per service parameters) and in the Coverage Descriptions (per
coverage parameters). Compatibility with the WCS 2.0.1 corrigendum and the
upcoming WCS 2.0 CRS Extension document shall be assured.

Currently, only the native CRS of a dataset is reported in the metadata and 
only a small hard-coded set output file format is announced as
supported (JPEG2000, HDF4, netCDF and GeoTIFF for WCS). Hence, there is no way
to configure these parameters. 

Furthermore, the underlying MapServer implementation does not return proper OWS
exceptions if an CRS not advertised in the service capabilities or coverage
descriptions is requested. 

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
coverage basis whereas all others standards allow to report supported formats 
in the global service metadata only.

The WCS 2.0.1 corrigendum introduces the concept of native CRSes and formats
which are reported in the coverage description. The native CRS is the one the
domain set uses. 

Counterintuitively, the WCS 2.0.1 native file format is not necessarily the same
as the file format of the stored data. Since not all source file formats are
supported as the output file format (e.g. ENVISAT N1), it is rather the default
format delivered when there no specific file format is requested (omitting the
``FORMAT`` parameter in GetCoverage requests).

Supported Output Formats and WCS 2.0.1 Native Format
----------------------------------------------------

As most services (all but WCS 1.1.2, see the table above) allow output
format configuration only per service instance, we propose that the list of
supported formats shall be kept in the global configuration. This can be most
easily done by adding new items to the global configuration file
``conf/eoxserver.conf``.

Due to the nature of the data transmitted by these services the configuration
should be separate for WMS and WCS.

The EOxServer implementation for WCS 2.0 and EO-WCS requires three parameters
to be defined for each supported format: 

* the MIME type
* the name of the GDAL driver
* the default file extension

The possible format choices are restricted by the capabilities of the underlying
SW components (MapServer and GDAL). The list of allowed formats can be fount at
http://www.gdal.org/formats_list.html.

Although the source format (i.e. the actual format of the stored data) could be
determined for each coverage individually at runtime it is preferable
to store this information in the database for performance reasons.

The actual native format announced by the WCS 2.0.1 compliant coverage
description can differ from the source format as not every source format can be
used as output format. 

The implementation of the native format reporting for WCS 2.0.1 requires that
EOxServer knows the mapping from the source to WCS 2.0.1 native format. As this
mapping varies depending on the GDAL version, available external libraries or
simply on the preference of the instance administrator the actual mapping shall
be configurable, i.e., it shall be a configuration item in
``conf/eoxserver.conf``.

For all the proposed configuration items reasonable default shall be provided. 

Supported CRSes
---------------

All services but WCS 2.0.1 support per-coverage or per-layer reporting of
CRSes. The WCS 2.0 CRS extension is not yet finished and it is suggested that 
it, too, should allow for CRS metadata being reported in the coverage
description, although this provision is not included in the current draft of
the document.

Currently, the EOxServer implementation of WMS and WCS sets the ``ows_srs``
MapServer parameter to the original CRS of a coverage. Thus the currently only
announced CRS is the native CRS of the dataset.

This RFC proposes to introduce global configuration items for WCS and WMS,
respectively, allowing definition of CRSes to be reported in addition
to the native CRS. These CRSes shall also be used for EO-WMS layers
corresponding to DatasetSeries.

In order to report a native CRS for Referenceable Grid Coverages
the data model needs to be changed to include the SRID of the GCP projection of
ReferenceableDatasets.

Proposed Implementation
-----------------------

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
* an optional mapping of source format to for native format reporting in WCS 2.0.1

The list of GDAL formats shall be configured in a CSV-like separate
configuration file in ``conf/formats.conf``. Each line in the file shall
correspond to a given format. The syntax is as follows::

  <GDAL driver name>,<MIME type>,<either "rw" for writable or "ro" for read-only formats>,<default file extension>
  
e.g.::

  GTiff,image/tiff,rw,.tiff

Empty lines shall be ignored as well as any comments started by single ``#``
(hash) character and ended by the end of the line. 

A default configuration (``default_formats.conf``) and a template
(``TEMPLATE_formats.conf``) shall be included in the ``eoxserver/conf``
directory. The default configuration shall only be used as a fall-back if no
``formats.conf`` file is available in the instance ``conf`` directory.

The other configuration settings shall be defined in ``conf/eoxserver.conf``::

  [services.ows.wcs]
  supported_formats=<MIME type>[,<MIME type>,...]
  
  [services.ows.wms]
  supported_formats=<MIME type>[,<MIME type>,...]

  [services.ows.wcs.wcs20]
  default_native_format=<MIME type>
  source_to_native_format_map=[<src MIME type>,<dst MIME type>[,<src MIME type>,<dst MIME type>,...] 

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
* map GDAL driver names to MIME types and vice versa
* map MIME type (i.e., format) to default file extensions 
* map source format to WCS 2.0.1 native format 

Changes to the Service Implementations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The WMS and WCS modules need to be altered to use the new global settings in
the service and layer / coverage configuration.

The hard-coded format settings in WCS 2.0
(:mod:`eoxserver.services.ows.wcs.wcs20.getcov` module) shall be removed.

The GDAL driver name obtained from the :class:`~.DataPackageWrapper`
implementation  shall be translated at runtime to the respective MIME type using
the functionality provided by :mod:`eoxserver.resources.coverages.formats`
module (inluding the translation from the source MIME type to the WCS 2.0.1
native MIME type). 

Changes to the Administration Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``create_instance`` command shall copy the template format configuration
file to the ``conf`` directory of the instance.

The Coverage Managers shall store the GDAL driver name of the native format in
the database.

Voting History
--------------

:Motion: To accept RFC 17
:Voting Start: 2012-05-11 
:Voting End: 2012-05-17
:Result: +5 for ACCEPTED

Traceability
------------

:Requirements: N/A
:Tickets: N/A
