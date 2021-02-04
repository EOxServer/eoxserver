#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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
#-------------------------------------------------------------------------------


import operator

from django.db.models import Min, Max
from django.contrib.gis.db.models import Union
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.utils.timezone import is_naive, make_aware, get_current_timezone
from django.utils.dateparse import parse_datetime
from django.utils.six import string_types

from eoxserver.contrib import gdal


def pk_equals(first, second):
    """ Helper function to check if the ``pk`` attributes of two models are
    equal.
    """
    return first.pk == second.pk


def collect_eo_metadata(qs, insert=None, exclude=None, bbox=False):
    """ Helper function to collect EO metadata from all EOObjects in a queryset,
    plus additionals from a list and exclude others from a different list. If
    bbox is ``True`` then the returned polygon will only be a minimal bounding
    box of the collected footprints.

    :param qs: the :class:`django.db.QuerySet` to collect all EO metadata from
    :param insert: an iterable of all objects that are to be inserted (thus not
                   entailed in the queryset) and should be considered when
                   collection metadata
    :param exclude: an iterable of objects that are considered to be excluded
                    from the list and should not be used for metadata collection
    :param bbox: if this is set to ``True`` the footprint will only be
                 represented as a minimal BBOX polygon of all collected
                 footprints. This is preferable for large collections.
    """

    values = qs.exclude(
        pk__in=[eo_object.pk for eo_object in exclude or ()]
    ).aggregate(
        begin_time=Min("begin_time"), end_time=Max("end_time"),
        footprint=Union("footprint")
    )

    begin_time, end_time, footprint = (
        values["begin_time"], values["end_time"], values["footprint"]
    )

    # workaround for Django 1.4 bug: aggregate times are strings
    if isinstance(begin_time, string_types):
        begin_time = parse_datetime(begin_time)

    if isinstance(end_time, string_types):
        end_time = parse_datetime(end_time)

    if begin_time and is_naive(begin_time):
        begin_time = make_aware(begin_time, get_current_timezone())
    if end_time and is_naive(end_time):
        end_time = make_aware(end_time, get_current_timezone())

    for eo_object in insert or ():
        if begin_time is None:
            begin_time = eo_object.begin_time
        elif eo_object.begin_time is not None:
            begin_time = min(begin_time, eo_object.begin_time)

        if end_time is None:
            end_time = eo_object.end_time
        elif eo_object.end_time is not None:
            end_time = max(end_time, eo_object.end_time)

        if footprint is None:
            footprint = eo_object.footprint
        elif eo_object.footprint is not None:
            footprint = footprint.union(eo_object.footprint)

    if not isinstance(footprint, MultiPolygon) and footprint is not None:
        footprint = MultiPolygon(footprint)

    if bbox and footprint is not None:
        footprint = MultiPolygon(Polygon.from_bbox(footprint.extent))

    return begin_time, end_time, footprint


def is_same_grid(coverages, epsilon=1e-10):
    """ Function to determine if the given coverages share the same base grid.
    Returns a boolean value, whether or not the coverages share a common grid.

    :param coverages: an iterable of :class:`Coverages
                      <eoxserver.resources.coverages.models.Coverage>`
    :param epsilon: the maximum difference each grid can have to be still
                    considered equal
    """

    if len(coverages) < 2:
        raise ValueError("Not enough coverages given.")

    first = coverages[0]
    first_ext = first.extent
    first_res = first.resolution
    first_srid = first.srid
    first_proj = first.projection

    e = epsilon

    for other in coverages[1:]:
        other_ext = other.extent
        other_res = other.resolution

        # check projection/srid
        if first_srid != other.srid or first_proj != other.projection:
            return False

        # check dimensions
        if len(first_res) != len(other_res):
            return False

        # check offset vectors
        for a, b in zip(first_res, other_res):
            if abs(a - b) > epsilon:
                return False

        # check base grids
        diff_origins = tuple(map(operator.sub, first_ext[:2], other_ext[:2]))

        v = tuple(map(operator.div, diff_origins, other_res))

        if (abs(v[0] - round(v[0])) > e or abs(v[1] - round(v[1])) > e):
            return False

    return True


def parse_raw_value(raw_value, dt):
    """ Parse a raw value from a string according to a given data type.

    :param raw_value: the raw string value
    :param dt: the data type enumeration
    :returns: the parsed value
    """
    if raw_value is None or raw_value == "":  # allow null and empty values
        return None

    is_float = False
    is_complex = False

    if dt in gdal.GDT_INTEGRAL_TYPES:
        value = int(raw_value)

    elif dt in gdal.GDT_FLOAT_TYPES:
        value = float(raw_value)
        is_float = True

    elif dt in gdal.GDT_INTEGRAL_COMPLEX_TYPES:
        value = complex(raw_value)
        is_complex = True

    elif dt in gdal.GDT_FLOAT_COMPLEX_TYPES:
        value = complex(raw_value)
        is_complex = True
        is_float = True

    else:
        value = None

    # range check makes sense for integral values only
    if not is_float:
        limits = gdal.GDT_NUMERIC_LIMITS.get(dt)

        if limits and value is not None:
            def within(v, low, high):
                return (v >= low and v <= high)

            error = ValueError(
                "Stored value is out of the limits for the data type"
            )
            if not is_complex and not within(value, *limits):
                raise error
            elif is_complex:
                if (not within(value.real, limits[0].real, limits[1].real)
                    or not within(value.real, limits[0].real, limits[1].real)):
                    raise error

    return value
