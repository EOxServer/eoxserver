.. _rfc_16:

RFC 16: Referenceable Grid Coverages
====================================

:Authors: Stephan Krause, Stephan Meissl, Fabian Schindler
:Created: 2011-11-24
:Last Edit: $Date$
:Status: ACCEPTED
:Discussion: http://www.eoxserver.org/wiki/DiscussionRfc16

This RFC proposes an implementation for Referenceable Grid Coverages as
well as for the WCS 2.0 operations working on them.

The implementation is available in the SVN under
http://eoxserver.org/svn/sandbox/sandbox_ref.

Introduction
------------

Referenceable Grid Coverages are coverages whose internal grid structure
can be mapped to a coordinate reference system by some general transformation.
They differ from rectified grid coverages in that the coordinate transformation
is not necessarily affine.

In the context of Earth Observation, raw satellite data can be seen as
referenceable grid coverages. They are typically delivered as image files but
do not have an affine transformation from the image geometry to a georeferenced
coordinate system. Depending on the desired geocoding precision, the
referencing transformation can be very complex involving additional data (DEMs)
and orbit metadata.

EOxServer shall be able to deliver (subsets of) Earth Observation raw data in
its original (referenceable grid) geometry using WCS 2.0 and EO-WCS.
Furthermore, it shall implement easily computable approximate referencing
algorithms based on ground control points (GCPs) in order to enable coordinate
transformations and rectified previews of the original data using WMS.

For the time being, the implementation will focus on SAR image data collected
by the ENVISAT-ASAR sensor made available by ESA.

Requirements
------------

The main requirement source for Referenceable Grid Coverage implementation in
EOxServer is the ESA O3S project. In the course of this project EOxServer shall
be installed in front of a small archive of ENVISAT-ASAR data. In a first step,
we will focus on covering the requirements of this use case, adding more generic
referenceable grid support in future iterations.

The ENVISAT-ASAR data are available in ENVISAT .N1 original format.

Delivery of the original referenceable grid data shall be supported using WCS
2.0 and EO-WCS. Subsetting shall be supported in pixel coordinates (imageCRS)
and in a coordinate reference system. The CRS subsets shall be mapped to pixel
coordinates using a simple coordinate transformation based on GCPs.

No support for resampling (``size`` and ``resolution``) or reprojection
(``outputcrs``) parameters is required as these are not applicable to
referenceable grid coverages.

At least GeoTIFF shall be supported as output format. GCP and metadata
information contained in the .N1 original file shall be preserved.

In order to support (rectified) WMS previews, a simple georeferencing algorithm
based on GCPs shall be implemented. This shall be reused to provide rectified
versions of referenceable grid coverages using WCS 2.0.

Implementation Details
----------------------

Input Formats
~~~~~~~~~~~~~

The implementation for referenceable grid coverages relies on GDAL for input
data and metadata (georeferencing information, GCPs). Any format that supports
storage of GCPs with the dataset can be used. The two most important formats
are the ENVISAT .N1 format and GeoTiff.


Referencing Algorithm and Subsetting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

WCS 2.0 allows to define subsets either in the image CRS, i.e. pixel
coordinates, or in some geographic or projected coordinate system. For
rectified grid coverages geographic coordinates can be easily transformed to
pixel coordinates in a straightforward way. This is not the case for 
referenceable grid coverages, though.

For referenceable grid coverages produced by Earth Observation missions, the
"correct" referencing transformation is not known in general. Instead, there
are many different algorithms some of them relying on different additional data
and metadata (DEMs, orbit information).

For the purposes of the EOxServer Referenceable Grid Coverage implementation,
a simple first order interpolation algorithm based on GCPs is used. This
algorithm does not use any additional data or metadata. The rationale for this
decision is that there is no way to advertise the actual referencing algorithm
in WCS or WMS, and therefore the most simple and straightfoward algorithm was
used.

Subsets given in georeferenced coordinates are transformed to the image CRS
using the inverse transformation algorithm based on GCPs. The implementation
uses not only the corner coordinates of the subsetting rectangle but also
intermediary points to calculate an envelope and thus to guarantee that the
requested extent be included in the result.

Genuine Referenceable Grid Coverage Support in WCS 2.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Referenceable Grid Coverages in their original geometry are available using
the EO-WCS extension of WCS 2.0.

The current implementation supports the ``subset`` parameter and transforms the
given subsets as indicated in the previous subsection. The ``size``
and ``resolution`` parameters are not supported as they do only apply to
rectified grid coverages.

The ``format`` parameter options are implemented in the same way as for
rectified grid coverages.

The ``rangesubset`` parameter is foreseen for implementation.

In order to be able to serve referenceable grid data, the original
:class:`~.WCS20GetCoverageHandler` was split up into
:class:`~.WCS20GetReferenceableCoverageHandler` and
:class:`~.WCS20GetRectifiedCoverageHandler`. While the latter one still relies
on MapServer, the one for referenceable grid data uses the vanilla GDAL Python 
bindings as well as additional GDAL-based extensions written for the
EOxServer project.

Metadata is read from the original dataset and tagged onto the result dataset
using the capabilities of the respective GDAL format drivers. Depending on
the driver implementation, the way the metadata is stored may be specific to
GDAL.

Coverage Metadata Tayloring
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The WCS 2.0 standard specifies that the complete referencing transformation be
described in the metadata of a referenceable grid coverage. This is a major
problem for Earth Observation data as in general there is no predefined
transformation; rather there are several different possible algorithms of
varying complexity that can be used for georeferencing the image, possibly
involving Earth Observation metadata such as orbit information, GCPs and 
additional data such as DEMs.

Furthermore there is no way to define an algorithm and describe its
parameters (e.g. the GCPs) in GML, but only the outcome of the algorithm, i.e. a
pixel-by-pixel mapping to geographic coordinates. This would produce a
tremendous amount of mostly useless metadata and blow up the XML descriptions
of coverage metadata to hundreds of megabytes for typical Earth Observation
products.

Therefore the current EOxServer implementation does not deliver any of the
``gml:AbstractReferenceableGrid`` extensions in its metadata. Instead a
non-standard ``ReferenceableGrid`` element is returned that contains all the
elements inherited from ``gml:Grid`` but no further information. This is only a
provisional solution that will be changed as soon as an appropriate way to
describe referencing metadata is defined by the WCS 2.0 standard or any of its
successors.

Support for Rectified Data in WMS and WCS 2.0
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The implementation of the WCS 2.0 (EO-WCS) GetCoverage request as well as
the WMS implementation is based on MapServer which supports rectified grid
coverages only. It is not possible to use any kind of GCP based referencing
algorithm in MapServer directly.

GDAL provides a mechanism to create so-called virtual raster datasets (VRT).
These consist of an XML file describing the parameters for transformation,
warping and other possible operations on raster data. They can be generated
using the GDAL C API and are readable by MapServer (which relies on GDAL as
well).

In order to provide referenced versions of referenceable data, EOxServer creates
such VRTs on the fly using the EOxServer GDAL extension. The VRT files are
deleted after each request.

GDAL Extension
~~~~~~~~~~~~~~

The EOxServer GDAL extension provides a Python binding to some C functions using
the GDAL C API that implement utilities for handling referenceable grid
coverages. At the moment the Python bindings are implemented using the
Python `ctypes <http://docs.python.org/library/ctypes.html>`_ module.

The :mod:`eoxserver.processing.gdal.reftools` module contains functions
for

* computing the pixel coordinate envelope from a georeferenced subset
* computing the footprint of a referenceable grid coverage
* creating a rectified GDAL VRT from referenceable grid data

All functions use a simple GCP-based referencing algorithm as indicated above.

The GDAL Extension was made necessary because the standard GDAL Python bindings
do not support GCP based coordinate transformations.
  
Voting History
--------------
  
:Motion: Adopted on  2012-01-03 with +1 from Arndt Bonitz, Martin Paces, 
         Fabian Schindler, Stephan Meißl and +0 from Milan Novacek
  
Traceability
------------
  
:Requirements: "N/A"
:Tickets: "N/A"
