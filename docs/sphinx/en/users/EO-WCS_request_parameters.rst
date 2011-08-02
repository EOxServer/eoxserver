.. EO-WCS Request Parameters

.. index::
   single: EO-WCS Request Parameters

.. _EO-WCS Request Parameters:

EO-WCS Request Parameters
=========================

The following tables provide an overview over the available EO-WCS request 
parameters for each operation supported by EOxServer.

Please see the :ref:`EOxServer Demonstration` for complete sample requests.

.. index::
   single: GetCapabilities (EO-WCS Request Parameters)

GetCapabilities
---------------

Request a Capabilities document.

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

Request a coverage metadata document.

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

Request a CoverageDescriptions document.

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
|                           | - cotainment = contains                                   |  "2006-08-22T09:22:00Z")&        |                                |
|                           |                                                           |  containment=contains            |                                |
|                           | Any combination thereof (but each value only once per     |                                  |                                |
|                           | request)                                                  |                                  |                                |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
| → section                 | see GetCapabilities                                       | - DatasetSeriesSummary           | O                              |
|                           |                                                           | - CoverageSummary                |                                |
|                           |                                                           | - All                            |                                |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

.. index::
   single: GetCoverage (EO-WCS Request Parameters)

GetCoverage
-----------

Request a coverage (for download).

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
| → format                  | Requested format of coverage to be returned, currently:   |  format=image/tiff               | M                              |
|                           |                                                           |                                  |                                |
|                           | - image/tiff                                              |                                  |                                |
|                           | - image/jpeg                                              |                                  |                                |
|                           | - image/png                                               |                                  |                                |
|                           | - image/gif                                               |                                  |                                |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
| → mediatype               | Coverage delivered directly as image file or enclosed in  | mediatype=multipart/mixed        | O                              |
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
| → rangesubset             | Subsetting in the range domain (e.g. Band-Subsetting)     | rangesubset=1,2,3                | O                              |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
| → outputcrs               | CRS for the requested output coverage                     | outputcrs=http://www.opengis.net/| O                              |
|                           |                                                           | def/crs/EPSG/0/3035              |                                |
|                           | - not present or                                          |                                  |                                |
|                           | - CRS                                                     |                                  |                                |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
|- → size  or               | Mutually exclusive per axis, either:                      |- size=Long(20)                   | O                              |
|- → resolution             |                                                           |- size=x(50)                      |                                |
|                           | - integer dimension of the requested coverage (per axis)  |- resolution=long(0.01)           |                                | 
|                           | - resolution of one pixel (per axis)                      |- resolution=y(0.3)               |                                |
+---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
|→ interpolation [2]_       | Interpolation method to be used                           | interpolation=bilinear           | O                              |
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
