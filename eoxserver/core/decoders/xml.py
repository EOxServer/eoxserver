#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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
#-------------------------------------------------------------------------------


from lxml import etree

from eoxserver.core.decoders import (
    ZERO_OR_ONE, ONE_OR_MORE, ANY, SINGLE_VALUES, WrongMultiplicityException, 
    InvalidParameterException, MissingParameterException
)


class Parameter(object):
    def __init__(self, selector, type=None, separator=None,
                 num=1, default=None, namespaces=None, locator=None):
        self.selector = selector
        self.type = type or str # default to string, because XPath might return some kind of object
        self.separator = separator
        self.num = num # int or "?", "+", "*"
        self.default = default # only used for "?"
        self.namespaces = namespaces
        self.locator = locator


    def __get__(self, decoder, decoder_class=None):
        # prepare the XPath selector if necessary
        if isinstance(self.selector, basestring):
            namespaces = self.namespaces or decoder_class.namespaces
            self.selector = etree.XPath(self.selector, namespaces=namespaces)

        locator = self.locator or str(self.selector)
        multiple = self.num not in SINGLE_VALUES

        results = self.selector(decoder._tree)
        if isinstance(results, basestring):
            results = [results]
        count = len(results)

        if not multiple and count > 1:
            raise WrongMultiplicityException(
                "Expected at most one, got %d." % count, locator
            )

        elif self.num == 1 and count == 0:
            raise MissingParameterException(
                "Expected exactly one, got none.", locator
            )

        elif self.num == ONE_OR_MORE and count == 0:
            raise MissingParameterException(
                "Expected at least one, got none.", locator
            )

        elif isinstance(self.num, int) and count != self.num:
            raise WrongMultiplicityException(
                "Expected %d, got %d." % (self.num, count), locator
            )

        if multiple:
            try:
                return map(self.type, results)
            except Exception, e:
                # let some more sophisticated exceptions pass
                if hasattr(e, "locator") or hasattr(e, "code"):
                    raise
                raise InvalidParameterException(str(e), locator)

        elif self.num == ZERO_OR_ONE and count == 0:
            return self.default

        elif self.type:
            try:
                return self.type(results[0])
            except Exception, e:
                # let some more sophisticated exceptions pass
                if hasattr(e, "locator") or hasattr(e, "code"):
                    raise
                raise InvalidParameterException(str(e), locator)

        return results[0]


class Decoder(object):
    """ Base class for XML Decoders.
    """

    namespaces = {}

    def __init__(self, tree):
        if isinstance(tree, basestring):
            tree = etree.fromstring(tree)
        self._tree = tree
