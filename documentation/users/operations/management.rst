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
For more information please refer to the `installation <Installation>`_,
`instance creation <InstanceCreation>`_, and `configuration
<InstanceConfiguration>`_ sections respectively. Also, data preprocessing
is not part of the this guide.

This guide will use a practical example of real high resolution RGB + near
infrared satellite imagery from the SPOT mission to show how to set up an
operational service. To add a little more complexity, the data type is 16 bit
unsigned integer, which is common for many eartch observation instruments.

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



