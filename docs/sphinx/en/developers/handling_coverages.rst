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
path to a data file and a meta-data-file and the name of the range type, which
unfortunately cannot be identified otherwise at the time being.
::

    mgr.create(
        "SomeCoverageID",
        local_path="path/to/data.tif",
        md_local_path="path/to/metadata.xml",
        range_type_name="RGB"
    )


Coverage ID Uniqueness 
~~~~~~~~~~~~~~~~~~~~~~

The :class:`~.CoverageIdManager` helps during creation of new, and querying
existing Coverage IDs::

    from eoxserver.resources.coverages.covmgrs import CoverageIDManager
    idmgr = CoverageIDManager()

The Coverage ID must be unique for all types of coverages, such as, *Rectified*
or *Referenceable* data-sets. This aspect is especially important for graceful
handling of Coverage IDs' conflicts in case of concurrent inserts of new
coverages. Once a new Coverage ID is approved by the EOxServer in course of the
processing of an insert request, any other insert request must not be allowed 
to use the same Coverage ID. Therefore the :class:`~.CoverageIdManager` allows
Coverage ID *reservation* to grant the Coverage ID exclusivity during 
of the actual coverage insert. The reservation is performed by the
:func:`~eoxserver.resources.coverages.covmgrs.CoverageIdManager.reserve` method::

    from datetime import datetime, timedelta
    idmgr.reserve("SomeCoverageID", until=datetime.now() + timedelta(days=1))

If the Coverage ID cannot be reserved (most likely, because it is used by an
existing coverage, or reserved by another insert request) an exception is raised,
as described in the method's documentation.

The reservation is released automatically after expiration of the given time-out
(the optional ``until`` parameter). The default time-out value can be configured 
via EOxServer configuration file (section ``resources.coverages.coverage_id``,
field ``reservation_time``, default value ``0:0:30:0``, i.e., 30 min.).

The reservation can be revoked by the  
:func:`~eoxserver.resources.coverages.covmgrs.CoverageIdManager.release`
method::

    idmgr.release("SomeCoverageID")

Although it is not necessary to release a booked Coverage ID, we encourage
to do so when possible. 

Whether a Coverage ID is neither in use nor reserved can be checked by the 
:func:`~eoxserver.resources.coverages.covmgrs.CoverageIdManager.available`
method::

    if idmgr.available(someID):
        # there is neither coverage nor cov.ID reservation 
        ...


Finding Coverages
-----------------

There are several techniques to search for coverages in the system,
depending on what information is desired and/or provided.
In a case, when the Coverage ID is known, it is possible to use 
:func:`~eoxserver.resources.coverages.covmgrs.CoverageIdManager.check` method 
of :class:`~.CoverageIdManager` to check whether this ID is used by an existing 
coverage::

    if idmgr.check(someID):
        # there is an coverage with this ID 

Once we know there is an existing coverage we can query type of the coverage 
by the
:func:`~eoxserver.resources.coverages.covmgrs.CoverageIdManager.getCoverageType`
method in order to select the proper handling of the coverage type:: 

    ctype = idmgr.getCoverageType(someID):

    if   ctype == "PlainCoverage" : 
        ...
    elif ctype == "RectifiedDataset" : 
        ...
    elif ctype == "ReferenceableDataset" : 
        ...
    elif ctype == "RectifiedStitchedMosaic" : 
        ...
    else : 
        # invalid coverage ID 
        ...

Alternatively, a factory can used to get the correct wrapper of a coverage, namely the
:class:`~.EOCoverageFactory`. The simplest case is to find a coverage according 
to its Coverage ID::

    from eoxserver.core.system import System

    coverage_wrapper = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.EOCoverageFactory",
        {"obj_id": coverage_id}
    )

This command returns the proper coverage wrapper according to the coverages type, 
or None, if no such coverage exists.

For more sophisticated searches, filter expressions have to be used. In case of
coverage filters, the :class:`~.CoverageExpressionFactory` creates the required
expressions. In the following example, we create a filter expression to get
all coverages whose footprint intersects with the area defined by the
:class:`~.BoundedArea`::

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
with our region.::

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

The following example demonstrates either use::

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
can be supplied three (optional) dictionary arguments:

 * ``link``: adds a reference to another object in the database. This is used,
   e.g., for ``container_ids``, ``coverages`` or ``data_sources``.
 * ``unlink``: removes a reference to another object. It has the same arguments
   as the ``link`` dictionary 
 * ``set``: Sets an integral value or a collection of values in the database
   object. Here are also keys from the ``FIELDS`` accepted.

The usable arguments depend on the actually used coverage manager type, but are
almost the same as the arguments available for the ``create`` method.

The following example demonstrates the use of the coverage managers ``update``
method with a rectified stitched mosaic::

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
