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
from eoxserver.core.decoders.base import BaseParameter

class Parameter(BaseParameter):
    """ Parameter for XML values."""
    def __init__(self, selector, type=None, num=1, default=None,
                 namespaces=None, locator=None):
        super(Parameter, self).__init__(type, num, default)
        self.selector = selector
        self.namespaces = namespaces
        self._locator = locator

    def select(self, decoder, decoder_class=None):
        # prepare the XPath selector if necessary
        if isinstance(self.selector, basestring):
            namespaces = self.namespaces or decoder_class.namespaces
            self.selector = etree.XPath(self.selector, namespaces=namespaces)

        results = self.selector(decoder._tree)
        if isinstance(results, basestring):
            results = [results]

        return results

    @property
    def locator(self):
        return self._locator or str(self.selector)


class Decoder(object):
    """ Base class for XML Decoders."""
    namespaces = {}

    def __init__(self, tree):
        if isinstance(tree, basestring):
            try:
                tree = etree.fromstring(tree)
            except etree.XMLSyntaxError as exc:
                # NOTE: lxml.etree.XMLSyntaxError is incorretly identified as
                #       an OWS exception by the exception handler leading
                #       to a wrong OWS error response.  This exception thus
                #       must be cought and replaced by another exception
                #       of a different type.
                raise ValueError("Malformed XML document! %s"%(exc))
        self._tree = tree
