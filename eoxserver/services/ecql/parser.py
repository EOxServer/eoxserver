from ply import yacc

from eoxserver.services.ecql.lexer import ECQLLexer
from eoxserver.services import filters


class ECQLParser(object):
    def __init__(self, field_mapping=None, mapping_choices=None):
        self.lexer = ECQLLexer(
            optimize=True,
            # lextab='ecql.lextab',
            # outputdir="ecql"
        )

        self.lexer.build()
        self.tokens = self.lexer.tokens

        self.parser = yacc.yacc(
            module=self,
            # start='condition_or_empty',
            # debug=True,
            optimize=True,
            # tabmodule='ecql.yacctab',
            # outputdir="ecql"

            errorlog=yacc.NullLogger(),
        )
        self.field_mapping = field_mapping or {}
        self.mapping_choices = mapping_choices

    def parse(self, text):
        return self.parser.parse(
            input=text,
            lexer=self.lexer
        )

    precedence = (
        ('left', 'EQ', 'NE'),
        ('left', 'GT', 'GE', 'LT', 'LE'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
    )

    #
    # grammar
    #

    start = 'condition_or_empty'

    def p_condition_or_empty(self, p):
        """ condition_or_empty : condition
                               | empty
        """
        p[0] = p[1]

    def p_condition(self, p):
        """ condition : predicate
                      | condition AND condition
                      | condition OR condition
                      | NOT condition
                      | LPAREN condition RPAREN
                      | LBRACKET condition RBRACKET
        """

        if len(p) == 2:
            p[0] = p[1]
        elif p[2] in ("AND", "OR"):
            p[0] = filters.combine([p[1], p[3]], p[2])
        elif p[1] == "NOT":
            p[0] = filters.negate(p[2])
        elif p[1] in ("(", "["):
            p[0] = p[2]

    def p_predicate(self, p):
        """ predicate : expression EQ expression
                      | expression NE expression
                      | expression LT expression
                      | expression LE expression
                      | expression GT expression
                      | expression GE expression
                      | expression NOT BETWEEN expression AND expression
                      | expression BETWEEN expression AND expression
                      | expression NOT LIKE QUOTED
                      | expression LIKE QUOTED
                      | expression NOT ILIKE QUOTED
                      | expression ILIKE QUOTED
                      | expression NOT IN LPAREN expression_list RPAREN
                      | expression IN LPAREN expression_list RPAREN
                      | expression IS NOT NULL
                      | expression IS NULL
                      | temporal_predicate
                      | spatial_predicate
        """
        if len(p) == 2:  # hand over temporal and spatial predicates
            p[0] = p[1]

        elif p[2] in ("=", "<>", "<", "<=", ">", ">="):
            p[0] = filters.compare(p[1], p[3], p[2], self.mapping_choices)
        else:
            not_ = False
            op = p[2]
            if op == 'NOT':
                not_ = True
                op = p[3]

            if op == "BETWEEN":
                p[0] = filters.between(
                    p[1], p[4 if not_ else 3], p[6 if not_ else 5], not_
                )
            elif op in ("LIKE", "ILIKE"):
                p[0] = filters.like(
                    p[1], p[4 if not_ else 3], op == "ILIKE", not_
                )
            elif op == "IN":
                p[0] = filters.contains(p[1], p[5 if not_ else 4], not_)

            elif op == "IS":
                p[0] = filters.null(p[1], p[3] == "NOT")

    def p_temporal_predicate(self, p):
        """ temporal_predicate : expression BEFORE TIME
                               | expression BEFORE OR DURING time_period
                               | expression DURING time_period
                               | expression DURING OR AFTER time_period
                               | expression AFTER TIME
        """

        if len(p) > 4:
            op = " ".join(p[2:-1])
        else:
            op = p[2]

        p[0] = filters.temporal(p[1], p[3 if len(p) == 4 else 5], op)

    def p_time_period(self, p):
        """ time_period : TIME DIVIDE TIME
                        | TIME DIVIDE DURATION
                        | DURATION DIVIDE TIME
        """
        p[0] = (p[1], p[3])

    def p_spatial_predicate(self, p):
        """ spatial_predicate : INTERSECTS LPAREN expression COMMA expression RPAREN
                              | DISJOINT LPAREN expression COMMA expression RPAREN
                              | CONTAINS LPAREN expression COMMA expression RPAREN
                              | WITHIN LPAREN expression COMMA expression RPAREN
                              | TOUCHES LPAREN expression COMMA expression RPAREN
                              | CROSSES LPAREN expression COMMA expression RPAREN
                              | OVERLAPS LPAREN expression COMMA expression RPAREN
                              | EQUALS LPAREN expression COMMA expression RPAREN
                              | RELATE LPAREN expression COMMA expression COMMA QUOTED RPAREN
                              | DWITHIN LPAREN expression COMMA expression COMMA number COMMA UNITS RPAREN
                              | BEYOND LPAREN expression COMMA expression COMMA number COMMA UNITS RPAREN
                              | BBOX LPAREN expression COMMA number COMMA number COMMA number COMMA number COMMA QUOTED RPAREN
        """
        # TODO: RELATE, DWITHIN, BEYOND, BBOX
        op = p[1]
        lhs = p[3]
        rhs = p[5]

        if op == "RELATE":
            p[0] = filters.spatial(lhs, rhs, op, pattern=p[7])
        elif op in ("DWITHIN", "BEYOND"):
            p[0] = filters.spatial(lhs, rhs, op, distance=p[7], units=p[9])
        elif op == "BBOX":
            p[0] = filters.bbox(lhs, *p[5::2])
        else:
            p[0] = filters.spatial(lhs, rhs, op)

    def p_expression_list(self, p):
        """ expression_list : expression_list COMMA expression
                            | expression
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[1].append(p[3])
            p[0] = p[1]

    def p_expression(self, p):
        """ expression : expression PLUS expression
                       | expression MINUS expression
                       | expression TIMES expression
                       | expression DIVIDE expression
                       | LPAREN expression RPAREN
                       | LBRACKET expression RBRACKET
                       | GEOMETRY
                       | ENVELOPE
                       | attribute
                       | QUOTED
                       | INTEGER
                       | FLOAT
        """
        if len(p) == 2:
            p[0] = p[1]
        else:
            if p[1] in ("(", "["):
                p[0] = p[2]
            else:
                op = p[2]
                lhs = p[1]
                rhs = p[3]
                p[0] = filters.arithmetic(lhs, rhs, op)

    def p_number(self, p):
        """ number : INTEGER
                   | FLOAT
        """
        p[0] = p[1]

    def p_attribute(self, p):
        """ attribute : ATTRIBUTE
        """
        p[0] = filters.attribute(p[1], self.field_mapping)

    def p_empty(self, p):
        'empty : '
        p[0] = None

    def p_error(self, p):
        if p:
            print dir(p)
            print("Syntax error at token", p.type, p.value, p.lexpos, p.lineno)
            # Just discard the token and tell the parser it's okay.
            #p.parser.errok()
        else:
            print("Syntax error at EOF")

# if __name__ == "__main__":
#     p = ECQLParser()
#     p.parse(
#         # 'a = 0 AND '
#         # 'b = "2" AND '
#         # 'x IN (a, b, c)'
#         # 'INTERSECTS(x, POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, 30 20, 20 30)))'
#         '2212312312 / abasnfoansfo + basdasfasfas * 5555555555555 = x'
#         ''
#     )

#     # # Give the lexer some input
#     # lexer = ECQLLexer()
#     # lexer.build()
#     # # lexer.input(
#     # #     'a = 1 AND b = "2" OR c = 2007-01-25T12:00:00Z'
#     # #     'AND d = MULTIPOINT(2 5)'
#     # # )
#     # lexer.input(
#     #     'POINT (30 10)'
#     #     'LINESTRING (30 10, 10 30, 40 40)'
#     #     'POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))'
#     #     'POLYGON ((35 10, 45 45, 15 40, 10 20, 35 10), (20 30, 35 35, 30 20, 20 30))'
#     #     'MULTIPOINT ((10 40), (40 30), (20 20), (30 10))'
#     #     'MULTIPOINT (10 40, 40 30, 20 20, 30 10)'
#     #     'MULTILINESTRING ((10 10, 20 20, 10 40), (40 40, 30 30, 40 20, 30 10))'
#     #     'MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)), ((15 5, 40 10, 10 20, 5 10, 15 5)))'
#     #     'MULTIPOLYGON (((40 40, 20 45, 45 30, 40 40)), ((20 35, 10 30, 10 10, 30 5, 45 20, 20 35), (30 20, 20 15, 20 25, 30 20)))'
#     # )

#     # # Tokenize
#     # while True:
#     #     tok = lexer.token()
#     #     if not tok:
#     #         break      # No more input
#     #     print(tok)
