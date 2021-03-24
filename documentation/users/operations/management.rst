.. Management
  #-----------------------------------------------------------------------------
  # $Id$
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

.. _Management:

Management
==========

This chapter deals with the operational management of an EOxServer instance. It
is assumed, that EOxServer is installed, an instance is created and configured.
For more information please refer to the :ref:`Installation`,
:ref:`InstanceCreation`, and :ref:`InstanceConfiguration` sections
respectively. Also, data preprocessing is not part of the this guide.

This guide will use a practical example of real high resolution RGB + near
infrared satellite imagery from the SPOT mission to show how to set up an
operational service. To add a little more complexity, the data type is 16 bit
unsigned integer, which is common for many earth observation instruments.

Setup
-----

Each instance will most likely deal with a limited set of data and semantics,
thus it is beneficial to provide a strict configuration of the underlying
types in order to improve coherence, add metadata and ensure integrity.

For our example we start with the lowest level of abstractions, the coverages.
As the data to be ingested consists of RGB + NIR files, the used coverage type
needs to reflect just that.

The following JSON definition is used to specify the fields of the coverage
type and to provide some extra metadata. The contents are stored in the file
``rgbnir.json``:

.. code-block:: json

    {
        "bands": [
            {
                "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
                "description": "Red Channel",
                "gdal_interpretation": "RedBand",
                "identifier": "red",
                "name": "red",
                "nil_values": [
                    {
                        "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                        "value": 0
                    }
                ],
                "uom": "W.m-2.Sr-1",
                "significant_figures": 5,
                "allowed_value_ranges": [
                    [0, 65535]
                ]
            },
            {
                "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
                "description": "Green Channel",
                "gdal_interpretation": "GreenBand",
                "identifier": "green",
                "name": "green",
                "nil_values": [
                    {
                        "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                        "value": 0
                    }
                ],
                "uom": "W.m-2.Sr-1",
                "significant_figures": 5,
                "allowed_value_ranges": [
                    [0, 65535]
                ]
            },
            {
                "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
                "description": "Blue Channel",
                "gdal_interpretation": "BlueBand",
                "identifier": "blue",
                "name": "blue",
                "nil_values": [
                    {
                        "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                        "value": 0
                    }
                ],
                "uom": "W.m-2.Sr-1",
                "significant_figures": 5,
                "allowed_value_ranges": [
                    [0, 65535]
                ]
            },
            {
                "definition": "http://www.opengis.net/def/property/OGC/0/Radiance",
                "description": "Nir Channel",
                "gdal_interpretation": "NirBand",
                "identifier": "nir",
                "name": "nir",
                "nil_values": [
                    {
                        "reason": "http://www.opengis.net/def/nil/OGC/0/unknown",
                        "value": 0
                    }
                ],
                "uom": "W.m-2.Sr-1",
                "significant_figures": 5,
                "allowed_value_ranges": [
                    [0, 65535]
                ]
            }
        ],
        "data_type": "Uint16",
        "name": "RGBNir"
    }

This definition can now be loaded in the services using the ``coveragetype
import`` command:

.. code-block:: bash

    python manage.py coveragetype loaddata rgbnir.json

Now that the Coverage type is registered, it can be used to create one or
multiple Product types. This takes the rather abstract Coverage type and
creates a more specific type structure data for a certain satellite mission or
instrument. The following command creates such a product type for ``PL00``
Products, referencing the previously imported Coverage type ``RGBNir``.

.. code-block:: bash

    python manage.py producttype create PL00 --coverage-type RGBNir

For the generated Product type, we can now add visual representations, called
Browse types in EOxServer. Browse types can be defined to create definitions
for RGB, RGBA or color scaled images from the registered coverages. This is
achieved by providing transfer functions using either the band names or
expressions and additional value ranges and no-data values.

For the example, three Browse types are created: true color RGB, false color
RGB, and a grayscale NDVI using the red and near infrared bands. The following
commands will do just that, plus creating a fourth Browse type (a copy of the
``TRUE_COLOR`` one) with no name, marking it as the default representation.

.. code-block:: bash

    python manage.py browsetype create PL00 \
        --red "red" \
        --green "green" \
        --blue "blue" \
        --red-range 1000 15000 \
        --green-range 1000 15000 \
        --blue-range 1000 15000 \
        --red-nodata 0 \
        --green-nodata 0 \
        --blue-nodata 0

    python manage.py browsetype create PL00 TRUE_COLOR \
        --red "red" \
        --green "green" \
        --blue "blue" \
        --red-range 1000 15000 \
        --green-range 1000 15000 \
        --blue-range 1000 15000 \
        --red-nodata 0 \
        --green-nodata 0 \
        --blue-nodata 0

    python manage.py browsetype create PL00 FALSE_COLOR \
        --red "nir" \
        --green "red" \
        --blue "green" \
        --red-range 1000 15000 \
        --green-range 1000 15000 \
        --blue-range 1000 15000 \
        --red-nodata 0 \
        --green-nodata 0 \
        --blue-nodata 0

    python manage.py browsetype create PL00 NDVI \
        --grey "(nir-red)/(nir+red)" --grey-range -1 1

For true and false color representations, a red, green, and blue band is
selected using the names as defined in the ``RGBNir`` range type. Using the
``range`` selectors the input range is specified which will be linearly scaled
to produce a normalized value range of the output image. The nodata values help
to mark out pixels that ought to be transparent.

The ``NDVI`` Browse type uses the ``--grey`` output band with a mathematical
expression. The variables names in the expression must use the band names of
the Coverage type. Using the ``--grey-range``, a default value range is
specified.

It is typical that EO data products entail vector masks to mark areas with a
specific property. Usually this is used to mark the (in-)validity in a specific
region or to mark clouds or snow.

In order to take advantage of these masks, for each type of mask a Mask type
must be registered. In our example, only the single validity mask is used.
To "mask-in" areas the specific ``--validity`` flag must be used, otherwise
the inverse is assumed.

.. code-block:: bash

    python manage.py masktype create --validity PL00 validity

.. note::

    It is possible to combine the data of multiple Product types. In those
    cases it is important to define the same Browse and Mask types (even if the
    underlying expressions/ranges/no-data values are different), so that they
    can be rendered as a single map layer.

The final step in the setup of the types is to create a Collection type. It is
possible to put both Coverages and Products into a collection, so it is a good
practice to limit the types of Products and Coverages that can be added to what
is actually required.

The following Collection type creation command specifies that it is possible
to put both Coverages and Products of the previously created types into such a
Collection.

.. code-block:: bash

    python manage.py collectiontype create CollectionType \
        --coverage-type RGBNir \
        --product-type PL00

Since we will most likely have only one or a very limited amount of Collections
in the lifetime of the service, the instantiation of the Collection could be
considered as part of the setup procedure.

.. code-block:: bash

    python manage.py collection create Collection --type CollectionType

One task that must be prepared when using more sophisticated storage mechanisms
is to specify the Storage backends and their respective Storage
authentication/authorization mechanisms. For our example, we assume that our
data resides on an OpenStack Swift object storage. This requires a keystone
authentication system which can be set up in the following manner (auth
credentials are assumed to be in the used bash environment variables):

.. code-block:: bash

    python manage.py storageauth create auth-keystone https://auth.obs.service.com \
        --type keystone \
        -p auth-version "${ST_AUTH_VERSION}" \
        -p identity-api-version="${ST_AUTH_VERSION}" \
        -p username "${OS_USERNAME}" \
        -p password "${OS_PASSWORD}" \
        -p tenant-name "${OS_TENANT_NAME}" \
        -p tenant-id "${OS_TENANT_ID}" \
        -p region-name "${OS_REGION_NAME}"

We can now create a named Storage of the type ``swift`` using the keystone auth
object from above:

.. code-block:: bash

    python manage.py storage create \
        my-storage ${CONTAINER} \
        --type swift \
        --storage-auth auth-keystone

This concludes the setup step and the service is now ready to be ingested with
data.

Data registration
-----------------

Products and Coverages can be ingested using the command line interface as
well.

In our example, we assume that our data files are structured in the following
way:

 - all files reside on a Swift object storage, the one established in the
   `Setup`_ section.
 - all acquisitions are stored as ZIP containers, which include the raster
   data, vector masks and metadata in GSC format.
 - the raster data are comprised of one TIFF file per band, one each for red,
   green, blue, and near infrared with their file suffix indicating their
   semantics.

The first step is to register the Product itself. This is done by referencing
the ZIP container itself.

.. code-block:: bash

    product_identifier=$(
        python manage.py product register \
            --type PL00 \
            --collection Collection \
            --meta-data my-storage path/to/package.zip metadata.gsc \
            --package my-storage path/to/package.zip \
            --print-identifier
    )

The management command prints the identifier of the registered coverage, which
is stored in a bash variable. It can be used to associated the Coverages to the
product. Using the ``--collection`` parameter, the Product is automatically put
into the Collection created earlier.

The next step is to register a Coverage and associate it with the Product.

.. code-block:: bash

    python manage.py coverage register \
        --type RGBNir \
        --product ${product_identifier} \
        --identifier "${product_identifier}_coverage" \
        --meta-data my-storage path/to/package.zip metadata.gsc \
        --data my-storage path/to/package.zip red.tif \
        --data my-storage path/to/package.zip green.tif \
        --data my-storage path/to/package.zip blue.tif \
        --data my-storage path/to/package.zip nir.tif

For the data access let us define that the Product identifier is ``Product-A``
this the Coverages identifier is ``Product-A_coverage``.

Data access
-----------

Now that the first Product and its Coverage are successfully registered, the
services can already be used.

:ref:`wms`
~~~~~~~~~~

Via WMS it is possible to get rendered maps from the stored Products and
Coverages. The table for `Layer Mapping <table_wms_layer_mapping>`_ is imporant
here. From that we can deduct various map layers that are available for access.

For production services it is typical to provide access to thounsands of earth
observation Products, thus rendering individual Product access impractical for
visual browsing. Typically, it is more convenient to access the Collection
instead using the area and time of interest and optionally additional metadata
filters.

This results in a catalog of the following available layers:

 - ``Collection``: the most basic rendering of the Collection. In our example
   the we created four Browse Type definitions: ``TRUE_COLOR``,
   ``FALSE_COLOR``, ``NDVI`` and an unnamed default one which had the same
   parameters as ``TRUE_COLOR``. This means, that the default rendering is
   a true color representation of the Products.
 - ``Collection__outlines``: this renders the outlines of the Products as
   geometries.
 - ``Collection__outlined``: this is a combination of the previous two layers:
   each Product is rendered in ``TRUE_COLOR`` with its outlines highlighted.
 - ``Collection__TRUE_COLOR``, ``Collection__FALSE_COLOR``,
   ``Collection__NDVI``: these are the browse visualizations with the
   definintions from earlier.
 - ``Collection__validity``: this renders the Products vector masks as colored
   geometries.
 - ``Collection__masked_validity``: this renders the default visualization
   (true color) but applies each Products validity mask.


The following list shows all of these rendering options with an example product

.. table:: WMS Collection Layers

    +-----------------------------------+---------------------------------------------------+
    | Layer                             | Example image                                     |
    +===================================+===================================================+
    | ``Collection``/                   | .. figure:: images/product_true_color.png         |
    | ``Collection__TRUE_COLOR``        |                                                   |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__FALSE_COLOR``       | .. figure:: images/product_false_color.png        |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__NDVI``              | .. figure:: images/product_ndvi.png               |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__outlines``          | .. figure:: images/product_outlines.png           |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__outlined``          | .. figure:: images/product_outlined.png           |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__validity``          | .. figure:: images/product_validity.png           |
    +-----------------------------------+---------------------------------------------------+
    | ``Collection__masked_validity``   | .. figure:: images/product_masked_validity.png    |
    +-----------------------------------+---------------------------------------------------+

It is possible to filter the objects using their metadata. This happens
already with the mandatory ``bbox``: only objects that intersect with that
bounding box are further processed and rendered to the output map. One other
such parameter is the ``time`` parameter. It allows to specify a time instant
or a time range to include objects.

It is, however, also possible to filter upon any other metadata of a Product
as well. This can be used, for example, to only render images below a threshold
of cloud coverage, to generate a mosaic of almost cloud free images. The
parameter to use is the ``cql`` one. For our example, we would append
``&cql=cloudCover <= 5`` to only include images with less or equal than 5%
cloud coverage. For this to work, the metadata of the Products needs to be
indexed upon registration. This is done in the process of metadata reading.

For more details about CQL and all available metadata fields refer to
the :ref:`CQL` documentation.

:ref:`wcs`
~~~~~~~~~~

WCS in EOxServer uses a more straight-forward mapping of EO object types to
WCS data model types. As EOxServer makes use of the EO Application Profile
it maps Mosaics and Coverages to Rectified Stitched Mosaics and
Rectified/Referenceable Datasets respectively and Collections and Products to
Dataset Series.

.. table:: WCS EO Object type mapping

    +---------------+-------------------------------------------+
    | Object type   | EO-WCS data model type                    |
    +===============+===========================================+
    | Coverage      | Rectified Dataset/Referenceable Dataset   |
    |               | (depending on whether or not a Grid is    |
    |               | used).                                    |
    +---------------+-------------------------------------------+
    | Product       | DatasetSeries                             |
    +---------------+-------------------------------------------+
    | Mosaic        | RectifiedStitchedMosaic                   |
    +---------------+-------------------------------------------+
    | Collection    | DatasetSeries                             |
    +---------------+-------------------------------------------+


For our example this means that a typical client will fist investigate the
WCS capabilities document to find out what Dataset Series are available, as
listing a very large amount of Coverages is not feasible. In our example, the
``Collection`` is listed as Dataset Series.

To explore it further, ``DescribeEOCoverageSet`` request with spatio-temporal
subsets can be used to get the contents of the Dataset Series. This will list
the entailed Products as sub Dataset Series and the Coverages as their
respective EO Coverage type.

All Coverages of interest can be downloaded using ``GetCoverage`` requests.

:ref:`opensearch`
~~~~~~~~~~~~~~~~~

The access to the indexed objects via OpenSearch uses the two-step search
principle: the root URL of OpenSearch returns with the general OpenSearch
description document (OSDD), detailing the available search patterns using
URL templates. Each template is associated with a result format in which the
search results are rendered. The first step is to search for advertised
Collections.

For our example, this will return our single ``Collection`` encoded in the
chosen result format. This also includes

.. table:: OpenSearch URL endpoints

    +---------------------------------------------------+-----------------------------------------------------------+
    | URL                                               | Semantic                                                  |
    +===================================================+===========================================================+
    | ``opensearch``                                    | The root OSDD file.                                       |
    +---------------------------------------------------+-----------------------------------------------------------+
    | ``opensearch/<format>``                           | The collection search step                                |
    +---------------------------------------------------+-----------------------------------------------------------+
    | ``opensearch/<format>``                           | The search for collections using the specified format     |
    +---------------------------------------------------+-----------------------------------------------------------+
    | ``opensearch/collections/Collection``             | The OSDD file specific to the ``Collection``              |
    +---------------------------------------------------+-----------------------------------------------------------+
    | ``opensearch/collections/Collection/<format>``    | The search for items in our ``Collection`` in that format |
    +---------------------------------------------------+-----------------------------------------------------------+

