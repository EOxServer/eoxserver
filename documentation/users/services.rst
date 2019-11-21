.. Services
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Martin Paces <martin.paces@eox.at>
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

.. _Servesis:

Services
========

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

This section describes how the EOxServer data  models are mapped into the OGC web services.

WCS
~~~
coverages
---------
**WCS** is used to retrieve coverages, coverages is a very generic term, it may refer to any geo-located n-dimensional array ( e.g atmospheric profile )

EO-WCS
~~~~~~
**EO-WCS** is a standard wcs extension for specified coverages (basically satellite imageries).

Eo-Dataset
---------
**Eo-Dataset** is a dataset (coverage) that is strictly a satellite image. It can be described as a coverage with 2D grid.

Rectified-Dataset
-----------------
**Rectified-Dataset** is a georeferenced grided dataset (coverage), it is associated with a CRS and origin or offset.

Referenced-Dataset
------------------
**Referenced-Dataset** is grid that is not rectified, but associated with (one or more) ground control points (coordinate transformations which relate the image to a CRS ).

Data-Series
-----------
**Data-Series** is basically a collection, it can entail coverages of all types and/or mosaics.
Collections(see ":ref:`Collection`") and products (see ":ref:`Product`") are mapped as Data-Series.

Rectified-Stitched-Mosaics
--------------------------
**Rectified-Stitched-Mosaics** is a specific collection type, where coverages share the same grid and the same range type.
It is used to map mosaics (see ":ref:`Mosaic`") into wsc service. 


OpenSearch
~~~~~~~~~~

**OpenSearch** is a 2 step search pattern where:

- first step is to search for Collections, where the request returns a collection.

- second step is to search for item within the collection, where the request returns either a coverage or a product.

example: 
--------
* The following HTTP request points to the root **OpenSearchDescriptionDocument(OSDD)** ::

    http://www.service.org/opensearch/

* The following request searches for collections, it returns the result in a json or xml format ::

    http://www.service.org/opensearch/search

* The following requests returns the **OpenSearchDescriptionDocument(OSDD)** of a specific collection ::

    http://www.service.org/opensearch/collections/<collectionId>/

* The following request searches for an item in the specified collection, it also returns the result as json or xml ::

    http://www.service.org/opensearch/collections/<collectionId>/search/






