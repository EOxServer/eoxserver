.. _rfc_16:

RFC 16: Referenceable Grid Coverages
====================================

:Authors: Stephan Krause, Stephan Meissl, Fabian Schindler
:Created: 2011-11-24
:Last Edit: $Date$
:Status: IN PREPARATION
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc16

This RFC proposes an implementation for Referenceable Grid Coverages as
well as for the WCS 2.0 operations working on them.

Introduction
------------

Referenceable Grid Coverages are coverages whose internal grid structure
can be mapped to a coordinate reference system by some general transformation.
They differ from rectified grid coverages in that the coordinate transformation
is not necessarily affine.

In the context of Earth Observation, raw satellite data can be seen as
referenceable grid coverages. They are typically delivered as image files but
do not have an affine transformation from the image geometry to a georeferenced
coordinate system. The referencing or geocoding of the data is a very complex task
involving Earth Observation metadata, such as orbit data of the satellite, as well
as additional input such as Digital Elevation Models (DEMs).

EOxServer shall be able to deliver (subsets of) Earth Observation raw data in its 
original (referenceable grid) geometry using WCS 2.0 and EO-WCS. Furthermore, it
shall implement easily computable approximate referencing algorithms based on
ground control points (GCPs) in order to enable coordinate transformations and
rectified previews of the original data using WMS.

For the time being, the implementation will focus on SAR image data collected
by the ENVISAT-ASAR sensor made available by ESA.

Requirements
~~~~~~~~~~~~

The main requirement source for Referenceable Grid Coverage implementation in
EOxServer is the ESA O3S project. In the course of this project EOxServer shall be
installed in front of a small archive of ENVISAT-ASAR data. In a first step, we will
focus on covering the requirements of this use case, adding more generic referenceable
grid support in future iterations.

The ENVISAT-ASAR data are available in ENVISAT .N1 original format.

Delivery of the original referenceable grid data shall be supported using WCS 2.0 and
EO-WCS. Subsetting shall be supported in pixel coordinates (imageCRS) and in a 
coordinate reference system. The CRS subsets shall be mapped to pixel coordinates using
a simple coordinate transformation based on GCPs.

No support for resampling (``size`` and ``resolution``) or reprojection
(``outputcrs``) parameters is required as these are not applicable to referenceable
grid coverages.

At least GeoTIFF shall be supported as output format. GCP and metadata information
contained in the .N1 original file shall be preserved.

In order to support (rectified) WMS previews, a simple georeferencing algorithm based
on GCPs shall be implemented.

* Full support of WCS 2.0 parameters for rectified grid coverages (?)
* Full support of WMS 1.0 - 1.3

Implementation Details
~~~~~~~~~~~~~~~~~~~~~~

Split GetCoverage handler into handler for Rectified Datasets and Referenceable
Datasets.

For referenceable grid coverages, no extra meta data files are required as all
the required meta data is taken from the N1 file.

Referenceable Grid Coverages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Subsetting is always done in imageCRS using standard GDAL python bindings.

If the subsetting parameter uses geo-referenced coordinates the calculation of
the imageCRS coordinates is implemented using `GDAL <http://www.gdal.org>`_ in
C with `ctypes <http://docs.python.org/library/ctypes.html>`_ python bindings.

Rectified Grid Coverages
^^^^^^^^^^^^^^^^^^^^^^^^

Using cache of prerendered (with GDAL) images. Cache can be preseeded or filled
at runtime.

Remainder as with any other rectified grid coverage.
   
Voting History
--------------
  
<Voting Records or "N/A">
  
:Motion: <Text of the motion>
:Voting Start: <YYYY-MM-DD>
:Voting End: <YYYY-MM-DD>
:Result: <Result>
  
Traceability
------------
  
:Requirements: <links to requirements or "N/A">
:Tickets: <links to tickets or "N/A">
