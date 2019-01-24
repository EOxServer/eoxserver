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


from ply import lex
from ply.lex import TOKEN
from django.contrib.gis.geos import GEOSGeometry, Polygon

from eoxserver.core.util.timetools import parse_iso8601, parse_duration


class ECQLLexer(object):
    def __init__(self, **kwargs):
        self.lexer = lex.lex(object=self, **kwargs)

    def build(self, **kwargs):
        pass
        # self.lexer.build()

    def input(self, *args):
        self.lexer.input(*args)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    keywords = (
        "NOT", "AND", "OR",
        "BETWEEN", "LIKE", "ILIKE", "IN", "IS", "NULL",
        "BEFORE", "AFTER", "DURING", "INTERSECTS", "DISJOINT", "CONTAINS",
        "WITHIN", "TOUCHES", "CROSSES", "OVERLAPS", "EQUALS", "RELATE",
        "DWITHIN", "BEYOND", "BBOX",
        "feet", "meters", "statute miles", "nautical miles", "kilometers"
    )

    tokens = keywords + (
        # Operators
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
        'LT', 'LE', 'GT', 'GE', 'EQ', 'NE',

        'LPAREN', 'RPAREN',
        'LBRACKET', 'RBRACKET',
        'COMMA',

        'GEOMETRY',
        'ENVELOPE',

        'UNITS',

        'ATTRIBUTE',
        'TIME',
        'DURATION',
        'FLOAT',
        'INTEGER',
        'QUOTED',
    )

    keyword_map = dict((keyword, keyword) for keyword in keywords)

    identifier_pattern = r'[a-zA-Z_$][0-9a-zA-Z_$]*'

    int_pattern = r'[0-9]+'
    # float_pattern = r'(?:[0-9]+[.][0-9]*|[.][0-9]+)(?:[Ee][-+]?[0-9]+)?'
    float_pattern = r'[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'

    time_pattern = "\d{4}-\d{2}-\d{2}T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z"
    duration_pattern = (
        # "P(?=[YMDHMS])"  # positive lookahead here... TODO: does not work
        # "((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
        "P((\d+Y)?(\d+M)?(\d+D)?)?(T(\d+H)?(\d+M)?(\d+S)?)?"
    )
    quoted_string_pattern = r'(\"[^"]*\")|(\'[^\']*\')'

    # for geometry parsing

    # a simple pattern that allows the simple float and integer notations (but
    # not the scientific ones). Maybe TODO
    number_pattern = r'-?[0-9]*\.?[0-9]+'

    coordinate_2d_pattern = r'%s\s+%s\s*' % (number_pattern, number_pattern)
    coordinate_3d_pattern = r'%s\s+%s\s*' % (
        coordinate_2d_pattern, number_pattern
    )
    coordinate_4d_pattern = r'%s\s+%s\s*' % (
        coordinate_3d_pattern, number_pattern
    )
    coordinate_pattern = r'((%s)|(%s)|(%s))' % (
        coordinate_2d_pattern, coordinate_3d_pattern, coordinate_4d_pattern
    )

    coordinates_pattern = r'%s(\s*,\s*%s)*' % (
        coordinate_pattern, coordinate_pattern
    )

    coordinate_group_pattern = r'\(\s*%s\s*\)' % coordinates_pattern
    coordinate_groups_pattern = r'%s(\s*,\s*%s)*' % (
        coordinate_group_pattern, coordinate_group_pattern
    )

    nested_coordinate_group_pattern = r'\(\s*%s\s*\)' % coordinate_groups_pattern
    nested_coordinate_groups_pattern = r'%s(\s*,\s*%s)*' % (
        nested_coordinate_group_pattern, nested_coordinate_group_pattern
    )

    geometry_pattern = (
        r'(POINT\s*\(%s\))|' % coordinate_pattern +
        r'((MULTIPOINT|LINESTRING)\s*\(%s\))|' % coordinates_pattern +
        r'((MULTIPOINT|MULTILINESTRING|POLYGON)\s*\(%s\))|' % (
            coordinate_groups_pattern
        ) +
        r'(MULTIPOLYGON\s*\(%s\))' % nested_coordinate_groups_pattern
    )
    envelope_pattern = r'ENVELOPE\s*\((\s*%s\s*){4}\)' % number_pattern

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_OR = r'OR'
    t_AND = r'AND'
    t_LT = r'<'
    t_GT = r'>'
    t_LE = r'<='
    t_GE = r'>='
    t_EQ = r'='
    t_NE = r'<>'

    # Delimeters
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_COMMA = r','

    @TOKEN(geometry_pattern)
    def t_GEOMETRY(self, t):
        t.value = GEOSGeometry(t.value)
        return t

    @TOKEN(envelope_pattern)
    def t_ENVELOPE(self, t):
        bbox = [
            float(number) for number in
            t.value.partition('(')[2].partition(')')[0].split()
        ]
        t.value = Polygon.from_bbox(bbox)
        return t

    @TOKEN(r'(feet)|(meters)|(statute miles)|(nautical miles)|(kilometers)')
    def t_UNITS(self, t):
        return t

    @TOKEN(time_pattern)
    def t_TIME(self, t):
        t.value = parse_iso8601(t.value)
        return t

    @TOKEN(duration_pattern)
    def t_DURATION(self, t):
        t.value = parse_duration(t.value)
        return t

    @TOKEN(float_pattern)
    def t_FLOAT(self, t):
        t.value = float(t.value)
        return t

    @TOKEN(int_pattern)
    def t_INTEGER(self, t):
        t.value = int(t.value)
        return t

    @TOKEN(quoted_string_pattern)
    def t_QUOTED(self, t):
        t.value = t.value[1:-1]
        return t

    @TOKEN(identifier_pattern)
    def t_ATTRIBUTE(self, t):
        t.type = self.keyword_map.get(t.value, "ATTRIBUTE")
        return t

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    def t_error(self, t):
        print "ERROR", t
