from eoxserver.services import filters


class Node(object):
    inline = False


class ConditionNode(Node):
    pass


class NotConditionNode(ConditionNode):
    def __init__(self, sub_node):
        self.sub_node = sub_node

    def get_sub_nodes(self):
        return [self.sub_node]

    def get_template(self):
        return "NOT %s"


class CombinationConditionNode(ConditionNode):
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class PredicateNode(Node):
    pass


class ComparisonPredicateNode(PredicateNode):
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class BetweenPredicateNode(PredicateNode):
    def __init__(self, lhs, low, high, not_):
        self.lhs = lhs
        self.low = low
        self.high = high
        self.not_ = not_

    def get_sub_nodes(self):
        return [self.lhs, self.low, self.high]

    def get_template(self):
        return "%%s %sBETWEEN %%s AND %%s" % ("NOT " if self.not_ else "")


class LikePredicateNode(PredicateNode):
    def __init__(self, lhs, rhs, case, not_):
        self.lhs = lhs
        self.rhs = rhs
        self.case = case
        self.not_ = not_

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s%sLIKE %%s" % (
            "NOT " if self.not_ else "",
            "I" if self.case else ""
        )


class InPredicateNode(PredicateNode):
    def __init__(self, lhs, sub_nodes, not_):
        self.lhs = lhs
        self.sub_nodes = sub_nodes
        self.not_ = not_

    def get_sub_nodes(self):
        return [self.lhs] + list(self.sub_nodes)

    def get_template(self):
        return "%%s %sIN (%s)" % (
            "NOT " if self.not_ else "",
            ", ".join(["%s"] * len(self.sub_nodes))
        )


class NullPredicateNode(PredicateNode):
    def __init__(self, lhs, not_):
        self.lhs = lhs
        self.not_ = not_

    def get_sub_nodes(self):
        return [self.lhs]

    def get_template(self):
        return "%%s IS %sNULL" % ("NOT " if self.not_ else "")


# class ExistsPredicateNode(PredicateNode):
#     pass


class TemporalPredicateNode(PredicateNode):
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class SpatialPredicateNode(PredicateNode):
    def __init__(self, lhs, rhs, op, pattern=None, distance=None, units=None):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op
        self.pattern = pattern
        self.distance = distance
        self.units = units

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        if self.pattern:
            return "%s(%%s, %%s, %r)" % (self.op, self.pattern)
        elif self.distance or self.units:
            return "%s(%%s, %%s, %r, %r)" % (self.op, self.distance, self.units)
        else:
            return "%s(%%s, %%s)" % (self.op)


class BBoxPredicateNode(PredicateNode):
    def __init__(self, lhs, minx, miny, maxx, maxy, crs):
        self.lhs = lhs
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.crs = crs

    def get_sub_nodes(self):
        return [self.lhs]

    def get_template(self):
        return "BBOX(%%s, %r, %r, %r, %r, %r)" % (
            self.minx, self.miny, self.maxx, self.maxy, self.crs
        )


class ExpressionNode(Node):
    pass


class AttributeExpression(ExpressionNode):
    inline = True

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "ATTRIBUTE %s" % self.name


class LiteralExpression(ExpressionNode):
    inline = True

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "LITERAL %r" % self.value


class ArithmeticExpressionNode(ExpressionNode):
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


def indent(text, amount, ch=' '):
    padding = amount * ch
    return ''.join(padding+line for line in text.splitlines(True))


def get_repr(node, indent_amount=0, indent_incr=4):
    """ Get a debug representation of the given AST node. :param:`indent_amount`
        and :param:`indent_incr` are for the recursive call and don't need to be
        passed.
    """
    sub_nodes = node.get_sub_nodes()
    template = node.get_template()

    args = []
    for sub_node in sub_nodes:
        if isinstance(sub_node, Node) and not sub_node.inline:
            args.append("(\n%s\n)" %
                indent(
                    get_repr(sub_node, indent_amount + indent_incr, indent_incr),
                    indent_amount + indent_incr
                )
            )
        else:
            args.append(repr(sub_node))

    return template % tuple(args)


class FilterEvaluator(object):
    def __init__(self, field_mapping=None, mapping_choices=None):
        self.field_mapping = field_mapping
        self.mapping_choices = mapping_choices

    def to_filter(self, node):
        to_filter = self.to_filter
        if isinstance(node, NotConditionNode):
            return filters.negate(to_filter(node.sub_node))
        elif isinstance(node, CombinationConditionNode):
            return filters.combine(
                to_filter(node.lhs), to_filter(node.rhs), node.op
            )
        elif isinstance(node, ComparisonPredicateNode):
            return filters.compare(
                to_filter(node.lhs), to_filter(node.rhs), node.op,
                self.mapping_choices
            )
        elif isinstance(node, BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs), to_filter(node.low), to_filter(node.high),
                node.not_
            )
        elif isinstance(node, BetweenPredicateNode):
            return filters.between(
                to_filter(node.lhs), to_filter(node.low), to_filter(node.high),
                node.not_
            )
        elif isinstance(node, LikePredicateNode):
            return filters.like(
                to_filter(node.lhs), to_filter(node.rhs), node.case, node.not_,
                self.mapping_choices

            )
        elif isinstance(node, InPredicateNode):
            return filters.contains(
                to_filter(node.lhs), [
                    to_filter(sub_node) for sub_node in node.sub_nodes
                ], node.not_, self.mapping_choices
            )
        elif isinstance(node, NullPredicateNode):
            return filters.null(
                to_filter(node.lhs), node.not_
            )
        elif isinstance(node, TemporalPredicateNode):
            return filters.temporal(
                to_filter(node.lhs), node.rhs, node.op
            )
        elif isinstance(node, SpatialPredicateNode):
            return filters.spatial(
                to_filter(node.lhs), to_filter(node.rhs), node.op,
                to_filter(node.pattern),
                to_filter(node.distance),
                to_filter(node.units)
            )
        elif isinstance(node, BBoxPredicateNode):
            return filters.bbox(
                to_filter(node.lhs),
                to_filter(node.minx),
                to_filter(node.miny),
                to_filter(node.maxx),
                to_filter(node.maxy),
                to_filter(node.crs)
            )
        elif isinstance(node, AttributeExpression):
            return filters.attribute(node.name, self.field_mapping)

        elif isinstance(node, LiteralExpression):
            return node.value

        elif isinstance(node, ArithmeticExpressionNode):
            return filters.arithmetic(
                to_filter(node.lhs), to_filter(node.rhs), node.op
            )

        return node


def to_filter(ast, field_mapping=None, mapping_choices=None):
    return FilterEvaluator(field_mapping, mapping_choices).to_filter(ast)
