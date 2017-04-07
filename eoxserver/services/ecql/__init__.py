from .parser import ECQLParser


def parse(cql, mapping=None, mapping_choices=None):
    parser = ECQLParser(mapping, mapping_choices)
    return parser.parse(cql)
