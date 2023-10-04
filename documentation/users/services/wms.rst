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

.. _wms:

Web Map Service (WMS)
=====================

    The OpenGIS® Web Map Service Interface Standard (WMS) provides a simple
    HTTP interface for requesting geo-registered map images from one or more
    distributed geospatial databases. A WMS request defines the geographic
    layer(s) and area of interest to be processed. The response to the request
    is one or more geo-registered map images (returned as JPEG, PNG, etc) that
    can be displayed in a browser application. The interface also supports the
    ability to specify whether the returned images should be transparent so
    that layers from multiple servers can be combined or not.

The standard can be obtained from the `Open Geospatial Consortiums homepage
<https://www.ogc.org/standards/wms>`_.

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

Table: ":ref:`table_wms_request_parameters_getmap`" below lists all
parameters that are available with GetMap requests.

.. _table_wms_request_parameters_getmap:
.. table:: WMS GetMap Request Parameters

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
    |                           |                                                           |                                  |                                |
    |                           |   - ``<no-postfix>``: the default rendering of the object |                                  |                                |
    |                           |   - ``outlines``: the objects footprint as a rendered     |                                  |                                |
    |                           |     geometry                                              |                                  |                                |
    |                           |   - ``outlined``: the default rendering of the object     |                                  |                                |
    |                           |     overlayed with the objects rendered footprint.        |                                  |                                |
    |                           |                                                           |                                  |                                |
    |                           | - ``Collection``/``Product``:                             |                                  |                                |
    |                           |                                                           |                                  |                                |
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
    |                           | color scales (Raster styles may apply).                   |                                  |                                |
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
    |                           |                                                           |                                  |                                |
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


Layer Mapping
-------------

Various objects in EOxServer generate exposed layers to be requested by clients
via WMS.

.. _table_wms_layer_mapping:
.. table:: WMS Layer Mapping

    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Base Object               | Suffix                        | Description                                 | Style                                       | Advertised [2]    |
    +===========================+===============================+=============================================+=============================================+===================+
    | Coverage                  | --                            | Renders the coverage as a map. This is the  | When the coverage only has a single field,  | no                |
    |                           |                               | most basic for of rendering and             | or only one is selected via ``dim_bands``,  |                   |
    |                           |                               | ``dim_bands`` and ``dim_range`` will likey  | then the name of a color scale can be passed|                   |
    |                           |                               | need to be used to achieve representative   | to colorize the otherwise greyscale image.  |                   |
    |                           |                               | result.                                     |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Mosaic                    | --                            | This behaves exactly like with Coverages    | Same as above.                              | yes               |
    |                           |                               | but applies the rendering to all contained  |                                             |                   |
    |                           |                               | Coverages.                                  |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Product                   | --                            | Renders the Products default Browse or      |                                             | no                |
    |                           |                               | using the defaults Browse Type to           |                                             |                   |
    |                           |                               | dynamically render a browse.                |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Coverage/Product          | ``outlines``                  | Renders the footprint of the                | Defines the color of the rendered geometry. | no                |
    |                           |                               | Coverage/Product as a colorized geometry.   |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Mosaic/Collection         | ``outlines``                  | Renders the footprint of all contained      | Defines the color of the rendered geometry. | yes               |
    |                           |                               | Coverages or Products as a colorized        |                                             |                   |
    |                           |                               | geometry.                                   |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Coverage/Product          | ``outlined``                  | Renders the Coverage/Product in its default | Defines the color of the rendered geometry. | no                |
    |                           |                               | way (as with no prefix) but overlays it     |                                             |                   |
    |                           |                               | with the footprint geometry (as with        |                                             |                   |
    |                           |                               | ``outlines`` suffix)                        |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Mosaic/Collection         | ``outlined``                  | Renders the Mosaic/Collection in its        | Defines the color of the rendered geometry. | yes               |
    |                           |                               | default way (as with no prefix) but each    |                                             |                   |
    |                           |                               | included Coverage/Product rendering is      |                                             |                   |
    |                           |                               | overlayed with the footprint geometry (as   |                                             |                   |
    |                           |                               | with the ``outlines`` suffix).              |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Product                   | ``<Browse Type Name>``        | Renders the Products Browse of that Browse  |                                             | no                |
    |                           |                               | Type if available or uses the Browse Type   |                                             |                   |
    |                           |                               | to dynamically render a Browse.             |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Product                   | ``<Mask Type Name>``          | Renders the Mask of the Product of that     | Defines the color of the geometry.          | no                |
    |                           |                               | Mask Type as a rasterized vector layer.     |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Product                   | ``masked_<Mask Type Name>``   | Use the default rendering of the product    |                                             | no                |
    |                           |                               | and apply the Mask of the specified Mask    |                                             |                   |
    |                           |                               | Type.                                       |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Collection                | --                            | Renders all Products in the Collection with |                                             |                   |
    |                           |                               | their default Browse (or dynamically using  |                                             |                   |
    |                           |                               | the default Browse Type).                   |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Collection                | ``<Browse Type Name>``        | Renders all contained Products using the    |                                             |                   |
    |                           |                               | Browse of that Browse Type or dynamically   |                                             |                   |
    |                           |                               | generated Browse of that Browse Type.       |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Collection                | ``<Mask Type Name>``          | Renders all Masks of the contained Products |                                             |                   |
    |                           |                               | as colorized geometries.                    |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+
    | Collection                | ``masked_<Mask Type Name>``   | Renders all contained Browses using their   |                                             |                   |
    |                           |                               | default Browse or a dynamically generated   |                                             |                   |
    |                           |                               | Browse of the default Browse Type and       |                                             |                   |
    |                           |                               | individually apply the Mask of that Mask    |                                             |                   |
    |                           |                               | Type.                                       |                                             |                   |
    +---------------------------+-------------------------------+---------------------------------------------+---------------------------------------------+-------------------+

.. [2]  Whether or not this layer is by default advertised in GetCapabilities
        documents. This can be overridden by setting the objects visibility.
