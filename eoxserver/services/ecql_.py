import lrparsing
from lrparsing import (
    Keyword, List, Opt, Prio, Ref, THIS, Token, Tokens, TokenSymbol,
    LrParsingError, Repeat
)
import traceback
from datetime import datetime
from django.contrib.gis.geos import GEOSGeometry
from eoxserver.core.util.timetools import parse_iso8601, parse_duration

from eoxserver.services import filters

# class ExprParser(lrparsing.Grammar):
#     #
#     # Put Tokens we don't want to re-type in a TokenRegistry.
#     #
#     class T(lrparsing.TokenRegistry):
#         integer = Token(re="[0-9]+")
#         integer["key"] = "I'm a mapping!"
#         ident = Token(re="[A-Za-z_][A-Za-z_0-9]*")
#     #
#     # Grammar rules.
#     #
#     expr = Ref("expr")                # Forward reference
#     call = T.ident + '(' + List(expr, ',') + ')'
#     atom = T.ident | T.integer | Token('(') + expr + ')' | call
#     expr = Prio(                      # If ambiguous choose atom 1st, ...
#         atom,
#         Tokens("+ - ~") >> THIS,      # >> means right associative
#         THIS << Tokens("* / // %") << THIS,
#         THIS << Tokens("+ -") << THIS,  # THIS means "expr" here
#         THIS << (Tokens("== !=") | Keyword("is")) << THIS)
#     expr["a"] = "I am a mapping too!"
#     START = expr                      # Where the grammar must start
#     COMMENTS = (                      # Allow C and Python comments
#         Token(re="#(?:[^\r\n]*(?:\r\n?|\n\r?))") |
#         Token(re="/[*](?:[^*]|[*][^/])*[*]/"))

# parse_tree = ExprParser.parse("1 + /* a */ b + 3 * 4 is c(1, a)")
# print(ExprParser.repr_parse_tree(parse_tree))


def Kwd(iden):
    return Keyword(iden, case=False)


def Toks(t, k=None):
    return Tokens(t, k, case=False)


class ECQLParser(lrparsing.Grammar):
    class T(lrparsing.TokenRegistry):
        not_ = Token('NOT')
        and_ = Token('AND')
        or_ = Token('OR')

        between = Token('BETWEEN')
        like = Token('LIKE')
        ilike = Token('ILIKE')
        in_ = Token('IN')
        is_ = Token('IS')
        null = Token('NULL')
        before = Token('BEFORE')
        after = Token('AFTER')
        during = Token('DURING')

        intersects = Token('INTERSECTS')
        disjoint = Token('DISJOINT')
        contains = Token('CONTAINS')
        within = Token('WITHIN')
        touches = Token('TOUCHES')
        crosses = Token('CROSSES')
        overlaps = Token('OVERLAPS')
        equals = Token('EQUALS')
        relate = Token('RELATE')
        dwithin = Token('DWITHIN')
        beyond = Token('BEYOND')
        bbox = Token('BBOX')

        integer = Token(re='[0-9]+')
        float = Token(re='(?:[0-9]+[.][0-9]*|[.][0-9]+)(?:[Ee][-+]?[0-9]+)?')
        # ident = Token(re="[A-Za-z_][A-Za-z_0-9]*")
        ident = Token(re="[a-z_][A-Za-z_0-9]*")

        # no_quote = Token(re='[^"]+')
        time_string = Token(
            re="\d{4}-\d{2}-\d{2}T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z"
        )
        duration_string = Token(
            re="P(?=[YMDHMS])"  # positive lookahead here
            "((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
        )
        quoted_string = Token(re='\"[^"]*\"')
        geometry_string = Token(re='POINT[^\)]*\)')
        # geometry_string = Token(
        #     re="POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON"
        #        "|ENVELOPE"
        #        "\s("
        #        #"\([^(]*\)|"  # POINT + LINESTRING + ENVELOPE
        #        #"\((\([^(]*\))*\)|"  # POLYGON + MULTIPOINT + MULTILINESTRING
        #        #"\((\((\([^(]*\))*\)*\)"  # MULTIPOLYGON
        #        ")"
        # )

    condition = Ref("condition")
    predicate = Ref("predicate")
    expr = Ref("expr")
    arithmetic_expr = Ref("arithmetic_expr")
    time = Ref("time")
    duration = Ref("duration")
    time_period = Ref("time_period")
    attribute = Ref("attribute")
    literal = Ref("literal")
    numeric_literal = Ref("numeric_literal")
    string_literal = Ref("string_literal")
    geometry_literal = Ref("geometry_literal")
    units = Ref("units")

    condition = Prio(
        THIS << Kwd('AND') << THIS,
        THIS << Kwd('OR') << THIS,
        predicate,
        '(' + THIS + ')',
        Kwd('NOT') + THIS,
    )

    predicate = (
        expr + Toks("= <> < <= > >=") + expr |
        expr << Opt(Kwd("NOT")) + Kwd("BETWEEN") << expr << Kwd("AND") << expr |
        expr << Opt(Kwd("NOT")) + (Kwd("LIKE") | Kwd("ILIKE")) << string_literal |
        expr << Opt(Kwd("NOT")) + Kwd("IN") + "(" + List(expr, ',') + ")" |
        expr << Kwd("IS") + Opt(Kwd("NOT")) + Kwd("NULL") |

        # temporal predicates
        expr + Kwd("BEFORE") + time |
        expr + Kwd("BEFORE") + Kwd("OR") + Kwd("DURING") + time_period |
        expr + Kwd("DURING") + time_period |
        expr + Kwd("DURING") + Kwd("OR") + Kwd("AFTER") + time_period |
        expr + Kwd("AFTER") + time |

        # spatial predicates
        Kwd("INTERSECTS") + "(" + expr + "," + geometry_literal + ")" |
        Kwd("DISJOINT") + "(" + expr + "," + expr + ")" |
        Kwd("CONTAINS") + "(" + expr + "," + expr + ")" |
        Kwd("WITHIN") + "(" + expr + "," + expr + ")" |
        Kwd("TOUCHES") + "(" + expr + "," + expr + ")" |
        Kwd("CROSSES") + "(" + expr + "," + expr + ")" |
        Kwd("OVERLAPS") + "(" + expr + "," + expr + ")" |
        Kwd("EQUALS") + "(" + expr + "," + expr + ")" |
        Kwd("RELATE") + "(" + expr + "," + expr + ")" |
        Kwd("DWITHIN") + "(" + expr + "," + expr + "," + numeric_literal + "," + units + ")" |
        Kwd("BEYOND") + "(" + expr + "," + expr + "," + numeric_literal + "," + units + ")" |
        Kwd("BBOX") + "(" + expr + "," + numeric_literal + "," + numeric_literal + "," + numeric_literal + "," + numeric_literal + "," + string_literal + ")"
    )

    # TODO temporal predicates
    # TODO spatial predicates

    expr = Prio(
        literal,
        attribute,
        arithmetic_expr,
        "(" + THIS + ")"
    )

    arithmetic_expr = Prio(
        expr << Toks("* /") << expr,
        expr << Toks("+ -") << expr
    )

    attribute = Prio(
        # '"' + T.no_quote + '"',
        T.ident
    )
    literal = (
        numeric_literal |
        string_literal |
        geometry_literal
        # Kwd("TRUE") | Kwd("FALSE") |
    )
    numeric_literal = (
        T.integer |
        T.float
    )
    string_literal = T.quoted_string
    # geometry_literal = T.geometry_string

    geom_tuple = Repeat(numeric_literal)
    geometry_literal = (
        # Prio(
        #     Kwd("POINT"),  Kwd("LINESTRING") #| #Kwd("POLYGON") |
        #     #Kwd("POINT") | Kwd("LINESTRING") | #Kwd("POLYGON") |
        #     # Kwd("MULTIPOINT") | Kwd("MULTILINESTRING") |
        #     # Kwd("MULTIPOLYGON") | Kwd("ENVELOPE")
        # ) +
        #(Kwd("POINT") + "(" + Repeat(numeric_literal) + ")")
        T.geometry_string
        # (
        #     #("(" + List(numeric_literal + numeric_literal, ',') + ")")
        #     geom_tuple
        # ) +
        # ")"
    )

    time = T.time_string
    duration = T.duration_string
    time_period = (
        time + "/" + time |
        duration + "/" + time |
        time + "/" + duration

    )

    units = (
        Kwd("feet") | Kwd("meters") | Kwd("statute_miles") |
        Kwd("nautical_miles") | Kwd("kilometers")
    )

    START = condition


class Node(tuple):
    value = None

    def __new__(cls, n):
        return super(Node, cls).__new__(cls, n)

    # def __repr__(self):
    #     return E.repr_parse_tree(self, False)


class ECQLEvaluator(object):
    def __init__(self, field_mapping):
        self.field_mapping = field_mapping

    def __call__(self, node):
        node = Node(node)
        name = node[0].name

        # if not isinstance(node[0], TokenSymbol):
        #     print "here"
        #     node = node[1]
        # else:
        #     print "there"
        #     name = name.split(".")[-1]

        name = name.split(".")[-1]

        if name in self.__class__.__dict__:
            return self.__class__.__dict__[name](self, node)

        return node

    def condition(self, node):
        value = node[1]
        if isinstance(value, filters.Q):
            if len(node) == 4:
                return filters.combine([value, node[3]], node[2][1])
            return value
        elif value[1] == "(":
            return node[2]
        elif value[1] == "NOT":
            return ~node[2]

    def predicate(self, node):
        # print list(node)
        lhs = node[1]
        rhs = node[-1]
        op = node[2][1]
        not_ = False

        if node[2][1] == "NOT":
            not_ = True
            op = node[3][1]

        if op in ("LIKE", "ILIKE"):
            return filters.like(lhs, rhs, op == "LIKE", not_)

        elif op == "IN":
            return filters.contains(lhs, node[4:-1:2], not_)

        elif op == "IS":
            if node[3][1] == "NOT":
                not_ = True
            return filters.null(lhs, not_)

        elif op in ("BEFORE", "AFTER", "DURING"):
            during = not isinstance(rhs, datetime)
            if op == "BEFORE" and during:
                filter_ = "BEFORE OR DURING"
            elif op == "BEFORE":
                filter_ = "BEFORE"
            elif len(node) == 5:
                filter_ = "DURING OR AFTER"
            elif during:
                filter_ = "DURING"
            else:
                filter_ = "AFTER"

            return filters.temporal(lhs, rhs, filter_)

        elif lhs[1] in (
            "INTERSECTS", "DISJOINT", "CONTAINS", "WITHIN", "TOUCHES", "CROSSES",
            "OVERLAPS", "EQUALS", "RELATE", "DWITHIN", "BEYOND"
        ):
            op = node[1][1]
            lhs = node[3]
            rhs = node[5]

            return filters.spatial(lhs, rhs, op)

        return filters.compare(lhs, rhs, op)

    def expr(self, node):
        return node[1]

    def arithmetic_expr(self, node):
        lhs = node[1]
        rhs = node[3]
        op = node[2][1]
        return filters.arithmetic(lhs, rhs, op)

    def attribute(self, node):
        return filters.attribute(node[1][1], self.field_mapping)

    def literal(self, node):
        return node[1]

    def numeric_literal(self, node):
        return filters.literal(float(node[1][1]))

    def string_literal(self, node):
        return filters.literal(node[1][1][1:-1])


    def geometry_string(self, node):
        print (node)


    def geometry_literal(self, node):
        print (node[1])
        return filters.literal(GEOSGeometry(node[1][1]))


    def time_period(self, node):
        return (node[1], node[3])

    def duration(self, node):
        return parse_duration(node[1][1])

    def time(self, node):
        return parse_iso8601(node[1][1])


# print ECQLParser.repr_grammar()

def parse(inp, field_mapping):
    # return ECQLParser.parse(inp, ECQLParser.eval_node)
    try:
        test(inp)
        return ECQLParser.parse(inp, ECQLEvaluator(field_mapping))[1]
    except LrParsingError as e:
        print (dir(e))
        print (e.stack)
        print (e.input_token)
        print (inp.split("\n")[getattr(e, 'line', 1) - 1])
        print ("%s^" % (" " * getattr(e, 'column', 0)))
        raise


# def print_parse_tree(inp):
#     print ECQLParser.repr_parse_tree(ECQLParser.parse(inp))


def test(inp):
    print ("Processing: %r" % inp)
    try:
        # print_parse_tree(inp)
        # print tree
        print(ECQLParser.repr_parse_tree(ECQLParser.parse(inp)))
    except:
        traceback.print_exc()
    print


def inspect(inp):
    import pdb
    try:
        tree = parse(inp)
        pdb.set_trace()
        # print(ECQLParser.repr_parse_tree(tree))
    except:
        traceback.print_exc()


# test conditions
# test("(a > b) AND c = 5")
# test("(a < b) OR c = 5")
# test("NOT c = 5")

# test predicates

# test("a = b")
# test("a <> b")
# test("a < b")
# test("a <= b")
# test("a > b")
# test("a >= b")

# # test temporal predicates

# test("a BEFORE 2012-02-21T15:31:22Z")
# test("a BEFORE OR DURING 2012-02-21T15:31:22Z / P12D")
# test("a DURING P12D / 2012-02-21T15:31:22Z")
# test("a DURING OR AFTER 2012-02-21T15:31:22Z / 2013-02-21T15:31:22Z")
# test("a AFTER 2013-02-21T15:31:22Z")

# # test expressions

# test("a = 1 + 2")
# test("a = 1 - 2")
# test("a = 1 * 2")
# test("a = 1 / 2")

# test("a = 1 + 2 * 3")
# test("a = (1 + 2) * 3")


# test("a BETWEEN 1 AND 2")
# test("a NOT BETWEEN 1 AND 2")
# test("a IN (1, 2, 3, 4)")
# test("a NOT IN (1, 2, 3, 4)")
# test("a IS NULL")
# test("a IS NOT NULL")





# inspect("(a < b) OR c = 5")
