.. Backends
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


.. _Backends:

Backends
========

The backends concepts provide a representation of data, metadata
and other files that either reside on a local or remote storage.

The backends have a static representation in the database (i.e the
data models) and a dynamic behavioral implementation: the handlers.
The combintation of both allows the registration of storages,
backend authorization and data items and the access at runtime.


Data model
----------

The backends data model are represented by Django database models.
The following classes provide both concrete and abstract model
for the use of the other components of EOxServer.

Data Item
~~~~~~~~~

This abstract model is used to reference files, which are either
local, or residing on a `Storage Model`_. Each concrete implementation
of this abstract class has at least a reference to a Storage,
a location and an optional format specifier.

The ``location`` is always relative to the specified storage.
When no storage is set, it is treated as a path to a local file.

Examples of concrete data items are the ``ArrayDataItem`` to
store raster data for ``Coverages`` or the ``MetaDataItem`` to
store arbitrary metadata for geospatial objects.

.. _Storage Model:

Storage
~~~~~~~

The Storage model allows to provide a simple abstraction of
files on a remote storage or a local archive file. The type
of the storage is denoted by its ``storage_type`` field. This
value is used when accessing the storage via the ``StorageHandler``
class of the appropriate type.

Each storage has a ``url`` field that provides a basic "location"
of the storage. The meaning of the field depends on the storage type.
For an HTTP storage, for example, the URL would be the URL to the
HTTP server and the root path for all data items to use, whereas
for a ZIP file storage the URL is the path to the ZIP file.

Each storage can be given a name, which helps with management.

A Storage can be linked to a `Storage Auth`_ model, which allows
to specify authorization credentials.

.. _default-storage-handlers:

.. table:: Default storage handlers

    +---------------+-----------------------------------------------------------+
    | Storage type  | Description                                               |
    +===============+===========================================================+
    | ZIP           | ZIP file storage.                                         |
    +---------------+-----------------------------------------------------------+
    | TAR           | TAR file storage                                          |
    +---------------+-----------------------------------------------------------+
    | directory     | A local directory is treated as a storage file storage    |
    +---------------+-----------------------------------------------------------+
    | HTTP          | An HTTP server storage.                                   |
    +---------------+-----------------------------------------------------------+
    | FTP           | An FTP server storage.                                    |
    +---------------+-----------------------------------------------------------+
    | swift         | OpenStack swift object storage.                           |
    +---------------+-----------------------------------------------------------+



Storage Auth
~~~~~~~~~~~~

The StorageAuth model stores authorization credentials. Similarly to the
`Storage Model`_ it is linked to a storage authorization handler class via its
``storage_auth_type`` attribute. The handler actually performs the
authorization with the stored credentials. A typical example is the keystone
authorization used for the OpenStack Swift object storage.

.. table:: Default storage auth handlers

    +--------------------+----------------------------------------------------------------------------+
    | Storage auth type  | Description                                                                |
    +====================+============================================================================+
    | keystone           | Keystone client authorization. Requires the                                |
    |                    | `python-keystoneclient <https://pypi.org/project/python-keystoneclient/>`_ |
    |                    | and `python-swiftclient <https://pypi.org/project/python-swiftclient/>`_   |
    |                    | packages to be installed.                                                  |
    +--------------------+----------------------------------------------------------------------------+


Command Line Management Interfaces
----------------------------------

The following management commands provide facilities to manage the model
instances related to the data backend.


storageauth
  This command provides two subcommands to ``create`` and ``delete`` Storage
  Auths.

  create
    This sub-command allows to create a new Storage Auth. It requires the
    following arguments and supports the following options.

    name
      the name of the Storage Auth to be created for internal reference
    url
      the URL of the Storage Auth

    --type, -t
      the type of the Storage Auth
    --parameter, -p
      an additional parameter to set in the Storage Auth. Can be specified
      multiple times.
    --check
      check if the access to the Storage Auth actually works. Raises an error
      if not.

    The following example shows the creation of a keystone Storage Auth. The
    credentials are passed in as environment variables.

    .. code-block:: bash

        python manage.py storageauth create auth-cloud-ovh "${OS_AUTH_URL_SHORT}" \
            --type keystone \
            -p auth-version "${ST_AUTH_VERSION}" \
            -p identity-api-version="${ST_AUTH_VERSION}" \
            -p username "${OS_USERNAME}" \
            -p password "${OS_PASSWORD}" \
            -p tenant-name "${OS_TENANT_NAME}" \
            -p tenant-id "${OS_TENANT_ID}" \
            -p region-name "${OS_REGION_NAME}"

  delete
    To delete a Storage Auth, the subcommand ``delete`` with the Storage
    Auth name must be passed. The following example deletes the previously
    created Storage Auth from above.

    .. code-block:: bash

        python manage.py storageauth delete auth-cloud-ovh


storage
  This command allows to manage storages. The subcommands ``create``,
  ``delete`` allow to create new storages and delete no longer required ones.


  create
    This sub-command creates a new storage. The following parameters and
    options can be passed.

    name
      the storages name for internal reference
    url
      the location reference. The actual meaning may change according to the
      storage type.

    --type
      this is the string type of the storage. See the above
      table :ref:`Default Storage Handlers <default-storage-handlers>` for
      the available ones.
    --parent
      if the storage type supports parent storages, this
      parameter can be used to specify the parent storage. This allows to
      nest storages, e.g a ZIP archive on a HTTP server.
    --storage-auth
      this parameter must be used for storage types
      that require additional authorization, such as OpenStack swift
      storages.
      Use the name of the Storage Auth as a value of this parameter.

    The following example creates an OpenStack swift storage, linked to the
    Storage Auth created above.

    .. code-block:: bash

        python manage.py storage create \
            MySwiftContainer container \
            --type swift \
            --storage-auth auth-cloud-ovh

  delete
    This sub-command deletes a previously created storage.

    name
      the name of the storage to delete

    .. code-block:: bash

        python manage.py storage delete MySwiftContainer


  env
    This sub-command lists environment variables necessary to access the
    storage.

    name
      the name of the storage to list the environment variables for

    --path
      a path on the storage to list variables for

  list
    A sub-command to list filenames on a storage

    name
      the name of the storage to list files on

    --pattern
      a file glob pattern to filter the returned filenames
    --path
      a path on the storage to limit the file search
