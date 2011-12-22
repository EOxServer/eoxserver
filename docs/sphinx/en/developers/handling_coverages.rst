.. Handling Coverages
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
  #          Fabian Schindler <fabian.schindler@eox.at>
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

Creating coverages
------------------

The best (and suggested) way to create a coverage is to use a coverage manager.
For each type of coverage there is the according coverage manager. As usual in,
EOxServer the correct coverage manager can be retrieved by the systems registry,
using the interface ID of the manager and the type of the coverages to identify
and find the correct manager:
::

    mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    )

The managers ``create`` method can now be used to create a new record of the
requested coverage. Since the possible arguments vary for each coverage type
and use case, please refer to the actual :mod:`implementation documentation 
<eoxserver.resources.coverages.covmgrs>` of the manager for the complete list 
of possible parameters.

The following example creates a rectified dataset as simple as passing a local
path to a data file and a metadatafile and the name of the range type, which
unfortunately cannot be identified otherwise at the time being.
::

    mgr.create(
        "SomeCoverageID",
        local_path="path/to/data.tif",
        md_local_path="path/to/metadata.xml",
        range_type_name="RGB"
    )


Coverage IDs
~~~~~~~~~~~~

To handle the reservation of Coverage IDs the :class:`~.CoverageIdManager` can
be used.
::

    from eoxserver.resources.coverages.covmgrs import CoverageIDManager
    mgr = CoverageIDManager()

Checking if a coverage ID is still available is done like this: 
::

    if mgr.available(someID):
        ...

To reserve a specific Coverage ID for a certain amount of time, use the
``reserve`` method. The first and only mandatory parameter is the ID to be
reserved. With the ``request_id`` parameter an additional ID can be associated
with the reserved coverage. This is especially useful for asynchronous
situations. The ``until`` parameter defines for how long the reservation will
be valid:
::

    from datetime import datetime, timedelta

    mgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))

If the ID could not be reserved an exception is raised, as described in the
modules documentation.

When the Coverage ID is not being used anymore it can be released with the
``release`` method:
::

    mgr.release("SomeCoverageID")

When the optional ``fail`` parameter is set to true, an exception will be
thrown if the ID was not previously reserved.


Finding Coverages
-----------------

There are several techniques to search for coverages in the system, depending
what information is desired and what information is provided. Typically a
factory is used to get the correct wrapper of a coverage, namely the 
:class:`~.EOCoverageFactory`.

The simplest case is to find a coverage according to its Coverage ID:
::

    from eoxserver.core.system import System

    coverage_wrapper = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.EOCoverageFactory",
        {"obj_id": coverage_id}
    )

This returns the coverage wrapper according to the coverages type, or None, if
no such coverage exists.

For more sophisticated searches, filter expressions have to be used. In case of
coverage filters, the :class:`~.CoverageExpressionFactory` creates the required
expressions. In the following example, we create a filter expression to get
all coverages whose footprint intersects with the area defined by the
:class:`~.BoundedArea`:
::

    from eoxserver.resources.coverages.filters import BoundedArea

    filter_exprs = []
    filter_exprs.append(System.getRegistry().getFromFactory(
        "resources.coverages.filters.CoverageExpressionFactory",
        {
            "op_name": "footprint_intersects_area",
            "operands": (BoundedArea(srid, minx, miny, maxx, maxy),)
        }
    ))

With our filter expressions, we are now able to get the list of coverages
complying to our filters with the ``find`` method of the
:class:`~.EOCoverageFactory` which returns a list of all objects intersecting
with our region.:
::

    factory = System.getRegistry().bind(
        "resources.coverages.wrappers.EOCoverageFactory"
    )
    coverages = factory.find(filter_exprs=filter_exprs)


Updating Coverages
------------------

Updating a coverage is either done by the wrappers or, on a more higher level,
with the coverage manager.

Updating with the wrappers is limited to several methods on the specific
wrapper itself (e.g.: the
:meth:`~eoxserver.resources.coverages.wrappers.RectifiedStitchedMosaicWrapper.addCoverage`
method of the :class:`~.RectifiedStitchedMosaicWrapper`) or the
:meth:`~eoxserver.core.resources.ResourceWrapper.setAttrValue` method. The
latter one is directly coupled to the wrappers ``FIELDS`` lookup dictionary
which expands to field lookup on the according model.

The following example demonstrates either use:
::

    rect_stitched_mosaic_wrapper = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.EOCoverageFactory",
        {"obj_id": mosaic_coverage_id}
    )

    rect_stitched_mosaic_wrapper.addCoverage(
        System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": coverage_id}
        )
    )

    rect_stitched_mosaic_wrapper.setAttrValue("size_x", 1000)
    rect_stitched_mosaic_wrapper.setAttrValue("size_y", 1000)

To know what attributes are allowed in the `setAttrValue`, either look up the
class variable ``FIELDS`` or call the
:meth:`~eoxserver.core.wrappers.ResourceWrapper.getAttrNames` method of the
wrapper .

Another way to update existing coverages is to use the correct coverage manager.
Its :meth:`~eoxserver.resources.coverages.covmgrs.BaseManager.update` method
can be supplied three (optional) dict arguments:

 * ``link``: adds a reference to another object in the database. This is used
   for e.g ``container_ids``, ``coverages`` or ``data_sources``.
 * ``unlink``: removes a reference to another object. It has the same arguments
   as the ``link`` dict.
 * ``set``: Sets an integral value or a collection of values in the database
   object. Here are also keys from the ``FIELDS`` accepted.

The usable arguments depend on the actually used coverage manager type, but are
almost the same as the arguments available for the ``create`` method.

The following example demonstrates the use of the coverage managers ``update``
method with a rectified stitched mosaic:
::

    mgr = System.getRegistry().findAndBind(
        intf_id="resources.coverages.interfaces.Manager",
        params={
            "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
        }
    )

    mgr.update(
        obj_id=mosaic_coverage_id,
        link={
            "coverage_ids": ["RectifiedDatasetCoverageID"]
        },
        unlink={
            "container_ids": ["DatasetSeriesEOID"]
        }
        set={
            "size_x": 1000,
            "size_y": 1000,
            "eo_metadata": EOMetadata(
                "NewEOID",
                timestamp_begin,
                timestamp_end,
                GEOSGeometry(some_footprint)
            )
        }
    )
