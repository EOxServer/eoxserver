.. Handling Coverages
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
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

.. _Handling Coverages:

Handling Coverages
==================

This document will explain the basic principles of handling the most important
EOxServer data models: coverages. The layout of the data models is explained in
its `own chapter <Data Model Overview>`_.

Since all data models in EOxServer are based upon the
:class:`django.db.models.Model` class all associated documentation is also 
applicable to all EOxServer models. Highly recommendable is also the `Django 
QuerySet documentation <https://docs.djangoproject.com/en/dev/ref/models/querysets/>`_,


Creating Coverages
------------------

As we allready mentioned, coverages are basically Django models and are also
created as such.

The following example creates a :class:`Rectified Dataset 
<eoxserver.resources.coverages.models.RectifiedDataset>`.
::
  
    from eoxserver.core.util.timetools import parse_iso8601
    from django.contrib.gis import geos
    from eoxserver.resources.coverages import models


    dataset = models.RectifiedDataset(
        identifier="SomeIdentifier",
        size_x=1024, size_y=1024,
        min_x=0, min_y=0, max_x=90, max_y=90, srid=4326,
        begin_time=parse_iso8601("2014-05-10"),
        end_time=parse_iso8601("2014-05-12"),
        footprint=geos.MultiPolygon(geos.Polygon.from_bbox((0, 0, 90, 90)))
    )

    dataset.full_clean()
    dataset.save()

Of course, in a productive environment,  all of the above values would come 
from a actual data and metadata files and would be parsed by
:class:`metadata readers 
<eoxserver.resources.coverages.metadata.interfaces.MetadataReaderInterface>`.

Also, our dataset is currently not linked to any actual raster files. To do 
this, we need to create at least one :class:`DataItem 
<eoxserver.backends.models.DataItem>` and add it to our Dataset.
::

    from eoxserver.backends import models as backends


    data_item = backends.DataItem(
        dataset=dataset, location="/path/to/your/data.tif", format="image/tiff",
        semantic="bands"
    )

    data_item.full_clean()
    data_item.save()

This would link the dataset to a local file with the path 
``/path/to/your/data.tif``.

.. note:: Be cautious with relative paths! Depending on the deployment of the
   server instance the actual meaning of the paths might differ! If you are 
   using :class:`Storages <eoxserver.backends.models.Storage>` or 
   :class:`Packages <eoxserver.backends.models.Package>` relative paths are of
   course okay and unambigous since they are relative to the package or storage
   base location.


If you want to set up a data item that resides in a package (such as a .zip or
.tar file) or on a storage (like an HTTP or FTP server) you would need to set
up the :class:`Packages <eoxserver.backends.models.Package>` or 
:class:`Storages <eoxserver.backends.models.Storage>`:
::

    http_storage = backends.Storage(
        url="http://example.com/base_path/",
        storage_type="HTTP"
    )
    http_storage.full_clean()
    http_storage.save()

    data_item.storage = http_storage
    data_item.full_clean()
    data_item.save()

    # *or* in case of a package

    zip_package = backends.Package(
        location="/path/to/package.zip",
        format="ZIP"
    )
    zip_package.full_clean()
    zip_package.save()

    data_item.package = zip_package
    data_item.full_clean()
    data_item.save()


.. note:: A ``DataItem`` can only be in either a storage *or* a package. If it
   has defined both a storage and a package, the storage has precedence. If you
   want to have a ``Package`` that resides on a ``Storage`` you must use the 
   :attr:`storage <eoxserver.backends.models.Package.storage>` of the 
   ``Package``.


Creating Collections
--------------------

Collections are also created like `Coverages <Creating Coverages>`_, but usually
require less initial information (because the metadata is usually collected from
all entailed datasets).

The following creates a :class:`DatasetSeries 
<eoxserver.resources.coverages.models.DatasetSeries>`, a collection that can
entail almost any object of any subtype of :class:`EOObject
<eoxserver.resources.coverages.models.EOObject>`.
::

    dataset_series = models.DatasetSeries(identifier="CollectionIdentifier")
    dataset_series.full_clean()
    dataset_series.save()

The handling of collections is fairly simple: you use :meth:`insert() 
<eoxserver.resources.coverages.models.Collection.insert>` to add a dataset or
subcollection to a collection and use :meth:`remove() 
<eoxserver.resources.coverages.models.Collection.remove>` to remove them. 
Whenever either of the action is performed, the EO metadata of the collection is
updated according to the entailed datasets.
::

    dataset_series.insert(dataset)
    dataset_series.footprint  # is now exactly the same as dataset.footprint
    dataset_series.begin_time # is now exactly the same as dataset.begin_time
    dataset_series.end_time   # is now exactly the same as dataset.end_time

    dataset_series.remove(dataset)
    dataset_series.footprint  # is now None
    dataset_series.begin_time # is now None
    dataset_series.end_time   # is now None


Accessing Coverages
-------------------

The simplest way to retrieve a coverage is by its ID:
::

    from eoxserver.resources.coverages import models

    dataset = models.Coverage.objects.get(identifier="SomeIdentifier")
    
This always returns an object of type :class:`Coverage
<eoxserver.resources.coverages.models.Coverage>`, to "cast" it to the actual 
type:
::

    dataset = dataset.cast()

.. note:: the ``cast()`` method only makes a database lookup if the actual type
   and the current type do not match. Otherwise (and only in this case), the
   object itself is returned and no lookup is performed.

If you know the exact type of the coverage you want to look up you can also
make the query with the desired type:
::

    dataset = models.RectifiedDataset.objects.get(identifier="SomeIdentifier")

If the ``get()`` query did not match any object (or possible more than one) an
exception is raised.

If you want to query more than one coverage at one (e.g: all coverages in a 
certain time period) the ``filter()`` method is what you want:
::

    from eoxserver.core.util.timetools import parse_iso8601

    start = parse_iso8601("2014-05-10")
    stop = parse_iso8601("2014-05-12")
    coverages_qs = models.Coverage.objects.filter(
        begin_time__gte=start, end_time__lte=stop
    )
    for coverage in coverages_qs:
        ... # Do whatever you like with the coverage

.. note:: ``filter()`` returns a :class:`Django QuerySet 
   <django.db.models.query.QuerySet>` which can be chained to further refine the
   actual query. There is a lot of `documentation on the topic 
   <https://docs.djangoproject.com/en/dev/topics/db/queries/>`_ I
   highly recommend.

Usually coverages are organized in collections. If you want to iterate over a
collection simply do so:
::

    dataset_series = models.DatasetSeries.objects.get(
        identifier="CollectionIdentifier"
    )
    for eo_object in dataset_series:
        ...

It is important to note that such an iteration *does not* yield coverages, but
:class:`EOObjects <eoxserver.resources.coverages.models.EOObject>`. This is due
to the fact that collections might also contain other collections that don't 
necessarily have to inherit from :class:`Coverage 
<eoxserver.resources.coverages.models.Coverage>`. If you just want to explicitly
get all ``Coverages`` from a collection you can do it like this:
::

    coverages_qs = models.Coverage.objects.filter(
        collections__in=[dataset_series.pk]
    )

You can also combine the filters for searches within a collection:
::

    coverages_qs = dataset_series.eo_objects.filter(
        begin_time__gte=start, end_time__lte=stop
    )

    # append an additional geometry search
    coverages_qs = coverages_qs.filter(
        footprint__intersects=geos.Polygon.from_bbox((30,30,40,40))
    )


.. note:: There is no intrinsic order of ``EOObjects`` in a ``Collection``, but
   the ``EOObjects`` can be sorted when they are retrieved from a collection. 
   (e.g: by ``identifier``, ``begin_time`` or ``end_time``) using the 
   QuerySets ``order_by()`` method.


Accessing Coverage Data
-----------------------

As already discussed, the actual data and metadata files of a coverage are
referenced via its associated :class:`DataItems
<eoxserver.backends.models.DataItem>`. First, it is necessary to select the 
``DataItems`` that are actually relevant. This depends on the current situation:
for example in a metadata oriented request (such as the WCS DescribeCoverage 
operation) only metadata items will be accessed (and only if they are of 
relevance):
::

    metadata_items = dataset.data_items.filter(
        semantic="metadata", format="eogml"
    )

The above example selected only metadata items with the format "eogml".

In some cases the bands of a coverage are separated into multiple files that
have a ``semantic`` like this: "bands[x:y]". To select only those, we can use
the `startswith field lookup <https://docs.djangoproject.com/en/dev/ref/models/querysets/#std:fieldlookup-startswith>`_:
::

    band_items = dataset.data_items.filter(
        semantic__startswith="bands"
    )
    for band_item in band_items:
        # TODO: parse the band index or start/stop indices
        ...


Now that we have our relevant ``DataItems`` we can start using them.

We also explained that the DataItems can reside on a :class:`Storage 
<eoxserver.backends.models.Storage>` or inside a :class:`Package 
<eoxserver.backends.models.Package>`. Each storage has a specific storage type
and each package has a specific format. What types and formats are available
depends on your instance configuration, since the formats are implemented as
:class:`Components <eoxserver.core.component.Component>`. EOxServer ships with 
support of :mod:`local <eoxserver.backends.storages.local>`, :mod:`HTTP 
<eoxserver.backends.storages.http>`, :mod:`FTP 
<eoxserver.backends.storages.ftp>` and :mod:`Rasdaman 
<eoxserver.backends.storages.rasdaman>` storages and with :mod:`ZIP
<eoxserver.backends.packages.zip>` and :mod:`TAR
<eoxserver.backends.packages.tar>` packages. This list of both storages and
packages can be easily extended by creating plugin :class:`Components 
<eoxserver.core.component.Component>` implementing either the
:class:`FileStorageInterface
<eoxserver.backends.interfaces.FileStorageInterface>`,
:class:`ConnectedStorageInterface
<eoxserver.backends.interfaces.ConnectedStorageInterface>` or the
:class:`PackageInterface <eoxserver.backends.interfaces.PackageInterface>`.
See the :ref:`documentation for writing Plugins <Plugins>` for further info.

To ease the actual data access, there are two main methods: :func:`retrieve() 
<eoxserver.backends.access.retrieve>` and :func:`connect() 
<eoxserver.backends.access.connect>`.

Both functions have in common, that they operate on ``DataItems`` which are 
passed as the first parameter to the function.

The function :func:`retrieve() <eoxserver.backends.access.retrieve>` returns a
path to the local file: for already local files, the path is simply passed,
in other cases the file is downloaded, unpacked, retrieved or whatever is
necessary to make the file locally accessible. 
::

    data_item = dataset.data_items.get(semantic="metadata")
    local_path = retrieve(data_item)

You do not have to care for cleanup afterwards, since this is handled by 
EOxServers cache layer.

The function :func:`connect() <eoxserver.backends.access.connect>` works 
similarly, apart from the fact that it takes also storages into account that
do not provide files, but streams of data. Currently this only includes the
:mod:`Rasdaman Storage <eoxserver.backends.storages.rasdaman>`. If this 
function does not deal with a :class:`Connected Storages
<eoxserver.backends.interfaces.ConnectedStorageInterface>` it behaves like the
:func:`retrieve() <eoxserver.backends.access.retrieve>` function.
