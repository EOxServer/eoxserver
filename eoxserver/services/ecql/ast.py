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
# ------------------------------------------------------------------------------

"""
"""


class Node(object):
    """ The base class for all other nodes to display the AST of ECQL.
    """
    inline = False

    def get_sub_nodes(self):
        """ Interface method. Get a list of sub-node of this node. """
        raise NotImplementedError

    def get_template(self):
        """ Interface method. Get a template string (using the ``%`` operator)
            to represent the current node and sub-nodes. The template string
            must provide a template replacement for each sub-node reported by
            :method:`get_sub_nodes`.
        """
        raise NotImplementedError


class ConditionNode(Node):
    """ The base class for all nodes representing a condition
    """
    pass


class NotConditionNode(ConditionNode):
    """ Node class to represent a negation condition.
    """
    def __init__(self, sub_node):
        self.sub_node = sub_node

    def get_sub_nodes(self):
        return [self.sub_node]

    def get_template(self):
        return "NOT %s"


class CombinationConditionNode(ConditionNode):
    """ Node class to represent a condition to combine two other conditions
        using either AND or OR.
    """
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class PredicateNode(Node):
    """ The base class for all nodes representing a predicate
    """
    pass


class ComparisonPredicateNode(PredicateNode):
    """ Node class to represent a comparison predicate: to compare two
        expressions using a comparison operation.
    """
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class BetweenPredicateNode(PredicateNode):
    """ Node class to represent a BETWEEN predicate: to check whether an
        expression value within a range.
    """
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
    """ Node class to represent a wildcard sting matching predicate.
    """
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
    """ Node class to represent list checking predicate.
    """
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
    """ Node class to represent null check predicate.
    """
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
    """ Node class to represent temporal predicate.
    """
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


class SpatialPredicateNode(PredicateNode):
    """ Node class to represent spatial relation predicate.
    """
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
    """ Node class to represent a bounding box predicate.
    """
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
    """ The base class for all nodes representing expressions
    """
    pass


class AttributeExpression(ExpressionNode):
    """ Node class to represent attribute lookup expressions
    """
    inline = True

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "ATTRIBUTE %s" % self.name


class LiteralExpression(ExpressionNode):
    """ Node class to represent literal value expressions
    """
    inline = True

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "LITERAL %r" % self.value


class ArithmeticExpressionNode(ExpressionNode):
    """ Node class to represent arithmetic operation expressions with two
        sub-expressions and an operator.
    """
    def __init__(self, lhs, rhs, op):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def get_sub_nodes(self):
        return [self.lhs, self.rhs]

    def get_template(self):
        return "%%s %s %%s" % self.op


def indent(text, amount, ch=' '):
    """ Helper function to indent a string with a certain number of fill
        characters.
    """
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
