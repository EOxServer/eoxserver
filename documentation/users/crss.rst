.. ConfigurationOptions
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Martin Paces <martin.paces@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2012 EOX IT Services GmbH
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
    single: Supported CRSs and Their Configuration  

.. _CRSConfiguration:

Supported CRSs and Their Configuration  
======================================

.. contents:: Table of Contents
   :depth: 3
   :backlinks: top

This section describes configuration of Coordinate Reference Systems for both
WMS and WCS services.

Coordinate Reference Systems  
----------------------------

The Coordinate Reference System (CRS) denotes the projection of coordinates to an
actual position on Earth. 
EOxServer allows the configuration of supported CRSes for WMS and WCS services. 
The CRSes used by EOxServer are specified exclusively by means of 
`EPSG numerical codes <http://www.epsg-registry.org>`_. 

Web Map Service
---------------

EOxServer allows the specification of the overall list of CRSes supported by all
published map layers (listed at the top layer of the WMS ``Capabilities`` XML
document). In case of no common CRS the list can be empty. In addition to the
list of common CRSes each individual layer has its *native* CRS which need
not to be necessarily listed among the common CRSes. The meaning of the *native*
CRS changes based on the EO dataset:
 
 * Rectified Datasets - the actual CRS of the source geo-rectified raster data,
 * Rectified Stitched Mosaic - the actual CRS of the source geo-rectified raster
   data,
 * Referenceable Dataset - the CRS of the geo-location grid tie-points. 
 * Time Series - always set to WGS 84 (may be subject to change in future).  

This *native* CRS is also used as the CRS in which the geographic extent
(bounding-box) is published.

The list of WMS common CRSes is specified as a comma separated list of EPSG codes
in the EOxServer's configuration (``<instance path>/conf/eoxserver.conf``) in
section ``serices.ows.wms``::

    [services.ows.wms]
    supported_crs= <EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]


Web Coverage Service
--------------------

EOxServer allows the specification of a list of CRCes to be used by the WCS. 
These CRSes can be used to select subsets of the desired coverage or, in case of
rectified datasets (including rectified stitched mosaics) to specify the
CRS of the output image data. The latter case is not applicabe to referenceable
datasets as these are always returned in the original image geometry.

The list of WCS supported CRSes is specified as a comma-separated list of EPSG 
codes in the EOxServer configuration (``<instance path>/conf/eoxserver.conf``) 
in section ``serices.ows.wcs``::

    [services.ows.wcs]
    supported_crs= <EPSG-code>[,<EPSG-code>[,<EPSG-code> ... ]]
