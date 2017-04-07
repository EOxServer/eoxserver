from operator import and_, or_, add, sub, mul, div
from datetime import datetime, timedelta

from django.db.models import Q, F, expressions, ForeignKey
try:
    from django.db.models import Value
    ARITHMETIC_TYPES = (F, Value, expressions.ExpressionNode, int, float)
except ImportError:
    def Value(v):
        return v
    ARITHMETIC_TYPES = (F, expressions.ExpressionNode, int, float)

from django.contrib.gis.geos import Polygon
from django.contrib.gis.measure import D

from eoxserver.resources.coverages import models

# ------------------------------------------------------------------------------
# Filters
# ------------------------------------------------------------------------------


def combine(sub_filters, combinator="AND"):
    """ Combine two filters using a logical combinator

        :param sub_filters: the filters to combine
        :param combinator: a string: "AND" / "OR"
        :type sub_filters: ``list`` of :class:`django.db.models.Q` objects
        :return: the combined filter
        :rtype: :class:`django.db.models.Q`
    """
    assert len(sub_filters) >= 2
    for sub_filter in sub_filters:
        assert isinstance(sub_filter, Q)

    assert combinator in ("AND", "OR")
    op = and_ if combinator == "AND" else or_
    return reduce(lambda acc, q: op(acc, q) if acc else q, sub_filters)


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
            if isinstance(rhs, basestring):
                rhs = mapping_choices[field_name][rhs]
            elif hasattr(rhs, 'value'):
                rhs = Value(mapping_choices[field_name][rhs.value])

        except KeyError, e:
            raise AssertionError("Invalid field value %s" % e)

    if comp:
        return Q(**{"%s__%s" % (lhs.name, comp): rhs})
    return ~Q(**{field_name: rhs})


def between(lhs, low, high, not_=False):
    assert isinstance(lhs, F)
    # assert isinstance(low, BaseExpression)
    # assert isinstance(high, BaseExpression)  # TODO

    q = Q(**{"%s__range" % lhs.name: (low, high)})
    return ~q if not_ else q


def like(lhs, rhs, case=False, not_=False, mapping_choices=None):
    assert isinstance(lhs, F)

    if isinstance(rhs, basestring):
        pattern = rhs
    elif hasattr(rhs, 'value'):
        pattern = rhs.value
    else:
        raise AssertionError('Invalid pattern specified')

    if mapping_choices and lhs.name in mapping_choices:
        # special case when choices are given for the field:
        # compare statically and use 'in' operator to check if contained
        cmp_av = [
            (a, a if case else a.lower())
            for a in mapping_choices[lhs.name].keys()
        ]
        cmp_p = pattern if case else pattern.lower()
        if pattern.startswith("%") and pattern.endswith("%"):
            available = [a[0] for a in cmp_av if cmp_p[1:-1] in a[1]]
        elif pattern.startswith("%"):
            available = [a[0] for a in cmp_av if a[1].endswith(cmp_p[1:])]
        elif pattern.endswith("%"):
            available = [a[0] for a in cmp_av if a[1].startswith(cmp_p[:-1])]
        else:
            available = [a[0] for a in cmp_av if a[1] == cmp_p]

        q = Q(**{
            "%s__in" % lhs.name: [
                mapping_choices[lhs.name][a]
                for a in available
            ]
        })
    else:
        i = "" if case else "i"

        if pattern.startswith("%") and pattern.endswith("%"):
            q = Q(**{
                "%s__%s" % (lhs.name, "%scontains" % i): pattern[1:-1]
            })
        elif pattern.startswith("%"):
            q = Q(**{
                "%s__%s" % (lhs.name, "%sendswith" % i): pattern[1:]
            })
        elif pattern.endswith("%"):
            q = Q(**{
                "%s__%s" % (lhs.name, "%sstartswith" % i): pattern[:-1]
            })
        else:
            q = Q(**{
                "%s__%s" % (lhs.name, "%sexact" % i): pattern
            })
    return ~q if not_ else q


def contains(lhs, items, not_=False, mapping_choices=None):
    assert isinstance(lhs, F)
    # for item in items:
    #     assert isinstance(item, BaseExpression)

    if mapping_choices and lhs.name in mapping_choices:
        def map_value(item):
            try:
                if isinstance(item, basestring):
                    item = mapping_choices[lhs.name][item]
                elif hasattr(item, 'value'):
                    item = Value(mapping_choices[lhs.name][item.value])

            except KeyError, e:
                raise AssertionError("Invalid field value %s" % e)
            return item

        items = map(map_value, items)

    q = Q(**{"%s__in" % lhs.name: items})
    return ~q if not_ else q


def null(lhs, not_=False):
    assert isinstance(lhs, F)
    return Q(**{"%s__isnull" % lhs.name: not not_})


def temporal(lhs, time_or_period, op):
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


UNITS_LOOKUP = {
    "kilometers": "km",
    "meters": "m"
}


def spatial(lhs, rhs, op, pattern=None, distance=None, units=None):
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
            return Q(**{"%s__dwithin" % lhs.name: (rhs, d)})
        return Q(**{"%s__distance_gt" % lhs.name: (rhs, d)})

    print op


def bbox(lhs, minx, miny, maxx, maxy, crs=None):
    assert isinstance(lhs, F)
    bbox = Polygon.from_bbox((minx, miny, maxx, maxy))
    # TODO: CRS?

    return Q(**{"%s__bboverlaps" % lhs.name: bbox})


# ------------------------------------------------------------------------------
# Expressions
# ------------------------------------------------------------------------------


def attribute(name, field_mapping):
    field = field_mapping[name]
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
    assert isinstance(lhs, ARITHMETIC_TYPES)
    assert isinstance(rhs, ARITHMETIC_TYPES)
    assert op in OP_TO_FUNC
    func = OP_TO_FUNC[op]
    return func(lhs, rhs)


# helpers
def to_camel_case(word):
    string = ''.join(x.capitalize() or '_' for x in word.split('_'))
    return string[0].lower() + string[1:]


def get_field_mapping_for_model(ModelClass):
    mapping = {}
    mapping_choices = {}

    def is_common_value(field):
        try:
            if isinstance(field, ForeignKey):
                field.related.parent_model._meta.get_field('value')
                return True
        except:
            pass
        return False

    if issubclass(ModelClass, models.EOMetadata):
        field_names = ('identifier', 'begin_time', 'end_time', 'footprint')
        for field_name in field_names:
            mapping[to_camel_case(field_name)] = field_name

    if issubclass(ModelClass, models.Coverage):
        metadata_classes = (
            (models.CoverageMetadata, 'metadata'),
            (models.SARMetadata, 'metadata__sarmetadata'),
            (models.OPTMetadata, 'metadata__optmetadata'),
            (models.ALTMetadata, 'metadata__altmetadata')
        )
        for (metadata_class, path) in metadata_classes:
            for field in metadata_class._meta.fields:
                # skip fields that are defined in a parent model
                if field.model is not metadata_class:
                    continue
                if is_common_value(field):
                    full_path = '%s__%s__value' % (path, field.name)
                else:
                    full_path = '%s__%s' % (path, field.name)
                mapping[to_camel_case(field.name)] = full_path
                if field.choices:
                    mapping_choices[full_path] = dict(
                        (full, abbrev) for (abbrev, full) in field.choices
                    )

    return mapping, mapping_choices
