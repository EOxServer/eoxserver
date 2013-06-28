.. Module eoxserver.resources.coverages.filters
  #-----------------------------------------------------------------------------
  # $Id$
  #
  # Project: EOxServer <http://eoxserver.org>
  # Authors: Stephan Krause <stephan.krause@eox.at>
  #          Stephan Meissl <stephan.meissl@eox.at>
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

.. _module_resources_coverages_filters:

Module eoxserver.resources.coverages.filters
============================================

.. automodule:: eoxserver.resources.coverages.filters

Helper Classes
--------------

.. autoclass:: TimeInterval
   :members:

.. autoclass:: Slice
   :members:

.. autoclass:: BoundedArea
   :members:

Filter Expressions
------------------

Filter expressions (i.e. implementations of
:class:`~.FilterExpressionInterface`) define certain search constraints
for resource factories. Filter expressions should be created using
the :meth:`~.CoverageExpressionFactory.get` or
:meth:`~.CoverageExpressionFactory.find` methods of
:class:`CoverageExpressionFactory`. They will be translated into the
corresponding filters by the resource factory.

.. autoclass:: TimeSliceExpression
   :members:
   
.. autoclass:: TimeIntervalExpression
   :members:
   
.. autoclass:: IntersectingTimeIntervalExpression
   :members:
   
.. autoclass:: ContainingTimeIntervalExpression
   :members:
   
.. autoclass:: SpatialSliceExpression
   :members:
   
.. autoclass:: BoundedAreaExpression
   :members:
   
.. autoclass:: FootprintIntersectsAreaExpression
   :members:

.. autoclass:: FootprintWithinAreaExpression
   :members:

Filters
-------

Filters (i.e. implementations of :class:`~.FilterInterface`) are used
primarily to select EO Coverages matching certain criteria. In general
developers will not use filters directly, but define filter expressions
instead which will be applied to the EO Coverages when invoking the
:meth:`~eoxserver.core.resources.ResourceFactory.find` method of a
resource factory.

.. autoclass:: TimeSliceFilter

.. autoclass:: RectifiedDatasetTimeSliceFilter

.. autoclass:: ReferenceableDatasetTimeSliceFilter

.. autoclass:: RectifiedStitchedMosaicTimeSliceFilter

.. autoclass:: IntersectingTimeIntervalFilter

.. autoclass:: RectifiedDatasetIntersectingTimeIntervalFilter

.. autoclass:: ReferenceableDatasetIntersectingTimeIntervalFilter

.. autoclass:: RectifiedStitchedMosaicIntersectingTimeIntervalFilter

.. autoclass:: ContainingTimeIntervalFilter

.. autoclass:: RectifiedDatasetContainingTimeIntervalFilter

.. autoclass:: ReferenceableDatasetContainingTimeIntervalFilter

.. autoclass:: RectifiedStitchedMosaicContainingTimeIntervalFilter

.. autoclass:: SpatialFilter

.. autoclass:: SpatialSliceFilter

.. autoclass:: RectifiedDatasetSpatialSliceFilter

.. autoclass:: ReferenceableDatasetSpatialSliceFilter

.. autoclass:: RectifiedStitchedMosaicSpatialSliceFilter

.. autoclass:: FootprintFilter

.. autoclass:: FootprintIntersectsAreaFilter

.. autoclass:: RectifiedDatasetFootprintIntersectsAreaFilter

.. autoclass:: ReferenceableDatasetFootprintIntersectsAreaFilter

.. autoclass:: RectifiedStitchedMosaicFootprintIntersectsAreaFilter

.. autoclass:: FootprintWithinAreaFilter

.. autoclass:: RectifiedDatasetFootprintWithinAreaFilter

.. autoclass:: ReferenceableDatasetFootprintWithinAreaFilter

.. autoclass:: RectifiedStitchedMosaicFootprintWithinAreaFilter

.. autoclass:: ContainedRectifiedDatasetFilter

.. autoclass:: ContainedReferenceableDatasetFilter

Factories
---------

.. autoclass:: CoverageExpressionFactory
   :members:
