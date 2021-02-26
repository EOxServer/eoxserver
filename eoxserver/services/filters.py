# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------


try:
    from operator import and_, or_, add, sub, mul, div
except ImportError:
    from operator import and_, or_, add, sub, mul, truediv as div
from datetime import datetime, timedelta

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict
from django.utils.six import string_types

from django.db.models import Q, F, ForeignKey, Value
from django.db.models.expressions import Expression

from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Polygon
from django.contrib.gis.measure import D

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, enum
from eoxserver.resources.coverages import models

ARITHMETIC_TYPES = (Expression, F, Value, int, float)

# ------------------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------------------


def combine(sub_filters, combinator="AND"):
    """ Combine filters using a logical combinator

        :param sub_filters: the filters to combine
        :param combinator: a string: "AND" / "OR"
        :type sub_filters: ``list`` of :class:`django.db.models.Q` objects
        :return: the combined filter
        :rtype: :class:`django.db.models.Q`
    """
    for sub_filter in sub_filters:
        assert isinstance(sub_filter, Q)

    assert combinator in ("AND", "OR")
    op = and_ if combinator == "AND" else or_

    out = None
    for sub_filter in sub_filters:
        if out is None:
            out = sub_filter
        else:
            out = op(out, sub_filter)

    return out


def negate(sub_filter):
    """ Negate a filter, opposing its meaning.

        :param sub_filter: the filter to negate
        :type sub_filter: :class:`django.db.models.Q`
        :return: the negated filter
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(sub_filter, Q)
    return ~sub_filter


OP_TO_COMP = {
    "<": "lt",
    "<=": "lte",
    ">": "gt",
    ">=": "gte",
    "<>": None,
    "=": "exact"
}


def compare(lhs, rhs, op, mapping_choices=None):
    """ Compare a filter with an expression using a comparison operation

        :param lhs: the field to compare
        :param rhs: the filter expression
        :param op: a string denoting the operation. one of ``"<"``, ``"<="``,
                   ``">"``, ``">="``, ``"<>"``, ``"="``
        :param mapping_choices: a dict to lookup potential choices for a
                                certain field.
        :type lhs: :class:`django.db.models.F`
        :type rhs: :class:`django.db.models.F`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    # assert isinstance(rhs, Q)  # TODO!!
    assert op in OP_TO_COMP
    comp = OP_TO_COMP[op]

    field_name = lhs.name

    if mapping_choices and field_name in mapping_choices:
        try:
            if isinstance(rhs, string_types):
                rhs = mapping_choices[field_name][rhs]
            elif hasattr(rhs, 'value'):
                rhs = Value(mapping_choices[field_name][rhs.value])

        except KeyError as e:
            raise AssertionError("Invalid field value %s" % e)

    if comp:
        return Q(**{"%s__%s" % (lhs.name, comp): rhs})
    return ~Q(**{field_name: rhs})


def between(lhs, low, high, not_=False):
    """ Create a filter to match elements that have a value within a certain
        range.

        :param lhs: the field to compare
        :param low: the lower value of the range
        :param high: the upper value of the range
        :param not_: whether the range shall be inclusive (the default) or
                     exclusive
        :type lhs: :class:`django.db.models.F`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    # assert isinstance(low, BaseExpression)
    # assert isinstance(high, BaseExpression)  # TODO

    q = Q(**{"%s__range" % lhs.name: (low, high)})
    return ~q if not_ else q


def like(lhs, rhs, case=False, not_=False, mapping_choices=None):
    """ Create a filter to filter elements according to a string attribute using
        wildcard expressions.

        :param lhs: the field to compare
        :param rhs: the wildcard pattern: a string containing any number of '%'
                    characters as wildcards.
        :param case: whether the lookup shall be done case sensitively or not
        :param not_: whether the range shall be inclusive (the default) or
                     exclusive
        :param mapping_choices: a dict to lookup potential choices for a
                                certain field.
        :type lhs: :class:`django.db.models.F`
        :type rhs: str
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)

    if isinstance(rhs, string_types):
        pattern = rhs
    elif hasattr(rhs, 'value'):
        pattern = rhs.value
    else:
        raise AssertionError('Invalid pattern specified')

    parts = pattern.split("%")
    length = len(parts)

    if mapping_choices and lhs.name in mapping_choices:
        # special case when choices are given for the field:
        # compare statically and use 'in' operator to check if contained
        cmp_av = [
            (a, a if case else a.lower())
            for a in mapping_choices[lhs.name].keys()
        ]

        for idx, part in enumerate(parts):
            if not part:
                continue

            cmp_p = part if case else part.lower()

            if idx == 0 and length > 1:  # startswith
                cmp_av = [a for a in cmp_av if a[1].startswith(cmp_p)]
            elif idx == 0:  # exact matching
                cmp_av = [a for a in cmp_av if a[1] == cmp_p]
            elif idx == length - 1:   # endswith
                cmp_av = [a for a in cmp_av if a[1].endswith(cmp_p)]
            else:  # middle
                cmp_av = [a for a in cmp_av if cmp_p in a[1]]

        q = Q(**{
            "%s__in" % lhs.name: [
                mapping_choices[lhs.name][a[0]]
                for a in cmp_av
            ]
        })

    else:
        i = "" if case else "i"
        q = None

        for idx, part in enumerate(parts):
            if not part:
                continue

            if idx == 0 and length > 1:  # startswith
                new_q = Q(**{
                    "%s__%s" % (lhs.name, "%sstartswith" % i): part
                })
            elif idx == 0:  # exact matching
                new_q = Q(**{
                    "%s__%s" % (lhs.name, "%sexact" % i): part
                })
            elif idx == length - 1:   # endswith
                new_q = Q(**{
                    "%s__%s" % (lhs.name, "%sendswith" % i): part
                })
            else:  # middle
                new_q = Q(**{
                    "%s__%s" % (lhs.name, "%scontains" % i): part
                })

            q = q & new_q if q else new_q

    return ~q if not_ else q


def contains(lhs, items, not_=False, mapping_choices=None):
    """ Create a filter to match elements attribute to be in a list of choices.

        :param lhs: the field to compare
        :param items: a list of choices
        :param not_: whether the range shall be inclusive (the default) or
                     exclusive
        :param mapping_choices: a dict to lookup potential choices for a
                                certain field.
        :type lhs: :class:`django.db.models.F`
        :type items: list
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    # for item in items:
    #     assert isinstance(item, BaseExpression)

    if mapping_choices and lhs.name in mapping_choices:
        def map_value(item):
            try:
                if isinstance(item, string_types):
                    item = mapping_choices[lhs.name][item]
                elif hasattr(item, 'value'):
                    item = Value(mapping_choices[lhs.name][item.value])

            except KeyError as e:
                raise AssertionError("Invalid field value %s" % e)
            return item

        items = map(map_value, items)

    q = Q(**{"%s__in" % lhs.name: items})
    return ~q if not_ else q


def null(lhs, not_=False):
    """ Create a filter to match elements whose attribute is (not) null

        :param lhs: the field to compare
        :param not_: whether the range shall be inclusive (the default) or
                     exclusive
        :type lhs: :class:`django.db.models.F`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    return Q(**{"%s__isnull" % lhs.name: not not_})


def temporal(lhs, time_or_period, op):
    """ Create a temporal filter for the given temporal attribute.

        :param lhs: the field to compare
        :param time_or_period: the time instant or time span to use as a filter
        :param op: the comparison operation. one of "BEFORE", "BEFORE OR
                   DURING", "DURING", "DURING OR AFTER", "AFTER".
        :type lhs: :class:`django.db.models.F`
        :type time_or_period: :class:`datetime.datetime` or a tuple of two
                              datetimes or a tuple of one datetime and one
                              :class:`datetime.timedelta`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    assert op in (
        "BEFORE", "BEFORE OR DURING", "DURING", "DURING OR AFTER", "AFTER"
    )
    low = None
    high = None
    if op in ("BEFORE", "AFTER"):
        assert isinstance(time_or_period, datetime)
        if op == "BEFORE":
            high = time_or_period
        else:
            low = time_or_period
    else:
        low, high = time_or_period
        assert isinstance(low, datetime) or isinstance(high, datetime)

        if isinstance(low, timedelta):
            low = high - low
        if isinstance(high, timedelta):
            high = low + high

    if low and high:
        return Q(**{"%s__range" % lhs.name: (low, high)})
    elif low:
        return Q(**{"%s__gte" % lhs.name: low})
    else:
        return Q(**{"%s__lte" % lhs.name: high})


def time_interval(time_or_period, containment='overlaps',
                  begin_time_field='begin_time', end_time_field='end_time'):
    """
    """
    config = get_eoxserver_config()
    reader = SubsetConfigReader(config)

    if reader.time_interval_interpretation == "closed":
        gt_op = "__gte"
        lt_op = "__lte"
    else:
        gt_op = "__gt"
        lt_op = "__lt"

    is_slice = len(time_or_period) == 1
    if len(time_or_period) == 1:
        is_slice = True
        value = time_or_period[0]
    else:
        is_slice = False
        low, high = time_or_period

    if is_slice or (high == low and containment == "overlaps"):
        return Q(**{
            begin_time_field + "__lte": time_or_period[0],
            end_time_field + "__gte": time_or_period[0]
        })

    elif high == low:
        return Q(**{
            begin_time_field + "__gte": value,
            end_time_field + "__lte": value
        })

    else:
        q = Q()
        # check if the temporal bounds must be strictly contained
        if containment == "contains":
            if high is not None:
                q &= Q(**{
                    end_time_field + lt_op: high
                })
            if low is not None:
                q &= Q(**{
                    begin_time_field + gt_op: low
                })
        # or just overlapping
        else:
            if high is not None:
                q &= Q(**{
                    begin_time_field + lt_op: high
                })
            if low is not None:
                q &= Q(**{
                    end_time_field + gt_op: low
                })
        return q


UNITS_LOOKUP = {
    "kilometers": "km",
    "meters": "m"
}


def spatial(lhs, rhs, op, pattern=None, distance=None, units=None):
    """ Create a spatial filter for the given spatial attribute.

        :param lhs: the field to compare
        :param rhs: the time instant or time span to use as a filter
        :param op: the comparison operation. one of "INTERSECTS", "DISJOINT",
                   "CONTAINS", "WITHIN", "TOUCHES", "CROSSES", "OVERLAPS",
                   "EQUALS", "RELATE", "DWITHIN", "BEYOND"
        :param pattern: the spatial relation pattern
        :param distance: the distance value for distance based lookups:
                         "DWITHIN" and "BEYOND"
        :param units: the units the distance is expressed in
        :type lhs: :class:`django.db.models.F`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    # assert isinstance(rhs, BaseExpression)  # TODO

    assert op in (
        "INTERSECTS", "DISJOINT", "CONTAINS", "WITHIN", "TOUCHES", "CROSSES",
        "OVERLAPS", "EQUALS", "RELATE", "DWITHIN", "BEYOND"
    )
    if op == "RELATE":
        assert pattern
    elif op in ("DWITHIN", "BEYOND"):
        assert distance
        assert units

    if op in (
            "INTERSECTS", "DISJOINT", "CONTAINS", "WITHIN", "TOUCHES",
            "CROSSES", "OVERLAPS", "EQUALS"):
        return Q(**{"%s__%s" % (lhs.name, op.lower()): rhs})
    elif op == "RELATE":
        return Q(**{"%s__relate" % lhs.name: (rhs, pattern)})
    elif op in ("DWITHIN", "BEYOND"):
        # TODO: maybe use D.unit_attname(units)
        d = D(**{UNITS_LOOKUP[units]: distance})
        if op == "DWITHIN":
            return Q(**{"%s__distance_lte" % lhs.name: (rhs, d, 'spheroid')})
        return Q(**{"%s__distance_gte" % lhs.name: (rhs, d, 'spheroid')})


def bbox(lhs, minx, miny, maxx, maxy, crs=None, bboverlaps=True):
    """ Create a bounding box filter for the given spatial attribute.

        :param lhs: the field to compare
        :param minx: the lower x part of the bbox
        :param miny: the lower y part of the bbox
        :param maxx: the upper x part of the bbox
        :param maxy: the upper y part of the bbox
        :param crs: the CRS the bbox is expressed in
        :type lhs: :class:`django.db.models.F`
        :return: a comparison expression object
        :rtype: :class:`django.db.models.Q`
    """
    assert isinstance(lhs, F)
    box = Polygon.from_bbox((minx, miny, maxx, maxy))
    box.srid = SpatialReference(crs).srid

    if bboverlaps:
        return Q(**{"%s__bboverlaps" % lhs.name: box})
    return Q(**{"%s__intersects" % lhs.name: box})


# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

class SubsetConfigReader(config.Reader):
    section = "services.owscommon"
    time_interval_interpretation = config.Option(
        default="closed", type=enum(("closed", "open"), False)
    )

# ------------------------------------------------------------------------------
# Expressions
# ------------------------------------------------------------------------------


def attribute(name, field_mapping=None):
    """ Create an attribute lookup expression using a field mapping dictionary.

        :param name: the field filter name
        :param field_mapping: the dictionary to use as a lookup.
        :rtype: :class:`django.db.models.F`
    """
    if field_mapping:
        field = field_mapping.get(name, name)
    else:
        field = name
    return F(field)


def literal(value):
    return Value(value)


OP_TO_FUNC = {
    "+": add,
    "-": sub,
    "*": mul,
    "/": div
}


def arithmetic(lhs, rhs, op):
    """ Create an arithmetic filter

        :param lhs: left hand side of the arithmetic expression. either a
                    scalar or a field lookup or another type of expression
        :param rhs: same as `lhs`
        :param op: the arithmetic operation. one of "+", "-", "*", "/"
        :rtype: :class:`django.db.models.F`
    """

    assert isinstance(lhs, ARITHMETIC_TYPES), (
        '%r is not a compatible type' % lhs
    )
    assert isinstance(rhs, ARITHMETIC_TYPES), (
        '%r is not a compatible type' % rhs
    )
    assert op in OP_TO_FUNC
    func = OP_TO_FUNC[op]
    return func(lhs, rhs)


def get_field_mapping_for_model(model_class, strict=False):
    """ Utility function to get the metadata mapping for a specific model class.

        :param model_class: The django database model to create the mapping for
        :param strict: Whether only the related metadata attributes shall be
                       included or the basic ones as-well
        :returns: two dictionaries: the mapping dict, mapping from metadata
                  filter name to the database field lookup and a dict to map
                  the field lookup to the potential choices.
    """
    mapping = OrderedDict()
    mapping_choices = {}

    metadata_classes = {
        models.Collection: (models.CollectionMetadata, 'collection'),
        models.Product: (models.ProductMetadata, 'product'),
        models.Coverage: (models.CoverageMetadata, 'coverage'),
    }

    if issubclass(model_class, models.EOObject) and not strict:
        field_names = ('identifier', 'begin_time', 'end_time', 'footprint')
        for field_name in field_names:
            mapping[_to_camel_case(field_name)] = field_name

    if model_class in metadata_classes:
        new_mapping, mapping_choices = _get_metadata_model_mapping(
            *metadata_classes.get(model_class)
        )
        mapping.update(new_mapping)

    elif model_class is models.EOObject:
        for metadata_class, name in metadata_classes.values():
            class_mapping, class_choices = _get_metadata_model_mapping(
                metadata_class, "%s__%s" % (name, name)
            )
            mapping.update(class_mapping)
            mapping_choices.update(class_choices)

    return mapping, mapping_choices


# helpers
def _to_camel_case(word):
    string = ''.join(x.capitalize() or '_' for x in word.split('_'))
    return string[0].lower() + string[1:]


def _is_common_value(field):
    try:
        if isinstance(field, ForeignKey):
            field.related_model._meta.get_field('value')
            return True
    except Exception:
        pass
    return False


def _get_metadata_model_mapping(metadata_class, path_name):
    mapping = OrderedDict()
    mapping_choices = {}
    for field in metadata_class._meta.fields:
        # skip fields that are defined in a parent model
        if field.model is not metadata_class or field.name == "id":
            continue
        if _is_common_value(field):
            full_path = '%s_metadata__%s__value' % (
                path_name, field.name
            )
        else:
            full_path = '%s_metadata__%s' % (path_name, field.name)
        mapping[_to_camel_case(field.name)] = full_path
        if field.choices:
            mapping_choices[full_path] = dict(
                (full, abbrev) for (abbrev, full) in field.choices
            )

    return mapping, mapping_choices
