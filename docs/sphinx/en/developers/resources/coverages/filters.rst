.. Module eoxserver.resources.coverages.filters

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
