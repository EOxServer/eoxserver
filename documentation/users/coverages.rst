Coverages
=========

This document describes the data model layout of the coverages, the internal
structure of earth observation products, collections and data files. It also
shows how these models can be interacted with via the command line interfaces.

Data model
----------

The data model is loosely based on the OGC coverages data models, especially
with the EO Application Profile for WCS 2.0.

Coverage Type
~~~~~~~~~~~~~

The coverage type describes the internal structure of coverages of a specific
type. The coverage type is comprised of a list of field types that define the
structure and metadata of a specific field of Data

TODO: ref SWE field

The coverage type has a unique name to allow its identification.


Product Type
~~~~~~~~~~~~

The product type model allows to define the structure of products by limiting
the coverage types each coverage is allowed to have for products of this
product type.

Additionally, each Product Type can be associated with a number of
`Browse Type`_ and `Mask Type`_ that define the masks and browses that products
of that type are allowed to have.


Browse Type
...........

A browse type defines a typical visual representation of a product. For this
purpose, it allows to define expression, scaling ranges and nodata values to
generate that representation (browse).

A browse type can either define a single output band (grey), three output bands
(RGB) or four output bands (RGBA).

Expressions must follow Python syntax rules but can only contain simple
arithmetic expressions. All identifiers must be names of field types that are
linked to coverage types in the list of allowed coverage types of the
referenced product type.


Mask Type
.........

These type models define what polygon masks can be linked to products of that
product type and whether the masks define areas of validity or invalidity.


Collection Type
~~~~~~~~~~~~~~~

These type models allow to define the shape of collections by allowing to limit
the product types and coverage types of product and coverages that can be added
to collections of their respective collection types.


EOObject
~~~~~~~~

This is the base model class for uniquely identifier geospatial objects.
EOObject provides the fields ``identifier`` (mandatory and unique), the
``footprint`` (its geometry) and its temporal distribution: ``begin_time`` and
``end_time``.

All objects inheriting from EOObject share a common pool of identifier. Thus,
it is, for example, not possible for a collection to have the same identifier
as a product or coverage.


.. _Grid Model:

Grid
~~~~

A grid defines a regularly spaced grid comprised of up to four axes. Each axis
can either be of spatial, temporal, evelation or other type. For each defined
axis, the regular offset value must be specified.

Each grid is associated with a coordinate reference system.

A grid can be named, making it easier to manage.

A grid does *not* provide an actual location or area, this information can only
be obtained with a Grid Fixture in conjunction with a grid.


.. _Mosaic Model:

Mosaic
~~~~~~

This model is a collection of homogenenous coverages, all sharing the same
coverage type and grid. This allows to access the mosaic as if it were a single
coverage by combinig the data from all its comprising elements.


.. _Coverage Model:

Coverage
~~~~~~~~

A coverage is an n-dimensional raster data set comprised of several fields.

A coverage is linked to at least one ArrayDataItem, a reference to the actual
raster data.

TODO: rel OGC coverage


.. _Product Model:

Product
~~~~~~~

A product is a sort of collection of geospatially and temporally very close
objects.


A product can combine multiple coverages which cover the same are but cannot be
combined to a single coverage because of different resolutions.

In some cases, coverages are not necessary at all, and just provide data items
for a binary download and browses for previewing.

.. _Browse Model:

Browse
......

A browse is always associated with a product and serves as a preview to the
actual data. Browses are materialized files that are either pre-generated or
can be generated from the coverage data.


.. _Mask Model:

Mask
....

Masks allow to specify regions in products for some kind of flag for example
validity. Each mask is linked to a `Mask Type`_.


.. _Collection Model:

Collection
~~~~~~~~~~

Multiple coverages and products can be grouped in a collection. This
relationship is many-to-many, so each product/coverage can be inserted into
multiple collections.

When a collection is linked to a `Collection Type`_ only Products and Coverages
whose types are of the set of allowed coverage/product types can be inserted.


Command Line Interfaces
-----------------------

The following command line interfaces can be executed via the ``manage.py``
utility of the instance. All commands are related to one of the models above
and use sub-commands for specific tasks.


``coveragetype``
~~~~~~~~~~~~~~~~

This command manages `Coverage Type`_ models and allows to inspect the
currently available ones. This command has four sub-commands:

- ``create``: creates a new Coverage Type with specifications
  from the parameters.
- ``import``: imports one or more Coverage Type definition from JSON files.
  TODO: show definitition, example
- ``delete``: deletes a Coverage Type by its name.
- ``list``: lists the stored Coverage Types


``producttype``
~~~~~~~~~~~~~~~

This command manages `Product Type`_ models. It provides the following
sub-commands:

- ``create``: creates a new Product Type. It allows to specify the
  allowed coverage types using the ``--coverage-type`` parameter.
  Also, rudimentary `Browse Type`_ instances and
  `Mask Type`_ instances can be created as well using the
  ``--browse-type`` and ``--mask-type`` parameters respectively.
  For both an own command (`browsetype`_ and `masktype`_) exists that
  allows for more options if needed.
- ``delete``: deletes a Product Type by name.
- ``list``: lists all available Product Types.


``browsetype``
~~~~~~~~~~~~~~

This command allows to create, delete and list `Browse Type`_ models. Since
Browse Types are always associated with a Product Type the first argument is
always the name of a Product Type. The sub-commands are in detail:

- ``create``: creates a new Browse Type for a Product Type. Allows to specify
  its expression, range and nodata value for each output band respectively.
- ``delete``: deletes a no longer needed Browse Type.
- ``list``: lists all Browse Types for a given Product Type.


``masktype``
~~~~~~~~~~~~

This command allows to create, delete and list `Mask Type`_ models. Since Mask
Types are always associated with a Product Type the first argument is always
the name of a Product Type. The sub-commands are in detail:

- ``create``: creates a new Mask Type for a Product Type. When the
  ``--validity`` flag is set, the masks if this type are used to mask in
  values, whereas otherwise to mask out areas.
- ``delete``: deletes a no longer needed Mask Type.
- ``list``: lists all Mask Types for a given Product Type.


``collectiontype``
~~~~~~~~~~~~~~~~~~

This command manages `Collection Type`_ models using the following
sub-commands:

- ``create``: creates a new Collection Type. To set the allowed
  Coverage/Product Types use the ``--coverage-type`` and ``--product-type```
  parameters.
- ``delete``: deletes a Collection Type by name.
- ``list``: lists all available Collection Types


``grid``
~~~~~~~~

This command allows to create and delete named `Grid Model`_ instances.

- ``create``: this creates a Grid. The first two arguments are the name
  and coordinate reference system of the grid, then the ``--name``,
  ``--type``, and ``--offset`` parameters can be repeated up to 4 times
  to define that many axes.
- ``delete``: deletes a Grid by name.


``coverage``
~~~~~~~~~~~~

This command allows the registration and deregistration of `Coverage Model`_
instances.

- ``register``: this sub-command registers a coverage.

  - ``--data``: this specifies a location for raster data. Multiple values
    can be used to denote that the data resides on a storage. If used in that
    way the first value can also be the name of a named storage.
    This parameter can be used multiple times, when the raster data is split
    into multiple files.
  - ``--meta-data``: similarly to the ``--data`` parameter, this parameter
    denotes a reference to meta-data. The same rules as for the ``--data``
    parameter also apply here.
  - ``--type``: specify the `Coverage Type`_ for this Coverage. By default no
    Coverage Type is used.
  - ``--grid``: specify the named `Grid Model`_ to use. By default an
    anonymous Grid is used.
  - ``--size``: specifies the size of the Coverage. This overrides the size
    extracted from the metadata/data. Must specify the size for each axis of
    the Grid.
  - ``--origin``: overrides the origin of the Coverage. Must provide a value
    for each axis of the Grid.
  - ``--footprint``: overrides the geographical footprint of the Coverage.
    Must be a valid WKT geometry.
  - ``--footprint-from-extent``: The footprint polygon shall be calculated
    from the Coverages extent.
  - ``--identifier``: override the Coverages identifier.
  - ``--identifier-template``: allows the construction of the final identifier
    from a template. Substitution values are passed in from the extracted
    metadata. e.g: ``{identifer}__B01``.
  - ``--begin-time``: override the begin timestamp of the Coverage. Must be a
    valid ISO 8601 datetime string.
  - ``--end-time``: override the end timestamp of the Coverage. Must be a
    valid ISO 8601 datetime string.
  - ``--product``: specify the Product identifier this Coverage shall be
    associated with. The Product must already be registered.
  - ``--collection``: specify the Collection identifier this Coverage shall be
    inserted into. The Collection must already exist.
  - ``--replace``: replace an already existing Coverage with the same
    identifier.
  - ``--print-identifier``: this switch prints the final identifier (after
    metadata extraction and potential templating) to stdout upon successful
    registration.

- ``deregister``: this sub-command de-registers the Coverage with the provided
  identifier. This will update all Collections metadata (footprint, begin-/end
  time) unless the ``--not-refresh-collections`` switch is set.


``product``
~~~~~~~~~~~

This command manages `Product Model`_ instances.

- ``register``: this sub-command registers products.

  - ``--metadata-file``: adds a metadata file to the product. As with file
    links for Coverages, the product file can be located on a storage. For
    these cases, multiple values can be used to specify the chain of
    locations.
  - ``--footprint``: overrides the geographical footprint of the Coverage.
    Must be a valid WKT geometry.
  - ``--identifier``: override the Product identifier.
  - ``--identifier-template``: allows the construction of the final identifier
    from a template. Substitution values are passed in from the extracted
    metadata. e.g: ``{identifer}__B01``.
  - ``--begin-time``: override the begin timestamp of the Coverage. Must be a
    valid ISO 8601 datetime string.
  - ``--end-time``: override the end timestamp of the Coverage. Must be a
    valid ISO 8601 datetime string.
  - ``--set``: sets a specific metadata value for that product. This
    parameter always uses two values: the name of the parameter key
    and its value.
    TODO: possible metadata keys to set
  - ``--type``: specify the `Product Type`_ for this Product. By default no
    Product Type is used.
  - ``--mask``: specify a mask file to be added to this product. Must be
    two values: the masks name and its file location.
  - ``--mask-geomety``: specify a mask using its geometry directly. Must be
    two values: the masks name and its WKT geometry representation.
  - ``--no-extended-metadata``:
  - ``--no-masks``:
  - ``--no-browses``:
  - ``--no-metadata``:
  - ``--package``: specify the main data package for this Product.
  - ``--collection``: specify the Collection identifier this Product shall be
    inserted into. The Collection must already exist.
  - ``--replace``: replace an already existing Product with the same
    identifier.
  - ``--print-identifier``: this switch prints the final identifier (after
    metadata extraction and potential templating) to stdout upon successful
    registration.

- ``deregister``: deregisters a Product via its identifier.
- ``discover``: print the contents of the main package file of a Product.
  Optionally a glob can be supplied to filter the files.


``browse``
~~~~~~~~~~

This command allows to manage `Browse Model`_ instances of a `Product Model`_.

- ``register``: This sub-command registers a Browse to a Product.
  The required arguments are the Products identifier and the location.
  As with other data items, the location can be of multiple parts, when
  the location is relative to a storage.
- ``generate``: TODO
- ``deregister``: TODO


``mask``
~~~~~~~~

This command allows to manage `Mask Model`_ instances of a `Product Model`_.

- ``register``: registers a Mask for a Product.
  TODO


``collection``
~~~~~~~~~~~~~~

This command manages `Collection Model`_ instances. As usual, it
uses sub-commands to allow fine control over the specific aspects
and tasks of a collection.

- ``create``: creates a new collection. Must be provided with an
  identifier. Additionally, it can be of a specific `Collection Type`_
  using the ``--type`` parameter. Collection metadata ca be specified
  via the ``--set`` parmeter which is a pair of name and value.
  TODO: metadata fields to use
- ``delete``: this sub-command deletes a Collection by its identifier.
- ``insert``: with this sub-command one or more `Coverage Model`_ instances
  or `Product Model`_ instances can be inserted into the collection. This
  command checks whether the to be inserted objects are of the allowed
  types when a Collection Type is set for this Collection.
- ``exclude``: this command allows to remove one or more objects from a
  collection.
- ``purge``: this command purges all Coverages and Products from this
  collection, leaving it effectively empty.
  TODO: not yet implemented
- ``summary``: collects metadata from all entailed Products and
  Coverages to generate a summary that is stored in the Collection.
  This allows a quick overview of the metadata ranges and specific
  values of all objects in the collection. With the ``--no-coverages``
  or ``--no-products`` the collecting of metadata for that specific
  object type can be disabled.


``mosaic``
~~~~~~~~~~

This command manages `Mosaic Model`_ instances with a variety of sub-commands.

- ``create``: creates a new Mosaic. An identifier is mandatory and both
  a `Coverage Type`_ and a `Grid Model`_ must be specified using the ``--type``
  and ``--grid`` parameters respectively.
- ``delete``: deletes a Mosaic via its identifier.
- ``insert``: insert one or more `Coverage Model`_ instances into this Mosaic.
  The Coverage Type must be the same for all and the Mosaic.
- ``exclude``: exclude one or more Coverages from the Mosaic.
- ``refresh``:
- ``purge``:
