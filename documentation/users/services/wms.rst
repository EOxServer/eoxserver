.. WMS Request Parameters
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

Web Map Service (WMS)
=====================

The following tables provide an overview over the available WMS request
parameters for each operation supported by EOxServer.

.. index::
   single: GetCapabilities (WMS Request Parameters)

GetCapabilities
---------------

Table: ":ref:`table_wms_request_parameters_getcapabilities`" below lists all
parameters that are available with Capabilities requests.

.. _table_wms_request_parameters_getcapabilities:
.. table:: WMS GetCapabilities Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | service                   | Requested service                                         |   WMS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | request                   | Type of request                                           |   GetCapabilities                | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | acceptVersions [1]_       | Prioritized sequence of one or more specification         |   1.3.0, 1.1.0, 1.0.0            | O                              |
    |                           | versions accepted by the client, with preferred versions  |                                  |                                |
    |                           | listed first (first supported version will be used)       |                                  |                                |
    |                           | version1[,version2[,...]]                                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | updateSequence            | Date of last issued GetCapabilities request; to receive   |   "2013-05-08"                   | O                              |
    |                           | new document only if it has changed since                 |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+

.. index::
   single: GetMap (WMS Request Parameters)

GetMap
------

Table: ":ref:`table_wms_request_parameters_getcoverage`" below lists all
parameters that are available with GetCoverage requests.

.. _table_wms_request_parameters_getcoverage:
.. table:: WMS GetCoverage Request Parameters

    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | Parameter                 | Description / Subparameter                                | Allowed value(s) / Example       | Mandatory (M) / Optional (O)   |
    +===========================+===========================================================+==================================+================================+
    | service                   | Requested service                                         |   WMS                            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | request                   | Type of request                                           |   GetMap                         | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | version                   | Version number                                            |   1.3.0, 1.1.0, 1.0.0            | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | layers                    | The layers to render. Must be a comma-separated list of   |                                  | M                              |
    |                           | layer names. Exposed layers are listed in the             |                                  |                                |
    |                           | Capabilities document and depend on the contents of the   |                                  |                                |
    |                           | instance.                                                 |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | For each object in the database a base layer with the     |                                  |                                |
    |                           | objects identifier as a name is added. Additionally       |                                  |                                |
    |                           | a number of layers are added with the objects identifier  |                                  |                                |
    |                           | plus a postfix as show in the list below:                 |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | - all:                                                    |                                  |                                |
    |                           |   - ``<no-postfix>``: the default rendering of the object |                                  |                                |
    |                           |   - ``outlines``: the objects footprint as a rendered     |                                  |                                |
    |                           |     geometry                                              |                                  |                                |
    |                           |   - ``outlined``: the default rendering of the object     |                                  |                                |
    |                           |     overlayed with the objects rendered footprint.        |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | - ``Collection``/``Product``:                             |                                  |                                |
    |                           |   - ``<mask-name>``: the rendered mask geometries for all |                                  |                                |
    |                           |     products in that collection or that single product.   |                                  |                                |
    |                           |   - ``masked_<mask-name>``: the default rendering of each |                                  |                                |
    |                           |     product, each individually masked with the            |                                  |                                |
    |                           |     mask of the provided ``mask-name``.                   |                                  |                                |
    |                           |   - ``<browse-type-name>``: renders the product(s)        |                                  |                                |
    |                           |     according to the browse types instructions (or uses   |                                  |                                |
    |                           |     an already existing browse if available.              |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | styles                    | The style for each of the rendered layers to be           |                                  | M                              |
    |                           | rendered with. This must be either empty or a             |                                  |                                |
    |                           | comma-separated list of either empty strings or names of  |                                  |                                |
    |                           | valid styles. When left empty (for a single layer or the  |                                  |                                |
    |                           | whole parameter), the default styling is applied.         |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | The available styles depend on the layer type. Outline    |                                  |                                |
    |                           | and mask layers can be rendered in the basic colors.      |                                  |                                |
    |                           | Single band output can be styled using a range of         |                                  |                                |
    |                           | color scales.                                             |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | The Capabilities document lists the available styles per  |                                  |                                |
    |                           | layer.                                                    |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | format                    | Requested format of the map to be returned, currently:    |   image/tiff                     | M                              |
    |                           |                                                           |                                  |                                |
    |                           | - image/tiff                                              |                                  |                                |
    |                           | - image/jpeg                                              |                                  |                                |
    |                           | - image/png                                               |                                  |                                |
    |                           | - image/gif                                               |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | bbox                      | The bounding box of the output map. Depending on the      |   12,17,14,17.4                  | M                              |
    |                           | service version and the coordinate reference system, the  |                                  |                                |
    |                           | axis order might change. The following rules apply:       |                                  |                                |
    |                           | - for service version 1.3 the axis order of the used CRS  |                                  |                                |
    |                           |   applies. For EPSG:4326, for example, the axis order is  |                                  |                                |
    |                           |   lat, lon, resulting in bounding boxes like              |                                  |                                |
    |                           |   ``<min_lat>,<min_lon>,<max_lat>,<max_lon>``             |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | crs / srs [1]_            | The CRS the bbox values are expressed in.                 | EPSG:4326                        | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | width                     | The width of the output image in pixels.                  | 512                              | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | height                    | The height of the output image in pixels.                 | 512                              | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | bgcolor                   | The background color to use in HEX notation: ``RRGGBB``   | 000000                           | M                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | transparent               | Defines whether or not to use transparency for            | TRUE                             | M                              |
    |                           | non-colored regions of the image. The ``format`` must     |                                  |                                |
    |                           | provide an alpha channel (like PNG).                      |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | dim_bands                 | Selects the given bands as gray, RGB or RGBA channels.    | B04,B03,B02                      | O                              |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | dim_wavelengths           | This behaves the same as with ``dim_bands`` but allows to | 664.6,559.8,492.4                | O                              |
    |                           | specify the bands center wavelength instead of the bands  |                                  |                                |
    |                           | name                                                      |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | dim_range                 | Allows to specify a min/max value for each selected band  | ``0 1;0 1;0 5``                  | O                              |
    |                           | linearly interpolate values.                              |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | cql                       | Allows to specify metadata filters. See the :ref:`CQL`    | ``cloudCover < 10``              | O                              |
    |                           | documentation for usage.                                  |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+
    | sortBy                    | Allows to sort the images regarding a specific metadata   | ``cloudCover A``                 | O                              |
    |                           | value. Can either be ascending or descending using ``A``  |                                  |                                |
    |                           | or ``D``                                                  |                                  |                                |
    +---------------------------+-----------------------------------------------------------+----------------------------------+--------------------------------+



.. [1]  For WMS service version 1.3 the ``crs`` parameter must be used, for services
        versions below 1.3 the parameter name is ``srs``.
