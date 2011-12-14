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
all coverages whose footprint intersects with the area defined by the :class:
`~.BoundedArea`:
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
complying to our filters with the ``find`` method of the :class:
`~.EOCoverageFactory`:
::

    factory = System.getRegistry().bind(
        "resources.coverages.wrappers.EOCoverageFactory"
    )
    coverages = factory.find(filter_exprs=filter_exprs)


Updating Coverages
------------------
