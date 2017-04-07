from .parser import ECQLParser
from .ast import to_filter, get_repr


def parse(cql, mapping=None, mapping_choices=None):
    parser = ECQLParser()
    return parser.parse(cql)
