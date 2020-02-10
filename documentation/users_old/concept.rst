.. Data Models Concepts
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

.. _Data Models Concepts:

Data Models Concepts
====================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Coverage
~~~~~~~~
Coverages are groups of raster fields (e.g bands) combined 
with metadata (metadata provides additional  information about the actual data).
EOxServer provides the ability to retrieve the whole coverage or can provide a subset of
the coverage using the Web Coverage Service `WCS <http://www.opengeospatial.org/standards/wcs>`_.

WCS standard provides the ability to retrieve sub-parts of the coverage (e.g certain bands or a smaller within the caverage bbox).
Another option would be to request the coverage -or a sub-area of it- as a map using WMS request 

.. _Product:

Product
~~~~~~~

Products can be defined as a small collection of coverages.

Coverages -when it comes to data versatility- are very strict (e.g all the data fields (bands) in a coverage must
must have the same size, grid (resolution), projection).
Storing a set of bands with a variety of resolutions can be done in a **product** data model.

In addition to coverages products contains metadata which provides additional information of the product ( e.g masks, noData value mask, satellite information ).

Browse
------

Products can be visualized using **browses**. which basically are pre-rendered images of the product.

.. _Collection:

Collection
~~~~~~~~~~

A collection is a much broader collection for raster data, they consist of a number of products or coverages or even both.

.. _Mosaic:

Mosaic 
------

A Mosaic is a separate type of collections,  it is basically a collection with more strict rules -when it comes to correlation of the data fields-, for example all bands in a mosaic must have the same resolution, datatype and projection.

Type objects
~~~~~~~~~~~~

type objects are json objects that contain information that defines the data model, (e.g bands definition and the datatype used ). There are 3 types used in EOxServer:

:CoverageType: contains information about **Coverages** ( e.g type name, bands, data type ). Mosaics are collections that uses coveragetype to define the rendered data, and therefore inherits the coverage's strictness.

:ProductType: contains associated information with **Products**. 

:CollectionType: contains associated information with **Collections**.

