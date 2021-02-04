#-------------------------------------------------------------------------------
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
import operator

from django.contrib.gis.geos import Polygon, LineString

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, enum
from eoxserver.contrib.osr import SpatialReference
from eoxserver.resources.coverages import crss
from eoxserver.services.exceptions import (
    InvalidAxisLabelException, InvalidSubsettingException,
    InvalidSubsettingCrsException
)


__all__ = ["Subsets", "Trim", "Slice"]

logger = logging.getLogger(__name__)


class Subsets(list):
    """ Convenience class to handle a variety of spatial and/or temporal
        subsets.

        :param iterable: an iterable of objects inheriting from :class:`Trim`
                         or :class:`Slice`
        :param crs: the CRS definition
        :param allowed_types: the allowed subset types. defaults to both
                              :class:`Trim` and :class:`Slice`
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
        """ See :meth:`list.extend` """
        for subset in iterable:
            self._check_subset(subset)
            super(Subsets, self).append(subset)

    def append(self, subset):
        """ See :meth:`list.append` """
        self._check_subset(subset)
        super(Subsets, self).append(subset)

    def insert(self, i, subset):
        """ See :meth:`list.insert` """
        self._check_subset(subset)
        super(Subsets, self).insert(i, subset)

    # Subset related stuff

    @property
    def has_x(self):
        """ Check if a subset along the X-axis is given. """
        return any(map(lambda s: s.is_x, self))

    @property
    def has_y(self):
        """ Check if a subset along the Y-axis is given. """
        return any(map(lambda s: s.is_y, self))

    @property
    def has_t(self):
        """ Check if a subset along the temporal axis is given. """
        return any(map(lambda s: s.is_temporal, self))

    @property
    def crs(self):
        """ Return the subset CRS definiton. """
        return self._crs

    @crs.setter
    def crs(self, value):
        """ Set the subset CRS definiton. """
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
                raise InvalidSubsettingCrsException(
                    "Could not parse EPSG code from URI '%s'" % crs
                )
            return srid
        return None

    def get_filters(self, containment="overlaps"):
        """ Filter a :class:`Django QuerySet <django.db.models.query.QuerySet>`
        of objects inheriting from :class:`EOObject
        <eoxserver.resources.coverages.models.EOObject>`.

        :param queryset: the ``QuerySet`` to filter
        :param containment: either "overlaps" or "contains"
        :returns: a ``dict`` with the filters
        """
        filters = {}
        if not len(self):
            return filters

        bbox = [None, None, None, None]
        srid = self.srid

        if srid is None:
            srid = 4326
        max_extent = crss.crs_bounds(srid)
        tolerance = crss.crs_tolerance(srid)

        # check if time intervals are configured as "open" or "closed"
        config = get_eoxserver_config()
        reader = SubsetConfigReader(config)
        if reader.time_interval_interpretation == "closed":
            gt_op = "__gte"
            lt_op = "__lte"
        else:
            gt_op = "__gt"
            lt_op = "__lt"

        for subset in self:
            if isinstance(subset, Slice):
                is_slice = True
                value = subset.value
            elif isinstance(subset, Trim):
                is_slice = False
                low = subset.low
                high = subset.high
                # we need the value in case low == high
                value = low

            if subset.is_temporal:
                if is_slice or (high == low and containment == "overlaps"):
                    filters['begin_time__lte'] = value
                    filters['end_time__gte'] = value

                elif high == low:
                    filters['begin_time__gte'] = value
                    filters['end_time__lte'] = value

                else:
                    # check if the temporal bounds must be strictly contained
                    if containment == "contains":
                        if high is not None:
                            filters['end_time' + lt_op] = high
                        if low is not None:
                            filters['begin_time' + gt_op] = low
                    # or just overlapping
                    else:
                        if high is not None:
                            filters['begin_time' + lt_op] = high
                        if low is not None:
                            filters['end_time' + gt_op] = low

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
                    filters['footprint__intersects'] = line

                else:
                    if subset.is_x:
                        bbox[0] = subset.low
                        bbox[2] = subset.high
                    else:
                        bbox[1] = subset.low
                        bbox[3] = subset.high

        if bbox != [None, None, None, None]:
            bbox = list(map(
                lambda v: v[0] if v[0] is not None else v[1],
                zip(bbox, max_extent)
            ))

            bbox[0] -= tolerance
            bbox[1] -= tolerance
            bbox[2] += tolerance
            bbox[3] += tolerance

            logger.debug(
                "Applying BBox %s with containment '%s'." % (bbox, containment)
            )

            poly = Polygon.from_bbox(bbox)
            poly.srid = srid

            if srid != 4326:
                poly.transform(4326)
            if containment == "overlaps":
                filters['footprint__intersects'] = poly
            elif containment == "contains":
                filters['footprint__within'] = poly

        return filters

    def filter(self, queryset, containment="overlaps"):
        """ Filter a :class:`Django QuerySet <django.db.models.query.QuerySet>`
        of objects inheriting from :class:`EOObject
        <eoxserver.resources.coverages.models.EOObject>`.

        :param queryset: the ``QuerySet`` to filter
        :param containment: either "overlaps" or "contains"
        :returns: a ``QuerySet`` with additional filters applied
        """

        if not len(self):
            return queryset

        filters = self.get_filters(containment)
        return queryset.filter(**filters)

    def matches(self, eo_object, containment="overlaps"):
        """ Check if the given :class:`EOObject
        <eoxserver.resources.coverages.models.EOObject>` matches the given
        subsets.

        :param eo_object: the ``EOObject`` to match
        :param containment: either "overlaps" or "contains"
        :returns: a boolean value indicating if the object is contained in the
                  given subsets
        """
        if not len(self):
            return True

        bbox = [None, None, None, None]
        srid = self.srid
        if srid is None:
            srid = 4326
        max_extent = crss.crs_bounds(srid)
        tolerance = crss.crs_tolerance(srid)

        # check if time intervals are configured as "open" or "closed"
        config = get_eoxserver_config()
        reader = SubsetConfigReader(config)
        # note that the operator is inverted from filter() above as the
        # filters use an inclusive search whereas here it's exclusive
        if reader.time_interval_interpretation == "closed":
            gt_op = operator.gt
            lt_op = operator.lt
        else:
            gt_op = operator.ge
            lt_op = operator.le

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
                # we need the value in case low == high
                value = low

            if subset.is_temporal:
                if is_slice or (low == high and containment == "overlaps"):
                    if begin_time > value or end_time < value:
                        return False
                elif low == high:
                    if begin_time < value or end_time > value:
                        return False
                else:
                    # check if the temporal bounds must be strictly contained
                    if containment == "contains":
                        if high is not None:
                            if gt_op(end_time, high):
                                return False
                        if low is not None:
                            if lt_op(begin_time, low):
                                return False
                    # or just overlapping
                    else:
                        if high is not None:
                            if gt_op(begin_time, high):
                                return False
                        if low is not None:
                            if lt_op(end_time, low):
                                return False

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

            bbox[0] -= tolerance
            bbox[1] -= tolerance
            bbox[2] += tolerance
            bbox[3] += tolerance

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

        :returns: a list of four elements [minx, miny, maxx, maxy], which might
                  be ``None``
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
        """ Returns a minimum bounding :class:`django.contrib.gis.geos.Polygon`
        for the given :class:`Coverage
        <eoxserver.render.coverages.objects.Coverage>`

        :param coverage: the coverage to calculate the bounding polygon for
        :returns: the calculated ``Polygon``
        """

        srid = SpatialReference(coverage.grid.coordinate_reference_system).srid
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
    """ Base class for all subsets.
    """

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
    """ Slice subsets reduce the dimension of the subsetted object by one and
    slice the given ``axis`` at the specified ``value``.

    :param axis: the axis name
    :param value: the slice point
    """
    def __init__(self, axis, value):
        super(Slice, self).__init__(axis)
        self.value = value

    def __repr__(self):
        return "Slice: %s[%s]" % (self.axis, self.value)


class Trim(Subset):
    """ Trim subsets reduce the domain of the specified ``axis``

    :param axis: the axis name
    :param low: the lower end of the ``Trim``; if omitted, the ``Trim`` has no
                lower bound
    :param high: the upper end of the ``Trim``; if omitted, the ``Trim`` has no
                 upper bound
    """
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


class SubsetConfigReader(config.Reader):
    section = "services.owscommon"
    time_interval_interpretation = config.Option(
        default="closed", type=enum(("closed", "open"), False)
    )
