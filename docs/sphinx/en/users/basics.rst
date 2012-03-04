.. EOxServer Basics
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

.. _EOxServer Basics:

EOxServer Basics
================

.. contents:: Table of Contents
    :depth: 3
    :backlinks: top

Introduction
------------

What is EOxServer?
~~~~~~~~~~~~~~~~~~

EOxServer is an open source software for registering, processing and publishing
Earth Observation data via different Web Services. EOxServer is written in
Python and relies on widely-used libraries for geospatial data manipulation.

The core concept of the EOxServer data model is the one of a coverage. In this
context, a coverage is a mapping from a domain set (a geographic region of the
earth described by its coordinates) to a range set. For original EO data,
the range set usually consists of measurements of some physical quantity (
e.g. radiation for optical instruments).

The EOxServer service model is designed to deliver (representations of) EO data
using open standard web service interfaces as specified by the `Open Geospatial
Consortium <http://www.opengeospatial.org>`_ (OGC).

What are the main features of EOxServer?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Repository for Earth Observation data
* OGC Web Services
* Administration Tools
* Web Client
* Identity Management System

Where can I get it?
~~~~~~~~~~~~~~~~~~~

You can get the EOxServer source from

* the `EOxServer Download page <http://eoxserver.org/wiki/Download>`_
* the `Python Package Index (PyPi) <http://pypi.python.org/pypi/EOxServer/>`_
* the `EOxServer SVN repository <http://eoxserver.org/svn/trunk>`_

The recommended way to install EOxServer on your system is to use the
Python installer utility
`pip <http://www.pip-installer.org/en/latest/index.html>`_.

Please refer to the :doc:`install` document for further information on
installing the software.

Where can I get support?
~~~~~~~~~~~~~~~~~~~~~~~~

If you have questions or problems, you can get support at the official
EOxServer Users' mailing list users@eoxserver.org. See :doc:`mailing_lists` for
instructions how to subscribe.

Documentation is available on this site and as a part of the EOxServer source.

EOxServer Documentation
~~~~~~~~~~~~~~~~~~~~~~~

The EOxServer documentation consists of the

* :doc:`/en/users/index` (which this document is part of)
* :doc:`/en/developers/index` (where you can find implementation details)
* :doc:`/en/rfc/index` (where you can find high-level design documentation)

Furthermore, you can consult the inline documentation in the source code
e.g. in the `Source Browser <http://eoxserver.org/browser>`_.

Demonstration Services
~~~~~~~~~~~~~~~~~~~~~~

There is a demonstration service available on the EOxServer site. You can reach
it under http://eoxserver.org/demo_stable/ows. For some sample calls to
different OGC Web Services, see :doc:`demonstration`.

Data Model
----------

The EOxServer data model describes which data can be handled by the software
and how this is done. This section gives you a short overview about the
basic components of the data model.

The term coverage is introduced by the OGC Abstract Specification. There,
coverages are defined as a mapping between a domain set that can be referenced
to some region of the earth to a range set which describes the possible values
of the coverage. This is, of course, a very abstract definition. It comprises
everything that has historically been called "raster data" (and then some, but
that is out of scope of EOxServer at the moment).

The data EOxServer originally was designed for is satellite imagery. So the
domain set is the extent of the area that was scanned by the respective sensor,
and the range set contains its measurements, e.g. the radiation of a spectrum of
wavelengths (optical data).

In the language of the OGC Abstract Specification ortho-rectified data
corresponds to "rectified grid coverages", whereas data in
the original geometry corresponds to "referenceable grid coverages".

The EOxServer coverage model relies heavily on the data model of the
Web Coverage Service 2.0 Earth Observation Application Profile which is about
to be approved by OGC. This profile introduces different categories of
Earth Observation data:

* Rectified or Referenceable Datasets roughly correspond to satellite scenes,
  either ortho-rectified or in the original geometry
* Rectified Stitched Mosaics are collections of Rectified Datasets that can be
  combined to form a single coverage
* Dataset Series are more general collections of Datasets; they are just
  containers for coverages, but not coverages themselves

Datasets, Stitched Mosaics and Dataset Series are accompanyed by Earth
Observation metadata. At the moment, EOxServer supports a limited subset of
metadata items, such as the identifier of the Earth Observation product, the
acquisition time and the acquisistion footprint.

Service Model
-------------

Earth Observation data are published by EOxServer using different OGC Web
Services. The OGC specifies open standard interfaces for the exchange of
geospatial data that shall ensure interoperability and universal access to
geodata.

Web Coverage Service
~~~~~~~~~~~~~~~~~~~~

The OGC `Web Coverage Service <http://www.opengeospatial.org/standards/wcs>`_
(WCS) is designed to deliver original coverage data. EOxServer implements
three versions of the WCS specification:

* version 1.0.0
* version 1.1.0
* version 2.0.0 including the Earth Observation Application Profile (EO-AP)

Each of these versions supports three operations:

* GetCapabilities - returns an XML document describing the available coverages
  (and Dataset Series)
* DescribeCoverage - returns an XML document describing a specific coverage
  and its metadata
* GetCoverage - returns (a subset of) the coverage data

The WCS 2.0 EO-AP adds an additional operation:

* DescribeEOCoverageSet - returns an XML document describing (a subset of) the
  datasets contained in a Rectified Stitched Mosaic or Dataset Series
  
For detailed lists of supported parameters for each of the operations see 
:ref:`EO-WCS Request Parameters` .

In addition, EOxServer supports the WCS 1.1 Transaction operation which provides
an interface to ingest coverages and metadata into an existing server.

Web Map Service
~~~~~~~~~~~~~~~

The OGC `Web Map Service <http://www.opengeospatial.org/standards/wms>`_ (WMS)
is intended to provide portrayals of geospatial data (maps). In EOxServer,
WMS is used for viewing purposes. The service provides RGB or grayscale
representations of Earth Observation data. In some cases, the Earth Observation
data will be RGB imagery itself, but in most cases the bands of the images
correspond to other parts of the wavelength spectrum or other measurements
altogether.

EOxServer implements WMS versions 1.0, 1.1 and 1.3 as well as parts of the
Earth Observation Application Profile for WMS 1.3. The basic operations are:

* GetCapabilities - returns an XML document describing the available layers
* GetMap - returns a map

For certain WMS 1.3 layers, there is also a third operation available

* GetFeatureInfo - returns information about geospatial features (in our case:
  datasets) at a certain position on the map

Every coverage (Rectified Dataset, Referenceable Dataset or Rectified Stitched
Mosaic) is mapped to a WMS layer. Furthermore, Dataset Series are mapped to
WMS layers as well. In WMS 1.3 a "bands" layer is appended for each coverage
that allows to select and view a subset of the coverage bands only. Furthermore,
queryable "outlines" layers are added for Rectified Stitched Mosaics and Dataset
Series which show the footprints of the Datasets they contain.

.. TODO: Include once implementation is available.
    Web Processing Service
    ~~~~~~~~~~~~~~~~~~~~~~

    The OGC `Web Processing Service <http://www.opengeospatial.org/standards/wps>`_
    (WPS) is intended to make processing resources for geospatial data available
    online. EOxServer features an implementation of this standard as well.

    The WPS server provides three operations:

    * GetCapabilities - returns an XML document describing the available processes
    * DescribeProcess - returns an XML document describing a specific process
    * Execute - allows to invoke a process

Security Architecture
---------------------

...
