#-----------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#-----------------------------------------------------------------------
"""
This module defines filters and filter expressions for EO Coverages.
For more information on filters, see :mod:`eoxserver.core.filters`.
"""

import math
from datetime import datetime

from django.db.models import Q, Count
from django.contrib.gis.geos import (
    fromstr as geos_fromstr, Polygon
)
from django.contrib.gis.gdal import SpatialReference

from eoxserver.core.system import System
from eoxserver.core.registry import FactoryInterface
from eoxserver.core.filters import (
    FilterExpressionInterface, FilterInterface, SimpleExpression,
    SimpleExpressionFactory
)
from eoxserver.core.util.timetools import UTCOffsetTimeZoneInfo
from eoxserver.core.exceptions import (
    InternalError, InvalidExpressionError, UnknownAttribute
)
from eoxserver.backends.base import LocationWrapper
from eoxserver.resources.coverages.models import EOMetadataRecord
from eoxserver.resources.coverages.wrappers import (
    RectifiedDatasetWrapper, ReferenceableDatasetWrapper,
    RectifiedStitchedMosaicWrapper, DatasetSeriesWrapper
)

#-----------------------------------------------------------------------
# Helper classes
#-----------------------------------------------------------------------

class Slice(object):
    """
    This class contains information about a slice subsetting. The
    constructor accepts three arguments:
    
    * ``crs_id``: either ``"imageCRS"`` or an integer EPSG SRID,
    * ``axis_label``: the axis label the slicing operation refers to,
    * ``slice_point``: a :class:`float` or :class:`int` containing the
      slice point information
    
    :exc:`~.InternalError` is raised if arguments do not validate.
    """
    def __init__(self, crs_id, axis_label, slice_point):
        self.__validate(crs_id, axis_label, slice_point)
        
        self.__crs_id = crs_id
        self.__axis_label = axis_label
        self.__slice_point = slice_point
    
    def __validate(self, crs_id, axis_label, slice_point):
        if not (crs_id == "imageCRS" or isinstance(crs_id, int)):
            raise InternalError(
                "'crs_id' must be set to 'imageCRS' or to an integer."
            )
        
        if not (isinstance(slice_point, float) or\
           isinstance(slice_point, int)):
            raise InternalError(
                "Slice point must be float or int."
            )
    
    #: Read only attribute.
    @property
    def crs_id(self):
        return self.__crs_id
    
    #: Read only attribute.
    @property
    def axis_label(self):
        return self.__axis_label
    
    # Read only attribute.
    @property
    def slice_point(self):
        return self.__slice_point

class BoundedArea(object):
    """
    This class contains information about a bounded area. The
    constructor accepts a ``crs_id`` and four bounds arguments
    ``minx, miny, maxx, maxy``. The ``crs_id`` parameter may be set to
    ``"imageCRS"`` or an integer EPSG SRID. The bounds parameters may
    be set to a :class:`float` or :class:`int` value designating the
    bound in the given coordinate system or to ``"unbounded"``.
    
    :exc:`~.InternalError` is raised if the arguments do not validate.
    :exc:`~.InvalidExpressionError` is raised if the lower bounds of
    an axis are greater than the upper bounds.
    """
    def __init__(self, crs_id, minx, miny, maxx, maxy):
        self.__validate(crs_id, minx, miny, maxx, maxy)
        
        self.__crs_id = crs_id
        self.__minx = minx
        self.__miny = miny
        self.__maxx = maxx
        self.__maxy = maxy
    
    def __validate(self, crs_id, minx, miny, maxx, maxy):
        if not (crs_id == "imageCRS" or isinstance(crs_id, int)):
            raise InternalError(
                "'crs_id' must be set to 'imageCRS' or to an integer."
            )
        
        for bound in (minx, miny, maxx, maxy):
            if not (bound == "unbounded" or isinstance(bound, float) or\
                    isinstance(bound, int)):
                raise InternalError(
                    "Bounds must be set to 'unbounded', float or int."
                )
        
        if (not (minx == "unbounded" or maxx == "unbounded") and minx > maxx) or\
           (not (miny == "unbounded" or maxy == "unbounded") and miny > maxy):
            raise InvalidExpressionError(
                "Invalid bounds: lower bound greater than upper bound."
            )
    
    #: Read only attribute.
    @property
    def crs_id(self):
        return self.__crs_id
    
    #: Read only attribute.
    @property
    def minx(self):
        return self.__minx

    #: Read only attribute.
    @property
    def miny(self):
        return self.__miny

    #: Read only attribute.
    @property
    def maxx(self):
        return self.__maxx

    #: Read only attribute.
    @property
    def maxy(self):
        return self.__maxy

class TimeInterval(object):
    """
    This class contains information about a time interval. The
    constructor accepts two arguments: ``begin`` and ``end`` which
    must be set either to the string ``"unbounded"`` or a
    :class:`datetime.datetime` object.
    
    :exc:`~.InternalError` is raised if the arguments do not validate.
    :exc:`~.InvalidExpressionError` is raised if the begin time is
    later than the end time.
    """
    
    def __init__(self, begin, end):
        self.__validate(begin, end)
        
        self.__begin = begin
        self.__end = end
    
    def __validate(self, begin, end):
        for timestamp in (begin, end):
            if not (timestamp == "unbounded" or isinstance(timestamp, datetime)):
                raise InternalError(
                    "Time bound must be 'unbounded' or 'datetime.datetime' object."
                )
        
        if not (begin == "unbounded" or end == "unbounded") and end < begin:
            raise InvalidExpressionError(
                "Begin of time interval later than end."
            )
    
    @property
    def begin(self):
        return self.__begin
        
    @property
    def end(self):
        return self.__end

#-----------------------------------------------------------------------
# Filter Expressions
#-----------------------------------------------------------------------

class AttributeExpression(SimpleExpression):
    """
    Filter expression implementation representing an attribute lookup
    on a model. Expects three operands:
    
    * the attribute name; the possible names are defined separately for
      each resource class;
    * the matching operation; the range of applicable operations 
      comprises the field lookups defined by Django; the 'search',
      'regex' and 'iregex' operations are not supported because they are
      database dependent; the shortcuts "=", "<", "<=", ">=", ">" are
      allowed;
    * the search value; has to be convertible to the type of the
      attribute
    """
    REGISTRY_CONF = {
        "name": "Attribute Lookup Expression",
        "impl_id": "resources.coverages.filters.AttributeExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "attr"
    NUM_OPS = 3
    
    LOOKUPS = (
        "=", "exact", "iexact", "contains", "icontains", "in", ">" ,
        "gt", ">=", "gte", "<", "lt", "<=", "lte", "startswith",
        "istartswith", "endswith", "iendswith", "range", "year",
        "month", "day", "weekday", "isnull"
    )
    
    
    def _validateOperands(self, operands):
        super(AttributeExpression, self)._validateOperands(operands)
        
        if operands[1].lstrip("!") not in self.LOOKUPS:
            raise InternalError(
                "'%s' is not a known field lookup operation." % \
                operands[1]
            )

AttributeExpressionImplementation = \
FilterExpressionInterface.implement(AttributeExpression)

class TimeSliceExpression(SimpleExpression):
    """
    Filter expression implementation representing a time slice. Expects
    one operand: a :class:`datetime.datetime` object representing the
    slice point in time.
    """
    REGISTRY_CONF = {
        "name": "Time Slice Expression",
        "impl_id": "resources.coverages.filters.TimeSliceExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "time_slice"
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(TimeSliceExpression, self)._validateOperands(operands)
    
        if not isinstance(operands[0], datetime):
            raise InternalError(
                "Expected 'datetime.datetime' object as operand, got '%s' object." % operands[0].__class__.__name__
            )

TimeSliceExpressionImplementation = \
FilterExpressionInterface.implement(TimeSliceExpression)

class TimeIntervalExpression(SimpleExpression):
    """
    Filter expression implementation representing a time interval.
    It expects one operand of type :class:`TimeInterval`.
    """
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(TimeIntervalExpression, self)._validateOperands(operands)
    
        if not isinstance(operands[0], TimeInterval):
            raise InternalError(
                "Expected 'TimeInterval' object as operand, got '%s' object." % operands[0].__class__.__name__
            )

class IntersectingTimeIntervalExpression(TimeIntervalExpression):
    """
    Filter expression implementation that matches if a time or
    time interval intersects with the time interval specified in the
    expression. Inherits from :class:`TimeIntervalExpression`.
    """
    REGISTRY_CONF = {
        "name": "Intersecting Time Interval Expression",
        "impl_id": "resources.coverages.filters.IntersectingTimeIntervalExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "time_intersects"
    
IntersectingTimeIntervalExpressionImplementation = \
FilterExpressionInterface.implement(IntersectingTimeIntervalExpression)

class ContainingTimeIntervalExpression(TimeIntervalExpression):
    """
    Filter expression implementation that matches if a time or time
    interval is contained in the time interval specified in the
    expression. Inherits from :class:`TimeIntervalExpression`.
    """
    REGISTRY_CONF = {
        "name": "Containing Time Interval Expression",
        "impl_id": "resources.coverages.filters.ContainingTimeIntervalExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "time_within"
    
ContainingTimeIntervalExpressionImplementation = \
FilterExpressionInterface.implement(ContainingTimeIntervalExpression)

class SpatialSliceExpression(SimpleExpression):
    """
    Filter expression implementation that represents a slice subsetting.
    It expects one operand of type :class:`Slice`.
    """
    REGISTRY_CONF = {
        "name": "Spatial Slice Expression",
        "impl_id": "resources.coverages.filters.SpatialSliceExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "spatial_slice"
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(SpatialSliceExpression, self)._validateOperands(operands)
        
        if not isinstance(operands[0], Slice):
            raise InternalError(
                "Expected operand of type 'Slice', got '%s' object" %\
                operands[0].__class__.__name__
            )

SpatialSliceExpressionImplementation = \
FilterExpressionInterface.implement(SpatialSliceExpression)

class BoundedAreaExpression(SimpleExpression):
    """
    Filter expression implementation that represents a trim or BBOX
    subsetting. It expects one operand of type :class:`BoundedArea`.
    """
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(BoundedAreaExpression, self)._validateOperands(operands)
        
        if not isinstance(operands[0], BoundedArea):
            raise InvalidExpressionError(
                "Expected 'BoundedArea' object as operand, got '%s' object" %\
                operands[0].__class__.__name__
            )

class FootprintIntersectsAreaExpression(BoundedAreaExpression):
    """
    Filter expression implementation that matches if the footprint
    of an object intersects the given :class:`BoundedArea`. Inherits
    from :class:`BoundedAreaExpression`.
    """
    REGISTRY_CONF = {
        "name": "Footprint intersects area Expression",
        "impl_id": "resources.coverages.filters.FootprintIntersectsAreaExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "footprint_intersects_area"

FootprintIntersectsAreaExpressionImplementation = \
FilterExpressionInterface.implement(FootprintIntersectsAreaExpression)

class FootprintWithinAreaExpression(BoundedAreaExpression):
    """
    Filter expression implementation that matches if the footprint
    of an object is contained within the given :class:`BoundedArea`.
    Inherits from :class:`BoundedAreaExpression`.
    """
    REGISTRY_CONF = {
        "name": "Footprint within area Expression",
        "impl_id": "resources.coverages.filters.FootprintWithinAreaExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "footprint_within_area"

FootprintWithinAreaExpressionImplementation = \
FilterExpressionInterface.implement(FootprintWithinAreaExpression)

class ContainedCoverageExpression(SimpleExpression):
    """
    Filter expression referring to the coverages contained in a
    container object (StitchedMosaic or DatasetSeries). Expects one
    operand, namely an integer resource ID relating to the container
    object.
    """
    REGISTRY_CONF = {
        "name": "Contained Coverage Expression",
        "impl_id": "resources.coverages.filters.ContainedCoverageExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "contained_in"
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(ContainedCoverageExpression, self)._validateOperands(operands)
        
        if not isinstance(operands[0], int):
            raise InternalError(
                "Expected integer resource ID, got '%s' object." %
                operands[0].__class__.__name__
            )

ContainedCoverageExpressionImplementation = \
FilterExpressionInterface.implement(ContainedCoverageExpression)

class ContainsCoverageExpression(SimpleExpression):
    """
    Filter expression referring to the coverages containing a
    StitchedMosaic or Dataset. Expects one operand, namely an integer resource
    ID relating to the contained object.
    """
    REGISTRY_CONF = {
        "name": "Contains Coverage Expression",
        "impl_id": "resources.coverages.filters.ContainsCoverageExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "contains"
    NUM_OPS = 1
    
    def _validateOperands(self, operands):
        super(ContainsCoverageExpression, self)._validateOperands(operands)
        
        if not isinstance(operands[0], int):
            raise InternalError(
                "Expected integer resource ID, got '%s' object." %
                operands[0].__class__.__name__
            )

ContainsCoverageExpressionImplementation = \
FilterExpressionInterface.implement(ContainsCoverageExpression)

class OrphanedCoverageExpression(SimpleExpression):
    """
    Filter expression implementation that matches coverages which are
    not related to any container (StitchedMosaic or DatasetSeries).
    Takes no operands.
    """
    
    REGISTRY_CONF = {
        "name": "Orphaned Coverage Expression",
        "impl_id": "resources.coverages.filters.OrphanedCoverageExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "orphaned"
    NUM_OPS = 0
    
OrphanedCoverageExpressionImplementation = \
FilterExpressionInterface.implement(OrphanedCoverageExpression)


class LocationReferencesDatasetExpression(SimpleExpression):
    """
    Filter expression that matches datasets which are referenced by a location.
    """
    
    REGISTRY_CONF = {
        "name": "Location References Dataset Expression",
        "impl_id": "resources.coverages.filters.LocationReferencesDatasetExpression",
        "factory_ids": ("resources.coverages.filters.CoverageExpressionFactory",)
    }
    
    OP_NAME = "referenced_by"
    NUM_OPS = 1

    def _validateOperands(self, operands):
        super(LocationReferencesDatasetExpression, self)._validateOperands(operands)
        
        if not isinstance(operands[0], LocationWrapper):
            raise InternalError(
                "Expected LocationWrapper, got '%s' object." %
                operands[0].__class__.__name__
            )

LocationReferencesDatasetExpressionImplementation = \
FilterExpressionInterface.implement(LocationReferencesDatasetExpression)

#-----------------------------------------------------------------------
# Filters
#-----------------------------------------------------------------------

class AttributeFilter(object):
    """
    Base class for attribute lookup filters.
    """
    
    WRAPPER_CLASS = None # To be overridden by implementations
    
    def _getField(self, attr):
        return self.WRAPPER_CLASS().getAttrField(attr)
        
    def _getLookup(self, op):
        if op == "=":
            return ""
        elif op == "<":
            return "__lt"
        elif op == "<=":
            return "__lte"
        elif op == ">=":
            return "__gte"
        elif op == ">":
            return "__gt"
        else:
            return "__%s" % op
    
    def _matchValues(self, model_value, op, value):
        try:
            if op in ("=", "exact"):
                return model_value == value
            elif op == "iexact":
                return model_value.lower() == value.lower()
            elif op == "contains":
                return model_value.find(value) != -1
            elif op == "icontains":
                return model_value.lower().find(value.lower()) != -1
            elif op == "in":
                return model_value in value
            elif op in ("<", "lt"):
                return model_value < value
            elif op in ("<=", "lte"):
                return model_value <= value
            elif op in (">=", "gte"):
                return model_value >= value
            elif op in (">", "gt"):
                return model_value > value
            elif op == "startswith":
                return model_value.startswith(value)
            elif op == "istartswith":
                return model_value.lower().startswith(value.lower())
            elif op == "endswith":
                return model_value.endswith(value)
            elif op == "iendswith":
                return model_value.lower().endswith(value.lower())
            elif op == "range":
                return value[0] <= model_value and model_value <= value[1]
            elif op == "year":
                return model_value.year == value
            elif op == "month":
                return model_value.month == value
            elif op == "day":
                return model_value.day == value
            elif op == "weekday":
                return model_value.weekday() == value
            elif op == "isnull":
                if value:
                    return model_value is None
                else:
                    return model_value is not None
        except:
            raise InvalidExpressionError(
                "Could not apply attribute expression to given attribute."
            )
    
    def _splitRawOp(self, raw_op):
        if raw_op.startswith("!"):
            invert = True
            op = raw_op.lstrip("!")
        else:
            invert = False
            op = raw_op
        
        return (invert, op)

    def applyToQuerySet(self, expr, qs):
        attr, raw_op, value = expr.getOperands()
        
        invert, op = self._splitRawOp(raw_op)
        
        try:
            field = self._getField(attr)
        # fail gracefully if the attribute name is unknown
        except UnknownAttribute:
            return qs
            
        if not invert:
            return qs.filter(**{
                "%s%s" % (field, self._getLookup(op)): value
            })
        else:
            return qs.exclude(**{
                "%s%s" % (field, self._getLookup(op)): value
            })
    
    def resourceMatches(self, expr, res):
        attr, raw_op, value = expr.getOperands()

        invert, op = self._splitRawOp(raw_op)
        
        model_value = res.getAttrValue(attr)
        
        if not invert:
            return self._matchValues(model_value, op, value)
        else:
            return not self._matchValues(model_value, op, value)

class RectifiedDatasetAttributeFilter(AttributeFilter):
    """
    Filter that executes attribute lookups on Rectified Datasets.
    """
    
    REGISTRY_CONF = {
        "name": "Attribute Lookup Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetAttribute",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.AttributeExpression"
        }
    }
    
    WRAPPER_CLASS = RectifiedDatasetWrapper

RectifiedDatasetAttributeFilterImplementation = \
FilterInterface.implement(RectifiedDatasetAttributeFilter)

class ReferenceableDatasetAttributeFilter(AttributeFilter):
    """
    Filter that executes attribute lookup operations on Referenceable
    Datasets.
    """
    
    REGISTRY_CONF = {
        "name": "Attribute Lookup Filter for Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetAttribute",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.AttributeExpression"
        }
    }
    
    WRAPPER_CLASS = ReferenceableDatasetWrapper

ReferenceableDatasetAttributeFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetAttributeFilter)

class RectifiedStitchedMosaicAttributeFilter(AttributeFilter):
    """
    Filter that executes attribute lookup operations on Rectified
    Stitched Mosaics.
    """
    
    REGISTRY_CONF = {
        "name": "Attribute Lookup Filter for Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicAttribute",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.AttributeExpression"
        }
    }
    
    WRAPPER_CLASS = RectifiedStitchedMosaicWrapper

RectifiedStitchedMosaicAttributeFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicAttributeFilter)

class TimeSliceFilter(object):
    """
    Filter class for time slice operations.
    """
    def applyToQuerySet(self, expr, qs):
        timestamp = expr.getOperands()[0]
        
        qs = qs.exclude(eo_metadata__timestamp_begin__gt=timestamp)
        qs = qs.exclude(eo_metadata__timestamp_end__lt=timestamp)
        
        return qs
    
    def resourceMatches(self, expr, res):
        timestamp = expr.getOperands()[0]
        
        return not timestamp < res.getBeginTime() or\
               not res.getEndTime() < timestamp

class RectifiedDatasetTimeSliceFilter(TimeSliceFilter):
    """
    Filter which matches Rectified Datasets whose acquisition time
    interval contains a given timestamp.
    """
    REGISTRY_CONF = {
        "name": "Time Slice Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetTimeSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.TimeSliceExpression"
        }
    }

RectifiedDatasetTimeSliceFilterImplementation = \
FilterInterface.implement(RectifiedDatasetTimeSliceFilter)

class ReferenceableDatasetTimeSliceFilter(TimeSliceFilter):
    """
    Filter which matches Referenceable Datasets whose acquisition time
    interval contains a given timestamp.
    """
    REGISTRY_CONF = {
        "name": "Time Slice Filter for Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetTimeSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.TimeSliceExpression"
        }
    }

ReferenceableDatasetTimeSliceFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetTimeSliceFilter)

class RectifiedStitchedMosaicTimeSliceFilter(TimeSliceFilter):
    """
    Filter which matches Rectified Stitched Mosaics whose acquisition
    time interval contains a given timestamp.
    """
    REGISTRY_CONF = {
        "name": "Time Slice Filter for Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicTimeSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.TimeSliceExpression"
        }
    }

RectifiedStitchedMosaicTimeSliceFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicTimeSliceFilter)

class IntersectingTimeIntervalFilter(object):
    """
    Filter class for 'time_intersects' operations.
    """
    def applyToQuerySet(self, expr, qs):
        begin = expr.getOperands()[0].begin
        end = expr.getOperands()[0].end
        
        if begin == "unbounded":
            if end == "unbounded":
                return qs
            else:
                return qs.filter(
                    eo_metadata__timestamp_begin__lte=end
                )
        else:
            if end == "unbounded":
                return qs.filter(
                    eo_metadata__timestamp_end__gte=begin
                )
            else:
                return qs.exclude(
                    eo_metadata__timestamp_begin__gt=end
                ).exclude(
                    eo_metadata__timestamp_end__lt=begin
                )

    def resourceMatches(self, expr, res):
        begin = expr.getOperands()[0].begin
        end = expr.getOperands()[0].end
        
        res_begin = res.getBeginTime() 
        res_end = res.getEndTime()
        
        if res_begin.tzinfo is None and begin.tzinfo is not None:
            res_begin = res_begin.replace(tzinfo=UTCOffsetTimeZoneInfo())
        if res_end.tzinfo is None and end.tzinfo is not None:
            res_end = res_end.replace(tzinfo=UTCOffsetTimeZoneInfo())
        
        return not end < res_begin and \
               not res_end < begin

class RectifiedDatasetIntersectingTimeIntervalFilter(IntersectingTimeIntervalFilter):
    """
    Filter which matches Rectified Datasets whose acquisition time
    interval intersects a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_intersects' operations on Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetIntersectingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.IntersectingTimeIntervalExpression"
        }
    }

RectifiedDatasetIntersectingTimeIntervalFilterImplementation = \
FilterInterface.implement(RectifiedDatasetIntersectingTimeIntervalFilter)

class ReferenceableDatasetIntersectingTimeIntervalFilter(IntersectingTimeIntervalFilter):
    """
    Filter which matches Referenceable Datasets whose acquisition time
    interval intersects a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_intersects' operations on Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetIntersectingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.IntersectingTimeIntervalExpression"
        }
    }

ReferenceableDatasetIntersectingTimeIntervalFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetIntersectingTimeIntervalFilter)

class RectifiedStitchedMosaicIntersectingTimeIntervalFilter(IntersectingTimeIntervalFilter):
    """
    Filter which matches Rectified Stitched Mosaics whose acquisition
    time interval intersects a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_intersects' operations on Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicIntersectingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.IntersectingTimeIntervalExpression"
        }
    }

RectifiedStitchedMosaicIntersectingTimeIntervalFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicIntersectingTimeIntervalFilter)

class ContainingTimeIntervalFilter(object):
    """
    Filter class for 'time_within' operations.
    """
    def applyToQuerySet(self, expr, qs):
        begin = expr.getOperands()[0].begin
        end = expr.getOperands()[0].end
        
        if begin == "unbounded":
            if end == "unbounded":
                return qs
            else:
                return qs.filter(
                    eo_metadata__timestamp_end__lte=end
                )
        else:
            if end == "unbounded":
                return qs.filter(
                    eo_metadata__timestamp_begin__gte=begin
                )
            else:
                return qs.filter(
                    eo_metadata__timestamp_begin__gte=begin,
                    eo_metadata__timestamp_end__lte=end
                )

    def resourceMatches(self, expr, res):
        begin = expr.getOperands()[0].begin
        end = expr.getOperands()[0].end
        
        return not res.getBeginTime() < begin and\
               not end < res.getEndTime()

class RectifiedDatasetContainingTimeIntervalFilter(ContainingTimeIntervalFilter):
    """
    Filter which matches Rectified Datasets whose acquisition time
    interval is contained within a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_within' operations on Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetContainingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainingTimeIntervalExpression"
        }
    }

RectifiedDatasetContainingTimeIntervalFilterImplementation = \
FilterInterface.implement(RectifiedDatasetContainingTimeIntervalFilter)

class ReferenceableDatasetContainingTimeIntervalFilter(ContainingTimeIntervalFilter):
    """
    Filter which matches Referenceable Datasets whose acquisition time
    interval is contained within a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_within' operations on Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetContainingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainingTimeIntervalExpression"
        }
    }

ReferenceableDatasetContainingTimeIntervalFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetContainingTimeIntervalFilter)

class RectifiedStitchedMosaicContainingTimeIntervalFilter(ContainingTimeIntervalFilter):
    """
    Filter which matches Rectified Stitched Mosaics whose acquisition
    time interval is contained within a given time interval.
    """
    REGISTRY_CONF = {
        "name": "Filter for 'time_within' operations on Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicContainingTimeInterval",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainingTimeIntervalExpression"
        }
    }

RectifiedStitchedMosaicContainingTimeIntervalFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicContainingTimeIntervalFilter)
    
class SpatialFilter(object):
    """
    Common base class for spatial filters.
    """
            
    def _getSRS(self, crs_id):
        if crs_id == "imageCRS":
            raise InvalidExpressionError(
                "Cannot use geospatial filters with pixel coordinates."
            )

        try:
            srs = SpatialReference(crs_id)
        except Exception, e:
            raise InvalidExpressionError(
                "Unknown SRID %d." % crs_id
            )
            
        return srs
        
    def _getCRSBounds(self, crs_id):
        srs = self._getSRS(crs_id)
        
        if srs.geographic:
            return (-180.0, -90.0, 180.0, 90.0)
        else:
            earth_circumference = 2*math.pi*srs.semi_major
        
            return (
                -earth_circumference,
                -earth_circumference,
                earth_circumference,
                earth_circumference
            )
            
    def _getCRSTolerance(self, crs_id):
        srs = self._getSRS(crs_id)
        
        if srs.geographic:
            return 1e-8
        else:
            return 1e-2
            
class SpatialSliceFilter(SpatialFilter):
    """
    Common base class for spatial slice filters.
    """
    
    def _getLine(self, slice, max_extent):
        #_max_extent = self._transformMaxExtent(slice.crs_id, max_extent)
        _max_extent = self._getCRSBounds(slice.crs_id)
        
        if slice.axis_label.lower() in ("x", "lon", "long"):
            line = Line(
                (slice.slice_point, _max_extent[1]),
                (slice.slice_point, _max_extent[3])
            )
        elif slice.axis_label.lower() in ("y", "lat"):
            line = Line(
                (_max_extent[0], slice.slice_point),
                (_max_extent[2], slice.slice_point)
            )
        else:
            raise InvalidExpressionError(
                "Unknown axis label '%s'." % slice.axis_label
            )
        
        line.srid = slice.crs_id
        
        if slice.crs_id != 4326:
            line.transform(4326)
        
        return line
    
    def applyToQuerySet(self, expr, qs):
        slice = expr.getOperands()[0]
        
        line = self._getLine(slice)
        
        # NOTE: this is a hack to account for bugs in GeoDjango
        # Should be:
        # return qs.filter(eo_metadata__footprint__intersects=line)
        
        eoqs = EOMetadataRecord.objects.filter(
            footprint__intersects=line
        )
        
        return qs.filter(
            eo_metadata__in=tuple(eoqs.values_list("pk", flat=True))
        )
        
        # End of hack
    
    def resourceMatches(self, expr, res):
        slice = expr.getOperands()[0]
        
        footprint = res.getFootprint()
        
        line = self._getLine(slice)
        
        return footprint.intersects(line)

class RectifiedDatasetSpatialSliceFilter(SpatialSliceFilter):
    """
    Filter which matches Rectified Datasets whose footprint intersects
    a given spatial slice.
    """
    REGISTRY_CONF = {
        "name": "Spatial Slice Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetSpatialSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.SpatialSliceExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifieddatasetrecord_set"

RectifiedDatasetSpatialSliceFilterImplementation = \
FilterInterface.implement(RectifiedDatasetSpatialSliceFilter)
    
class ReferenceableDatasetSpatialSliceFilter(SpatialSliceFilter):
    """
    Filter which matches Referenceable Datasets whose footprint
    intersects a given spatial slice.
    """
    REGISTRY_CONF = {
        "name": "Spatial Slice Filter for Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetSpatialSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.SpatialSliceExpression"
        }
    }
    
    def _getRelationName(self):
        return "referenceabledatasetrecord_set"

        
ReferenceableDatasetSpatialSliceFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetSpatialSliceFilter)

class RectifiedStitchedMosaicSpatialSliceFilter(SpatialSliceFilter):
    """
    Filter which matches Rectified Stitched Mosaics whose footprint
    intersects a given spatial slice.
    """

    REGISTRY_CONF = {
        "name": "Spatial Slice Filter for Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicSpatialSlice",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.SpatialSliceExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifiedstitchedmosaicrecord_set"
    
    def _getSizeField(self, axis_label):
        if axis_label in ("x", "lon", "long", "Long"):
            return "extent__size_x"
        else:
            return "extent__size_y"

        
RectifiedStitchedMosaicSpatialSliceFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicSpatialSliceFilter)


class FootprintFilter(SpatialFilter):
    """
    Common base class for footprint-related filters.
    """    
    def _getPolygon(self, bounded_area):
        #_max_extent = self._transformMaxExtent(
        #    bounded_area.crs_id, max_extent
        #)
        
        _max_extent = self._getCRSBounds(bounded_area.crs_id)
        
        if bounded_area.minx == "unbounded":
            minx = _max_extent[0]
        else:
            minx = max(bounded_area.minx, _max_extent[0])
        
        if bounded_area.miny == "unbounded":
            miny = _max_extent[1]
        else:
            miny = max(bounded_area.miny, _max_extent[1])
        
        if bounded_area.maxx == "unbounded":
            maxx = _max_extent[2]
        else:
            maxx = min(bounded_area.maxx, _max_extent[2])
        
        if bounded_area.maxy == "unbounded":
            maxy = _max_extent[3]
        else:
            maxy = min(bounded_area.maxy, _max_extent[3])
        
        # add a tolerance to the extent to account for string conversion and
        # rounding errors
        e = self._getCRSTolerance(bounded_area.crs_id)
        minx -= e; miny -= e; maxx += e; maxy += e
        
        poly = Polygon.from_bbox((minx, miny, maxx, maxy))
        poly.srid = bounded_area.crs_id
        
        if bounded_area.crs_id != 4326:
            # reproject to WGS 84
            poly.transform(4326)
        
        return poly

class FootprintIntersectsAreaFilter(FootprintFilter):
    """
    Base filter class matching EO Coverages whose footprint intersects a
    given area.
    """
    def applyToQuerySet(self, expr, qs):
        #max_extent = self._getMaxExtent(qs)
                
        poly = self._getPolygon(expr.getOperands()[0])
        
        # NOTE: this is a hack to account for bugs in GeoDjango
        # Should be:
        #return qs.filter(eo_metadata__footprint__intersects=poly)
        
        eoqs = EOMetadataRecord.objects.filter(
            footprint__intersects=poly
        )
        
        return qs.filter(
            eo_metadata__in=tuple(eoqs.values_list("pk", flat=True))
        )
        
        # End of hack
    
    def resourceMatches(self, expr, res):
        footprint = res.getFootprint()

        poly = self._getPolygon(expr.getOperands()[0])
        
        return footprint.intersects(poly)

class FootprintWithinAreaFilter(FootprintFilter):
    """
    Filter matching EO Coverages whose footprint lies within a given
    area.
    """
    
    def applyToQuerySet(self, expr, qs):
        poly = self._getPolygon(expr.getOperands()[0])
        
        # NOTE: this is a hack to account for bugs in GeoDjango
        # Should be:
        # return qs.filter(eo_metadata__footprint__within=poly)
        
        eoqs = EOMetadataRecord.objects.filter(footprint__within=poly)
        
        return qs.filter(
            eo_metadata__in=tuple(eoqs.values_list("pk", flat=True))
        )
        
        # End of hack
    
    def resourceMatches(self, expr, res):
        footprint = res.getFootprint()
        
        poly = self._getPolygon(expr.getOperands()[0])
        
        return footprint.within(poly)

class RectifiedDatasetFootprintIntersectsAreaFilter(FootprintIntersectsAreaFilter):
    """
    Filter which matches Rectified Datasets whose footprint intersects
    a given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint intersects area Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetFootprintIntersectsArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintIntersectsAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifieddatasetrecord_set"

RectifiedDatasetFootprintIntersectsAreaFilterImplementation = \
FilterInterface.implement(RectifiedDatasetFootprintIntersectsAreaFilter)


class RectifiedDatasetFootprintWithinAreaFilter(FootprintWithinAreaFilter):
    """
    Filter which matches Rectified Datasets whose footprint is
    contained within a given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint within area Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.RectifiedDatasetFootprintWithinArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintWithinAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifieddatasetrecord_set"

RectifiedDatasetFootprintWithinAreaFilterImplementation = \
FilterInterface.implement(RectifiedDatasetFootprintWithinAreaFilter)

class ReferenceableDatasetFootprintIntersectsAreaFilter(FootprintIntersectsAreaFilter):
    """
    Filter which matches Referenceable Datasets whose footprint
    intersects a given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint intersects area Filter for Referenceable Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetFootprintIntersectsArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintIntersectsAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "referenceabledatasetrecord_set"

ReferenceableDatasetFootprintIntersectsAreaFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetFootprintIntersectsAreaFilter)

class ReferenceableDatasetFootprintWithinAreaFilter(FootprintWithinAreaFilter):
    """
    Filter which matches Referenceable Datasets whose footprint is
    contained within a given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint intersects area Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.ReferenceableDatasetFootprintWithinArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintWithinAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "referenceabledatasetrecord_set"

ReferenceableDatasetFootprintWithinAreaFilterImplementation = \
FilterInterface.implement(ReferenceableDatasetFootprintWithinAreaFilter)

class RectifiedStitchedMosaicFootprintIntersectsAreaFilter(FootprintIntersectsAreaFilter):
    """
    Filter which matches Rectified Stitched Mosaics whose footprint
    intersects a given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint intersects area Filter for Rectified StitchedMosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicFootprintIntersectsArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintIntersectsAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifiedstitchedmosaicrecord_set"

RectifiedStitchedMosaicFootprintIntersectsAreaFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicFootprintIntersectsAreaFilter)


class RectifiedStitchedMosaicFootprintWithinAreaFilter(FootprintWithinAreaFilter):
    """
    Filter which matches Rectified Stiched Mosaics whose footprint is
    contained within given bounded area.
    """
    REGISTRY_CONF = {
        "name": "Footprint within area Filter for Rectified StitchedMosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicFootprintWithinArea",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.FootprintWithinAreaExpression"
        }
    }
    
    def _getRelationName(self):
        return "rectifiedstitchedmosaicrecord_set"

RectifiedStitchedMosaicFootprintWithinAreaFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicFootprintWithinAreaFilter)

class ContainedRectifiedDatasetFilter(object):
    """
    Filter which matches RectifiedDatasets contained in a given
    RectifiedStitchedMosaic or Dataset series.
    """
    REGISTRY_CONF = {
        "name": "Contained Rectified Dataset Filter",
        "impl_id": "resources.coverages.filters.ContainedRectifiedDataset",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        container_id = expr.getOperands()[0]
        
        return qs.filter(
            Q(rect_stitched_mosaics__pk=container_id) | \
            Q(dataset_series_set__pk=container_id)
        )
        
    def resourceMatches(self, expr, res):
        container_id = expr.getOperands()[0]
        
        return res.containedIn(container_id)

ContainedRectifiedDatasetFilterImplementation = \
FilterInterface.implement(ContainedRectifiedDatasetFilter)

class ContainedReferenceableDatasetFilter(object):
    """
    Filter which matches ReferenceableDatasets contained in a given
    DatasetSeries.
    """
    REGISTRY_CONF = {
        "name": "Contained Referenceable Dataset Filter",
        "impl_id": "resources.coverages.filters.ContainedReferenceableDatasetFilter",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        container_id = expr.getOperands()[0]
        
        return qs.filter(dataset_series_set__pk=container_id)
    
    def resourceMatches(self, expr, res):
        container_id = expr.getOperands()[0]
        
        return res.containedIn(container_id)

ContainedReferenceableDatasetFilterImplementation = \
FilterInterface.implement(ContainedReferenceableDatasetFilter)

class ContainedRectifiedStitchedMosaicFilter(object):
    """
    Filter which matches RectifiedStitchedMosaics contained in a given
    DatasetSeries.
    """
    REGISTRY_CONF = {
        "name": "Contained Referenceable Dataset Filter",
        "impl_id": "resources.coverages.filters.ContainedRectifiedStitchedMosaicFilter",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        container_id = expr.getOperands()[0]
        
        return qs.filter(dataset_series_set__pk=container_id)
    
    def resourceMatches(self, expr, res):
        container_id = expr.getOperands()[0]
        
        return res.containedIn(container_id)

ContainedRectifiedStitchedMosaicFilterImplementation = \
FilterInterface.implement(ContainedRectifiedStitchedMosaicFilter)

class RectifiedStitchedMosaicContainsFilter(object):
    """
    Filter which matches RectifiedStitchedMosaics which contain the
    RectifiedDataset with the resource primary key conveyed with the
    expression.
    """
    
    REGISTRY_CONF = {
        "name": "Filter for 'contains' operations on RectifiedStitchedMosaics",
        "impl_id": "resources.coverages.filters.RectifiedStitchedMosaicContains",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainsCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        res_id = expr.getOperands()[0]
        
        return qs.filter(rect_datasets__pk=res_id)
    
    def resourceMatches(self, expr, res):
        res_id = expr.getOperands()[0]
        
        return res.contains(res_id)
        
RectifiedStitchedMosaicContainsFilterImplementation = \
FilterInterface.implement(RectifiedStitchedMosaicContainsFilter)

class DatasetSeriesContainsFilter(object):
    """
    Filter which matches DatasetSeries which contain the (Rectified
    or Referenceable) Dataset with the resource primary key conveyed
    with the expression.
    """

    REGISTRY_CONF = {
        "name": "Filter for 'contains' operations on DatasetSeries",
        "impl_id": "resources.coverages.filters.DatasetSeriesContains",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.DatasetSeriesWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.ContainsCoverageExpression"
        }
    }

    def applyToQuerySet(self, expr, qs):
        res_id = expr.getOperands()[0]
        
        return qs.filter(
            Q(rect_datasets__pk=res_id) | Q(ref_datasets__pk=res_id)
        )
    
    def resourceMatches(self, expr, res):
        res_id = expr.getOperands()[0]
        
        return res.contains(res_id)

DatasetSeriesContainsFilterImplementation = \
FilterInterface.implement(DatasetSeriesContainsFilter)

class OrphanedRectifiedDatasetFilter(object):
    """
    Filter which matches RectifiedDatasets that are neither contained
    in a DatasetSeries nor in a RectifiedStitchedMosaic.
    """
    
    REGISTRY_CONF = {
        "name": "Orphan Filter for Rectified Datasets",
        "impl_id": "resources.coverages.filters.OrphanedRectifiedDataset",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.OrphanedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        return qs.annotate(
            dataset_series_count=Count('dataset_series_set')
        ).annotate(
            rect_stitched_mosaics_count=Count('rect_stitched_mosaics')
        ).filter(
            dataset_series_count=0,
            rect_stitched_mosaics_count=0
        )
    
    def resourceMatches(self, expr, res):
        return res.getContainerCount() == 0

OrphanedRectifiedDatasetFilterImplementation = \
FilterInterface.implement(OrphanedRectifiedDatasetFilter)

class OrphanedReferenceableDatasetFilter(object):
    """
    Filter which matches ReferenceableDatasets that are not contained
    in any DatasetSeries.
    """
    
    REGISTRY_CONF = {
        "name": "Orphan Filter for Referenceable Datasets",
        "impl_id": "resources.coverages.filters.OrphanedReferenceableDataset",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.OrphanedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        return qs.annotate(
            dataset_series_count=Count('dataset_series_set')
        ).filter(
            dataset_series_count=0
        )
    
    def resourceMatches(self, expr, res):
        return res.getContainerCount() == 0
        
OrphanedReferenceableDatasetFilterImplementation = \
FilterInterface.implement(OrphanedReferenceableDatasetFilter)

class OrphanedRectifiedStitchedMosaicFilter(object):
    """
    Filter which matches RectifiedStitchedMosaics that are not contained
    in any DatasetSeries.
    """
    
    REGISTRY_CONF = {
        "name": "Orphan Filter for Rectified Stitched Mosaics",
        "impl_id": "resources.coverages.filters.OrphanedRectifiedStitchedMosaic",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.OrphanedCoverageExpression"
        }
    }
    
    def applyToQuerySet(self, expr, qs):
        return qs.annotate(
            dataset_series_count=Count('dataset_series_set')
        ).filter(
            dataset_series_count=0
        )
    
    def resourceMatches(self, expr, res):
        return res.getContainerCount() == 0
        
OrphanedRectifiedStitchedMosaicFilterImplementation = \
FilterInterface.implement(OrphanedRectifiedStitchedMosaicFilter)

class LocationReferencesRectifiedDatasetFilter(object):
    """
    Filter which matches RectifiedDatasets which are referenced by a
    specified location.
    """
    
    REGISTRY_CONF = {
        "name": "Location References Rectified Dataset Filter",
        "impl_id": "resources.coverages.filters.LocationReferencesRectifiedDatasetFilter",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.LocationReferencesDatasetExpression"
        }
    }

    def applyToQuerySet(self, expr, qs):
        location = expr.getOperands()[0]
        
        if location.getType() == "local":
            return qs.filter(
                data_package__localdatapackage__data_location__path=location.getPath()
            )
        elif location.getType() == "ftp":
            return qs.filter(
                data_package__remotedatapackage__data_location__path=location.getPath()
            ).filter(
                data_package__remotedatapackage__data_location__storage__host=location.getHost(),
                data_package__remotedatapackage__data_location__storage__port=location.getPort(),
                data_package__remotedatapackage__data_location__storage__user=location.getUser(),
                data_package__remotedatapackage__data_location__storage__passwd=location.getPassword()
            )
        elif location.getType() == "rasdaman":
            return qs.filter(
                data_package__rasdamandatapackage__data_location__collection=location.getCollection(),
                data_package__rasdamandatapackage__data_location__oid=location.getOID()
            ).filter(
                data_package__rasdamandatapackage__data_location__storage__host=location.getHost(),
                data_package__rasdamandatapackage__data_location__storage__port=location.getPort(),
                data_package__rasdamandatapackage__data_location__storage__user=location.getUser(),
                data_package__rasdamandatapackage__data_location__storage__passwd=location.getPassword()
            )
        
    def resourceMatches(self, expr, res):
        location = expr.getOperands()[0]
        
        if location.getType() == "local":
            return location.getPath() == res.getData().getLocation().getPath()
        elif location.getType() == "ftp":
            return (
                location.getPath() == res.getData().getLocation().getPath() and
                location.getHost() == res.getData().getLocation().getHost() and
                location.getPort() == res.getData().getLocation().getPort() and
                location.getUser() == res.getData().getLocation().getUser() and
                location.getPassword() == res.getData().getLocation().getPassword()
            )
        elif location.getType() == "rasdaman":
            return (
                location.getCollection() == res.getData().getLocation().getCollection() and
                location.getOID() == res.getData().getLocation().getOID() and
                location.getHost() == res.getData().getLocation().getHost() and
                location.getPort() == res.getData().getLocation().getPort() and
                location.getUser() == res.getData().getLocation().getUser() and
                location.getPassword() == res.getData().getLocation().getPassword()
            )

LocationReferencesRectifiedDatasetFilterImplementation = \
FilterInterface.implement(LocationReferencesRectifiedDatasetFilter)

class LocationReferencesReferencableDatasetFilter(object):
    """
    Filter which matches RectifiedDatasets which are referenced by a
    specified location.
    """
    
    REGISTRY_CONF = {
        "name": "Location References Rectified Dataset Filter",
        "impl_id": "resources.coverages.filters.LocationReferencesReferencableDatasetFilter",
        "registry_values": {
            "core.filters.res_class_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
            "core.filters.expr_class_id": "resources.coverages.filters.LocationReferencesDatasetExpression"
        }
    }

    def applyToQuerySet(self, expr, qs):
        location = expr.getOperands()[0]
        
        if location.getType() == "local":
            return qs.filter(
                data_package__localdatapackage__data_location__path=location.getPath()
            )
        elif location.getType() == "ftp":
            return qs.filter(
                data_package__remotedatapackage__data_location__path=location.getPath()
            ).filter(
                data_package__remotedatapackage__data_location__storage__host=location.getHost(),
                data_package__remotedatapackage__data_location__storage__port=location.getPort(),
                data_package__remotedatapackage__data_location__storage__user=location.getUser(),
                data_package__remotedatapackage__data_location__storage__passwd=location.getPassword()
            )
        elif location.getType() == "rasdaman":
            return qs.filter(
                data_package__rasdamandatapackage__data_location__collection=location.getCollection(),
                data_package__rasdamandatapackage__data_location__oid=location.getOID()
            ).filter(
                data_package__rasdamandatapackage__data_location__storage__host=location.getHost(),
                data_package__rasdamandatapackage__data_location__storage__port=location.getPort(),
                data_package__rasdamandatapackage__data_location__storage__user=location.getUser(),
                data_package__rasdamandatapackage__data_location__storage__passwd=location.getPassword()
            )
        
    def resourceMatches(self, expr, res):
        location = expr.getOperands()[0]
        
        if location.getType() == "local":
            return location.getPath() == res.getData().getLocation().getPath()
        elif location.getType() == "ftp":
            return (
                location.getPath() == res.getData().getLocation().getPath() and
                location.getHost() == res.getData().getLocation().getHost() and
                location.getPort() == res.getData().getLocation().getPort() and
                location.getUser() == res.getData().getLocation().getUser() and
                location.getPassword() == res.getData().getLocation().getPassword()
            )
        elif location.getType() == "rasdaman":
            return (
                location.getCollection() == res.getData().getLocation().getCollection() and
                location.getOID() == res.getData().getLocation().getOID() and
                location.getHost() == res.getData().getLocation().getHost() and
                location.getPort() == res.getData().getLocation().getPort() and
                location.getUser() == res.getData().getLocation().getUser() and
                location.getPassword() == res.getData().getLocation().getPassword()
            )

LocationReferencesReferencableDatasetFilterImplementation = \
FilterInterface.implement(LocationReferencesReferencableDatasetFilter)

#-----------------------------------------------------------------------
# Factory
#-----------------------------------------------------------------------

class CoverageExpressionFactory(SimpleExpressionFactory):
    """
    This is the factory which gives access to the filter expressions
    defined in this module. It inherits from
    :class:`~.SimpleExpressionFactory`.
    """    
    REGISTRY_CONF = {
        "name": "Coverage Filter Expression Factory",
        "impl_id": "resources.coverages.filters.CoverageExpressionFactory"
    }

CoverageExpressionFactoryImplementation = \
FactoryInterface.implement(CoverageExpressionFactory)
