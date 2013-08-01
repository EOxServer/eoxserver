import sys

from lxml import etree

from eoxserver.core.decoders import (
    ZERO_OR_ONE, ONE_OR_MORE, ANY, SINGLE_VALUES, WrongMultiplicity, typelist
)


class Parameter(object):
    def __init__(self, selector, type=None, separator=None,
                 num=1, default=None, namespaces=None):
        self.selector = selector
        self.type = type
        self.separator = separator
        self.num = num # int or "?", "+", "*"
        self.default = default # only used for "?"
        self.namespaces = namespaces


    def __get__(self, decoder, decoder_class=None):
        # prepare the XPath selector if necessary
        if isinstance(self.selector, basestring):
            namespaces = self.namespaces or decoder_class.namespaces
            self.selector = etree.XPath(selector, namespaces=namespaces)

        multiple = self.num not in SINGLE_VALUES
        results = self.selector(decoder._tree)
        count = len(results)

        if not multiple and count > 1:
            raise WrongMultiplicity

        elif isinstance(self.num, int) and count != self.num:
            raise WrongMultiplicity("Expected %d, got %d." % (self.num, count))

        elif self.num == ONE_OR_MORE and count == 0:
            raise WrongMultiplicity

        if multiple:
            return map(self.type, results)

        elif self.num == ZERO_OR_ONE and count == 0:
            return self.default

        elif self.type:
            return self.type(results[0])

        return results[0]


class Decoder(object):
    """ Base class for XML Decoders.
    """

    namespaces = {}

    def __init__(self, tree):
        if isinstance(tree, basestring):
            tree = etree.fromstring(tree)
        self._tree = tree
