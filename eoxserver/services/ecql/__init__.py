from .parser import ECQLParser


def parse(cql, mapping=None):
    parser = ECQLParser(mapping)
    return parser.parse(cql)
