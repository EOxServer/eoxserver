.. RFC 17
  #-----------------------------------------------------------------------------
  # $Id: index.rst 1344 2012-02-26 01:20:15Z meissls $
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
:Status: IN PREPARATION
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

Output Formats
--------------

...

Voting History
--------------

N/A

Traceability
------------

:Requirements: N/A
:Tickets: N/A
