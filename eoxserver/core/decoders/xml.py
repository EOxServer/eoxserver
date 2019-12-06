#-------------------------------------------------------------------------------
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

""" This module contains facilities to help decoding XML structures.
"""

from lxml import etree
from eoxserver.core.decoders.base import BaseParameter
from django.utils.six import string_types


class Parameter(BaseParameter):
    """ Parameter for XML values.

        :param selector: the node selector; if a string is passed it is
                         interpreted as an XPath expression, a callable will be
                         called with the root of the element tree and shall
                         yield any number of node
        :param type: the type to parse the raw value; by default the raw
                     string is returned
        :param num: defines how many times the key can be present; use any
                    numeric value to set it to a fixed count, "*" for any
                    number, "?" for zero or one time or "+" for one or more
                    times
        :param default: the default value
        :param namespaces: any namespace necessary for the XPath expression;
                           defaults to the :class:`Decoder` namespaces.
        :param locator: override the locator in case of exceptions
    """

    def __init__(self, selector, type=None, num=1, default=None,
                 namespaces=None, locator=None):
        super(Parameter, self).__init__(type, num, default)
        self.selector = selector
        self.namespaces = namespaces
        self._locator = locator

    def select(self, decoder):
        # prepare the XPath selector if necessary
        if isinstance(self.selector, string_types):
            namespaces = self.namespaces or decoder.namespaces
            self.selector = etree.XPath(self.selector, namespaces=namespaces)
        results = self.selector(decoder._tree)
        if isinstance(results, (string_types + (float, int))):
            results = [results]

        return results

    @property
    def locator(self):
        return self._locator or str(self.selector)


class Decoder(object):
    """ Base class for XML Decoders.

        :param params: an instance of either :class:`lxml.etree.ElementTree`,
                       or :class:`basestring` (which will be parsed using
                       :func:`lxml.etree.fromstring`)

    Decoders should be used as such:
    ::

        from eoxserver.core.decoders import xml
        from eoxserver.core.decoders import typelist

        class ExampleDecoder(xml.Decoder):
            namespaces = {"myns": "http://myns.org"}
            single = xml.Parameter("myns:single/text()", num=1)
            items = xml.Parameter("myns:collection/myns:item/text()", num="+")
            attr_a = xml.Parameter("myns:object/@attrA", num="?")
            attr_b = xml.Parameter("myns:object/@attrB", num="?", default="x")


        decoder = ExampleDecoder('''
            <myns:root xmlns:myns="http://myns.org">
                <myns:single>value</myns:single>
                <myns:collection>
                    <myns:item>a</myns:item>
                    <myns:item>b</myns:item>
                    <myns:item>c</myns:item>
                </myns:collection>
                <myns:object attrA="value"/>
            </myns:root>
        ''')

        print decoder.single
        print decoder.items
        print decoder.attr_a
        print decoder.attr_b
    """

    namespaces = {}  # must be overriden if the XPath expressions use namespaces

    def __init__(self, tree):
        if isinstance(tree, string_types) or isinstance(tree, bytes):
            try:
                tree = etree.fromstring(tree)
                
            except etree.XMLSyntaxError as exc:
                # NOTE: lxml.etree.XMLSyntaxError is incorretly identified as
                #       an OWS exception by the exception handler leading
                #       to a wrong OWS error response.  This exception thus
                #       must be cought and replaced by another exception
                #       of a different type.
                raise ValueError("Malformed XML document. Error was %s" % exc)
        self._tree = tree
