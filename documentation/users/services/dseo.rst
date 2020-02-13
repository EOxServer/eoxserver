.. DSEO Request Parameters
  #-----------------------------------------------------------------------------
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Fabian Schindler <fabian.schindler@eox.at>
  #
  #-----------------------------------------------------------------------------
  # Copyright (C) 2020 EOX IT Services GmbH
  #
  # Permission is hereby granted, free of charge, to any person obtaining a
  # copy of this software and associated documentation files (the "Software"),
  # to deal in the Software without restriction, including without limitation
  # the rights to use, copy, modify, merge, publish, distribute, sublicense,
  # and/or sell copies of the Software, and to permit persons to whom the
  # Software is furnished to do so, subject to the following conditions:
  #
  # The above copyright notice and this permission notice shall be included in
  # all copies of this Software or works derived from this Software.
  #
  # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
  # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
  # DEALINGS IN THE SOFTWARE.
  #-----------------------------------------------------------------------------

Download Service for Earth Observation Products (DSEO)
======================================================

The following tables provide an overview over the available DSEO request
parameters for each operation supported by EOxServer.

.. index::
   single: GetCapabilities (DSEO Request Parameters)

GetCapabilities
---------------

Table: ":ref:`table_dseo_request_parameters_getcapabilities`" below lists all
parameters that are available with Capabilities requests.

.. _table_dseo_request_parameters_getcapabilities:
.. table:: DSEO GetCapabilities Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | service                   | Requested service                                         |   DSEO                           | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | request                   | Type of request                                           |   GetCapabilities                | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | acceptVersions            | Prioritized sequence of one or more specification         |   1.0.0                          | O                              |
    |                           | versions accepted by the client, with preferred versions  |                                  |                                |
    |                           | listed first (first supported version will be used)       |                                  |                                |
    |                           | version1[,version2[,...]]                                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | sections                  | Comma-separated unordered list of zero or more names of   | - All                            | O                              |
    |                           | zero or more names of sections of service metadata        | - ServiceIdentification          |                                |
    |                           | document to be returned in service metadata document.     | - ServiceProvider                |                                |
    |                           | Request only certain sections of Capabilities             | - OperationsMetadata             |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | updateSequence            | Date of last issued GetCapabilities request; to receive   |   "2013-05-08"                   | O                              |
    |                           | new document only if it has changed since                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

.. index::
   single: GetProduct (DSEO Request Parameters)

GetProduct
----------

Table: ":ref:`table_dseo_request_parameters_getproduct`" below lists all
parameters that are available with GetProduct requests.

.. _table_dseo_request_parameters_getproduct:
.. table:: DSEO GetProduct Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | service                   | Requested service                                         |   DSEO                           | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | request                   | Type of request                                           |   GetProduct                     | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | version                   | Version number                                            |   1.0.0                          | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | producturi                | Valid identifier of a registered Product                  |                                  | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
