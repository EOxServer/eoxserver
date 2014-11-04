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


from cgi import parse_qs

from django.http import QueryDict

from eoxserver.core.decoders.base import BaseParameter


class Parameter(BaseParameter):
    """ Parameter for KVP values.
    """

    key = None

    def __init__(self, key=None, type=None, num=1, default=None, locator=None):
        super(Parameter, self).__init__(type, num, default)
        self.key = key.lower() if key is not None else None
        self._locator = locator

    def select(self, decoder, decoder_class=None):
        return decoder._query_dict.get(self.key, [])

    @property
    def locator(self):
        return self._locator or self.key


class MultiParameter(Parameter):
    """ Class for selecting different KVP parameters at once.
    """

    def __init__(self, selector, num=1, default=None, locator=None):
        super(MultiParameter, self).__init__(
            "", lambda s: s, num, default, locator
        )
        self.key = selector

    def select(self, decoder, decoder_class=None):
        result = []
        for key, values in decoder._query_dict.items():
            if self.key(key):
                result.append((key, values))

        return result


class DecoderMetaclass(type):
    """ Metaclass for KVP Decoders to allow easy parameter declaration.
    """
    def __init__(cls, name, bases, dct):
        # set the "key" attribute of any parameter to the parameters name
        # if no other key was specified.
        for key, value in dct.items():
            if isinstance(value, Parameter) and value.key is None:
                value.key = key.lower()

        super(DecoderMetaclass, cls).__init__(name, bases, dct)


class Decoder(object):
    """ Base class for KVP decoders.
    """
    __metaclass__ = DecoderMetaclass

    def __init__(self, params):
        query_dict = {}
        if isinstance(params, QueryDict):
            for key, values in params.lists():
                query_dict[key.lower()] = values

        elif isinstance(params, basestring):
            tmp = parse_qs(params)
            for key, values in tmp.items():
                query_dict[key.lower()] = values

        elif isinstance(params, dict):
            for key, value in params.items():
                query_dict[key.lower()] = (value,)

        else:
            raise ValueError(
                "Decoder input '%s' not supported." % type(params).__name__
            )

        self.kvp = params
        self._query_dict = query_dict
