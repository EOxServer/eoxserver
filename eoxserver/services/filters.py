from operator import and_, or_, add, sub, mul, div
from datetime import datetime, timedelta

from django.db.models import Q, F
try:
    from django.db.models import Value
    ARITHMETIC_TYPES = (F, Value, int, float)
except ImportError:
    def Value(v):
        return v
    ARITHMETIC_TYPES = (F, int, float)

from django.contrib.gis.geos import Polygon
from django.contrib.gis.measure import D

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


def compare(lhs, rhs, op):
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
    if comp:
        return Q(**{"%s__%s" % (lhs.name, comp): rhs})
    return ~Q(**{field_name: rhs})


def between(lhs, low, high, not_=False):
    assert isinstance(lhs, F)
    # assert isinstance(low, BaseExpression)
    # assert isinstance(high, BaseExpression)  # TODO

    q = Q(**{"%s__range" % lhs.name: (low, high)})
    return ~q if not_ else q


def like(lhs, rhs, case=False, not_=False):
    assert isinstance(lhs, F)

    i = "" if case else "i"

    if rhs.startswith("%") and rhs.endswith("%"):
        q = Q(**{
            "%s__%s" % (lhs.name, "%scontains" % i): rhs[1:-1]
        })
    elif rhs.startswith("%"):
        q = Q(**{
            "%s__%s" % (lhs.name, "%sendswith" % i): rhs[1:]
        })
    elif rhs.endswith("%"):
        q = Q(**{
            "%s__%s" % (lhs.name, "%sstartswith" % i): rhs[:-1]
        })
    else:
        q = Q(**{
            "%s__%s" % (lhs.name, "%sexact" % i): rhs
        })
    return ~q if not_ else q


def contains(lhs, items, not_=False):
    assert isinstance(lhs, F)
    # for item in items:
    #     assert isinstance(item, BaseExpression)

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
            return Q(**{"%s__dwithin": d})
        return Q(**{"%s__distance_gt": d})

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
