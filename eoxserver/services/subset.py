#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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
#-------------------------------------------------------------------------------


import logging

from django.contrib.gis.geos import Polygon, LineString

from eoxserver.resources.coverages import crss
from eoxserver.services.exceptions import (
    InvalidAxisLabelException, InvalidSubsettingException
)


__all__ = ["Subsets", "Trim", "Slice"]

logger = logging.getLogger(__name__)


class Subsets(list):
    """ Convenience class to handle a variety of spatial and/or temporal 
        subsets.
    """

    def __init__(self, iterable, crs=None, allowed_types=None):
        """ Constructor. Allows to add set the initial subsets
        """
        self.allowed_types = allowed_types if allowed_types is not None else (
            Trim, Slice
        )
        # Do a manual insertion here to assure integrity
        for subset in iterable:
            self.append(subset)

        self._crs = crs

    # List API
    
    def extend(self, iterable):
        for subset in iterable:
            self._check_subset(subset)
            super(Subsets, self).append(subset)


    def append(self, subset):
        self._check_subset(subset)
        super(Subsets, self).append(subset)


    def insert(self, i, subset):
        self._check_subset(subset)
        super(Subsets, self).insert(i, subset)

    # Subset related stuff

    @property
    def has_x(self):
        return any(map(lambda s: s.is_x, self))

    @property
    def has_y(self):
        return any(map(lambda s: s.is_y, self))

    @property
    def has_t(self):
        return any(map(lambda s: s.is_temporal, self))

    @property
    def crs(self):
        return self._crs

    @crs.setter
    def crs(self, value):
        self._crs = value
    
    @property
    def srid(self):
        """ Tries to find the correct integer SRID for the crs.
        """
        crs = self.crs
        if crs is not None:
            srid = crss.parseEPSGCode(crs, 
                (crss.fromURL, crss.fromURN, crss.fromShortCode)
            )
            if srid is None and not crss.is_image_crs(crs):
                raise InvalidSubsettingException(
                    "Could not parse EPSG code from URI '%s'" % crs
                )
            return srid
        return None


    def filter(self, queryset, containment="overlaps"):
        if not len(self):
            return queryset

        qs = queryset

        bbox = [None, None, None, None]
        srid = self.srid

        if srid is None:
            srid = 4326
        max_extent = crss.crs_bounds(srid)
        tolerance = crss.crs_tolerance(srid)

        for subset in self:
            if isinstance(subset, Slice):
                is_slice = True
                value = subset.value
            elif isinstance(subset, Trim):
                is_slice = False
                low = subset.low
                high = subset.high

            if subset.is_temporal:
                if is_slice:
                    qs = qs.filter(
                        begin_time__lte=value,
                        end_time__gte=value
                    )

                else:
                    if high is not None:
                        qs = qs.filter(
                            begin_time__lte=high
                        )
                    if low is not None:
                        qs = qs.filter(
                            end_time__gte=low
                        )
                
                    # check if the temporal bounds must be strictly contained
                    if containment == "contains":
                        if high is not None:
                            qs = qs.filter(
                                end_time__lte=high
                            )
                        if low is not None:
                            qs = qs.filter(
                                begin_time__gte=low
                            )

            else:
                if is_slice:
                    if subset.is_x:
                        line = LineString(
                            (value, max_extent[1]),
                            (value, max_extent[3])
                        )
                    else:
                        line = LineString(
                            (max_extent[0], value),
                            (max_extent[2], value)
                        )
                    line.srid = srid
                    if srid != 4326:
                        line.transform(4326)
                    qs = qs.filter(footprint__intersects=line)

                else:
                    if subset.is_x:
                        bbox[0] = subset.low
                        bbox[2] = subset.high
                    else:
                        bbox[1] = subset.low
                        bbox[3] = subset.high


        if bbox != [None, None, None, None]:
            bbox = map(
                lambda v: v[0] if v[0] is not None else v[1], 
                zip(bbox, max_extent)
            )

            bbox[0] -= tolerance; bbox[1] -= tolerance
            bbox[2] += tolerance; bbox[3] += tolerance

            logger.debug(
                "Applying BBox %s with containment '%s'." % (bbox, containment)
            )

            poly = Polygon.from_bbox(bbox)
            poly.srid = srid

            if srid != 4326:
                poly.transform(4326)
            if containment == "overlaps":
                qs = qs.filter(footprint__intersects=poly)
            elif containment == "contains":
                qs = qs.filter(footprint__within=poly)

        return qs


    def matches(self, eo_object, containment="overlaps"):
        if not len(self):
            return True

        bbox = [None, None, None, None]
        srid = self.srid
        if srid is None:
            srid = 4326
        max_extent = crss.crs_bounds(srid)
        tolerance = crss.crs_tolerance(srid)

        footprint = eo_object.footprint
        begin_time = eo_object.begin_time
        end_time = eo_object.end_time

        for subset in self:
            if isinstance(subset, Slice):
                is_slice = True
                value = subset.value
            elif isinstance(subset, Trim):
                is_slice = False
                low = subset.low
                high = subset.high

            if subset.is_temporal:
                if is_slice:
                    if begin_time > value or end_time < value:
                        return False
                elif low is None and high is not None:
                    if begin_time > high:
                        return False
                elif low is not None and high is None:
                    if end_time < low:
                        return False
                else:
                    if begin_time > high or end_time < low:
                        return False

            else:
                if is_slice:
                    if subset.is_x:
                        line = Line(
                            (value, max_extent[1]),
                            (value, max_extent[3])
                        )
                    else:
                        line = Line(
                            (max_extent[0], value),
                            (max_extent[2], value)
                        )
                    line.srid = srid
                    if srid != 4326:
                        line.transform(4326)

                    if not line.intersects(footprint):
                        return False
                    
                else:
                    if subset.is_x:
                        bbox[0] = subset.low
                        bbox[2] = subset.high
                    else:
                        bbox[1] = subset.low
                        bbox[3] = subset.high


        if bbox != [None, None, None, None]:
            bbox = map(
                lambda v: v[0] if v[0] is not None else v[1],
                zip(bbox, max_extent)
            )

            bbox[0] -= tolerance; bbox[1] -= tolerance
            bbox[2] += tolerance; bbox[3] += tolerance

            logger.debug(
                "Applying BBox %s with containment '%s'." % (bbox, containment)
            )

            poly = Polygon.from_bbox(bbox)
            poly.srid = srid

            if srid != 4326:
                poly.transform(4326)
            if containment == "overlaps":
                if not footprint.intersects(poly):
                    return False
            elif containment == "contains":
                if not footprint.within(poly):
                    return False
        return True


    def _check_subset(self, subset):
        if not isinstance(subset, Subset):
            raise ValueError("Supplied argument is not a subset.")

        if not isinstance(subset, self.allowed_types):
            raise InvalidSubsettingException(
                "Supplied subset is not allowed."
            )

        if self.has_x and subset.is_x:
            raise InvalidSubsettingException(
                "Multiple subsets for X-axis given."
            )

        if self.has_y and subset.is_y:
            raise InvalidSubsettingException(
                "Multiple subsets for Y-axis given."
            )

        if self.has_t and subset.is_temporal:
            raise InvalidSubsettingException(
                "Multiple subsets for time-axis given."
            )


    @property
    def xy_bbox(self):
        """ Returns the minimum bounding box for all X and Y subsets.
        """
        bbox = [None, None, None, None]
        for subset in self:
            if subset.is_x:
                if isinstance(subset, Trim):
                    bbox[0] = subset.low
                    bbox[2] = subset.high
                else:
                    bbox[0] = bbox[2] = subset.value
            elif subset.is_y:
                if isinstance(subset, Trim):
                    bbox[1] = subset.low
                    bbox[3] = subset.high
                else:
                    bbox[1] = bbox[3] = subset.value

        return bbox


    def bounding_polygon(self, coverage):
        srid = coverage.srid
        extent = coverage.extent
        size_x, size_y = coverage.size
        footprint = coverage.footprint

        subset_srid = self.srid

        if subset_srid is None:
            bbox = list(extent)
        else:
            bbox = list(footprint.extent)

        for subset in self:
            if not isinstance(subset, Trim) or subset.is_temporal:
                continue

            if subset_srid is None:
                # transform coordinates from imageCRS to coverages CRS
                if subset.is_x:
                    if subset.low is not None:
                        l = max(float(subset.low) / float(size_x), 0.0)
                        bbox[0] = extent[0] + l * (extent[2] - extent[0])

                    if subset.high is not None:
                        l = max(float(subset.high) / float(size_x), 0.0)
                        bbox[2] = extent[0] + l * (extent[2] - extent[0])

                elif subset.is_y:
                    if subset.low is not None:
                        l = max(float(subset.low) / float(size_y), 0.0)
                        bbox[1] = extent[3] - l * (extent[3] - extent[1])

                    if subset.high is not None:
                        l = max(float(subset.high) / float(size_y), 0.0)
                        bbox[3] = extent[3] - l * (extent[3] - extent[1])

            else:
                if subset.is_x:
                    if subset.low is not None:
                        bbox[0] = max(subset.low, bbox[0])

                    if subset.high is not None:
                        bbox[2] = min(subset.high, bbox[2])

                if subset.is_y:
                    if subset.low is not None:
                        bbox[1] = max(subset.low, bbox[1])

                    if subset.high is not None:
                        bbox[3] = min(subset.high, bbox[3])

        if subset_srid is None:
            poly = Polygon.from_bbox(bbox)
            poly.srid = srid

        else:
            poly = Polygon.from_bbox(bbox)
            poly.srid = subset_srid

        return poly


class Subset(object):
    def __init__(self, axis):
        axis = axis.lower()
        if axis not in all_axes:
            raise InvalidAxisLabelException(axis)
        self.axis = axis

    @property
    def is_temporal(self):
        return self.axis in temporal_axes

    @property
    def is_x(self):
        return self.axis in x_axes

    @property
    def is_y(self):
        return self.axis in y_axes


class Slice(Subset):
    def __init__(self, axis, value):
        super(Slice, self).__init__(axis)
        self.value = value

    def __repr__(self):
        return "Slice: %s[%s]" % (self.axis, self.value)


class Trim(Subset):
    def __init__(self, axis, low=None, high=None):
        super(Trim, self).__init__(axis)

        if low is not None and high is not None and low > high:
            raise InvalidSubsettingException(
                "Invalid bounds: lower bound greater than upper bound."
            )

        self.low = low
        self.high = high

    def __repr__(self):
        return "Trim: %s[%s:%s]" % (
            self.axis, self.low, self.high
        )


temporal_axes = ("t", "time", "phenomenontime")
x_axes = ("x", "lon", "long")
y_axes = ("y", "lat")
z_axes = ("z", "height")
all_axes = temporal_axes + x_axes + y_axes + z_axes


def is_temporal(axis):
    """ Returns whether or not an axis is a temporal one.
    """
    return (axis.lower() in temporal_axes)
