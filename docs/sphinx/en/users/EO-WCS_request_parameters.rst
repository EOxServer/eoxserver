.. EO-WCS Request Parameters
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
   single: EO-WCS Request Parameters

.. _EO-WCS Request Parameters:

EO-WCS Request Parameters
=========================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

The following tables provide an overview over the available EO-WCS request 
parameters for each operation supported by EOxServer.

Please see EOxServer's :ref:`Demonstration` for complete sample requests.

.. index::
   single: GetCapabilities (EO-WCS Request Parameters)

GetCapabilities
---------------

Table: ":ref:`table_eo-wcs_request_parameters_getcapabilities`" below lists all 
parameters that are available with Capabilities requests.

.. _table_eo-wcs_request_parameters_getcapabilities:
.. table:: EO-WCS GetCapabilities Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | → service                 | Requested service                                         |   WCS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → request                 | Type of request                                           |   GetCapabilities                | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → version [1]_            | Version number                                            |   2.0.0                          | O                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → acceptVersions [1]_     | Prioritized sequence of one or more specification         |   2.0.0, 1.1.2, 1.0.0            | O                              |
    |                           | versions accepted by the client, with preferred versions  |                                  |                                |
    |                           | listed first (first supported version will be used)       |                                  |                                |
    |                           | version1[,version2[,...]]                                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → sections                | Comma-separated unordered list of zero or more names of   | - DatasetSeriesSummary           | O                              |
    |                           | zero or more names of sections of service metadata        | - CoverageSummary                |                                |
    |                           | document to be returned in service metadata document.     | - Contents                       |                                |
    |                           | Request only certain sections of Capabilities             | - All                            |                                |
    |                           | Document section1[,section2[,...]]                        | - ServiceIdentification          |                                |
    |                           |                                                           | - ServiceProvider                |                                |
    |                           |                                                           | - OperationsMetadata             |                                |
    |                           |                                                           | - Languages                      |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → updateSequence          | Date of last issued GetCapabilities request; to receive   |   "2011-01-17"                   | O                              |
    |                           | new document only if it has changed since                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

.. index::
   single: DescribeCoverage (EO-WCS Request Parameters)

DescribeCoverage
----------------

Table: ":ref:`table_eo-wcs_request_parameters_describecoverage`" below lists all
parameters that are available with DescribeCoverage requests.

.. _table_eo-wcs_request_parameters_describecoverage:
.. table:: EO-WCS DescribeCoverage Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | → service                 | Requested service                                         |   WCS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → request                 | Type of request                                           |   DescribeCoverage               | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → version [1]_            | Version number                                            |   2.0.0                          | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → coverageId              | NCName(s):                                                |                                  | M                              |
    |                           |                                                           |                                  |                                |
    |                           | - valid coverageID of a Dataset                           |                                  |                                |
    |                           | - valid coverageID of a StichedMosaic                     |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

.. index::
   single: DescribeEOCoverageSet (EO-WCS Request Parameters)

DescribeEOCoverageSet
---------------------

Table: ":ref:`table_eo-wcs_request_parameters_describeeocoverageset`" below 
lists all parameters that are available with DescribeEOCoverageSet requests.

.. _table_eo-wcs_request_parameters_describeeocoverageset:
.. table:: EO-WCS DescribeEOCoverageSet Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | → service                 | Requested service                                         |   WCS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → request                 | Type of request                                           |   DescribeEOCoverageSet          | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → version [1]_            | Version number                                            |   2.0.0                          | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → eoId                    | Valid eoId:                                               |                                  | M                              |
    |                           |                                                           |                                  |                                |
    |                           | - using the coverageId of a Datatset                      |                                  |                                | 
    |                           | - using the eoId of a DatatsetSeries                      |                                  |                                | 
    |                           | - using the coverageId of a StitchedMosaic                |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → subset                  | Allows to constrain the request in each dimensions and    |- Lat,http://www.opengis.net/def/ | O                              |
    |                           | define how these  parameters are applied.                 |  crs/EPSG/0/4326(32,47)          |                                |
    |                           |                                                           |- Long,http://www.opengis.net/def/|                                |
    |                           | The spatial constraint is expressed in WGS84, the         |  crs/EPSG/0/4326(11,33)&         |                                |
    |                           | temporal constraint in ISO 8601.                          |- phenomenonTime("2006-08-01",    |                                |
    |                           |                                                           |  "2006-08-22T09:22:00Z")         |                                |
    |                           | Spatial trimming:  Name of an coverage axis (Long or Lat) |- Lat,http://www.opengis.net/def/ |                                |
    |                           | Temporal trimming: phenomenonTime                         |  crs/EPSG/0/4326(32,47)&         |                                |
    |                           | Plus optional either:                                     |  Long,http://www.opengis.net/def/|                                |
    |                           |                                                           |  crs/EPSG/0/4326(11,33)&         |                                |
    |                           | - containment = overlaps (default)                        |  phenomenonTime("2006-08-01",    |                                |
    |                           | - containment = contains                                  |  "2006-08-22T09:22:00Z")&        |                                |
    |                           |                                                           |  containment=contains            |                                |
    |                           | Any combination thereof (but each value only once per     |                                  |                                |
    |                           | request)                                                  |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → containment             | see `subset` parameter                                    | - overlaps (default)             | O                              |
    |                           |                                                           | - contains                       |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → section                 | see GetCapabilities                                       | - DatasetSeriesSummary           | O                              |
    |                           |                                                           | - CoverageSummary                |                                |
    |                           |                                                           | - All                            |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → count                   | Limits the maximum number of DatasetDescriptions returned |   10                             | O                              |
    |                           | in the EOCoverageSetDescription.                          |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+


.. index::
   single: GetCoverage (EO-WCS Request Parameters)

GetCoverage
-----------

Table: ":ref:`table_eo-wcs_request_parameters_getcoverage`" below lists all 
parameters that are available with GetCoverage requests.

.. _table_eo-wcs_request_parameters_getcoverage:
.. table:: EO-WCS GetCoverage Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | → service                 | Requested service                                         |   WCS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → request                 | Type of request                                           |   GetCoverage                    | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → version [1]_            | Version number                                            |   2.0.0                          | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → coverageId              | NCName(s):                                                |                                  | M                              |
    |                           |                                                           |                                  |                                |
    |                           | - valid coverageID of a Dataset                           |                                  |                                |
    |                           | - valid coverageID of a StichedMosaic                     |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → format                  | Requested format of coverage to be returned, currently:   |   image/tiff                     | M                              |
    |                           |                                                           |                                  |                                |
    |                           | - image/tiff                                              |                                  |                                |
    |                           | - image/jpeg                                              |                                  |                                |
    |                           | - image/png                                               |                                  |                                |
    |                           | - image/gif                                               |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → mediatype               | Coverage delivered directly as image file or enclosed in  |   multipart/mixed                | O                              |
    |                           | GML structure                                             |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | - not present or                                          |                                  |                                |
    |                           | - multipart/mixed                                         |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → subset                  | Trimming of coverage dimension (no slicing allowed!)      |- x(400,200)                      | O                              |
    |                           |                                                           |- Lat(12,14)                      |                                |
    |                           | - the label of a coverage axis                            |- Long,http://www.opengis.net/def/|                                |
    |                           |                                                           |  crs/EPSG/0/4326(17,17.4)        |                                |
    |                           |   + plus either:                                          |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           |     * pixel coordinates                                   |                                  |                                |
    |                           |     * without CRS (→ original projection)                 |                                  |                                |
    |                           |     * with CRS (→ reprojecting)                           |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → rangesubset             | Subsetting in the range domain (e.g. Band-Subsetting).    | - 1,2,3                          | O                              |
    |                           |                                                           | - Blue,Green,Red                 |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → outputcrs               | CRS for the requested output coverage                     | http://www.opengis.net/def/      | O                              |
    |                           |                                                           | crs/EPSG/0/3035                  |                                |
    |                           | - not present or                                          |                                  |                                |
    |                           | - CRS                                                     |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    |- → size  or               | Mutually exclusive per axis, either:                      |- size=Long(20)                   | O                              |
    |- → resolution             |                                                           |- size=x(50)                      |                                |
    |                           | - integer dimension of the requested coverage (per axis)  |- resolution=long(0.01)           |                                | 
    |                           | - resolution of one pixel (per axis)                      |- resolution=y(0.3)               |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | → interpolation [2]_      | Interpolation method to be used                           | bilinear                         | O                              |
    |                           |                                                           |                                  |                                | 
    |                           | - nearest (default)                                       |                                  |                                |
    |                           | - bilinear                                                |                                  |                                |
    |                           | - average                                                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

\

.. [1]  Version, acceptVersions: Support for EO-WCS is available only together 
        with WCS version 2.0.0.

.. [2] Interpolation: (Note: Resampling options other than NEAREST can 
        dramatically slow down raster processing). The default (and fastest) is 
        NEAREST. Replaces the target pixel with its NEAREST Neighbor. 
        AVERAGE will compute the average pixel value of all pixels in the region 
        of the disk file being mapped to the output pixel (or possibly just a 
        sampling of them). Generally AVERAGE can be desirable for reducing noise 
        in dramatically downsampled data, and can give something approximating 
        anti-aliasing for black and white linework. BILINEAR will compute a 
        linear interpolation of the four pixels around the target location. 
        BILINEAR can be helpful when oversampling data to give a smooth 
        appearance.
