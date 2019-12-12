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

""" This module contains facilities to help decoding KVP strings.
"""

from django.http import QueryDict
from django.utils.six import string_types, add_metaclass
from django.utils.six.moves.urllib.parse import parse_qs

from eoxserver.core.decoders.base import BaseParameter


class Parameter(BaseParameter):
    """ Parameter for KVP values.

        :param key: the lookup key; defaults to the property name of the
                    :class:`Decoder`
        :param type: the type to parse the raw value; by default the raw
                     string is returned
        :param num: defines how many times the key can be present; use any
                    numeric value to set it to a fixed count, "*" for any
                    number, "?" for zero or one time or "+" for one or more
                    times
        :param default: the default value
        :param locator: override the locator in case of exceptions
    """

    key = None

    def __init__(self, key=None, type=None, num=1, default=None, locator=None):
        super(Parameter, self).__init__(type, num, default)
        self.key = key.lower() if key is not None else None
        self._locator = locator

    def select(self, decoder, decoder_class=None):
        return [
            value for value in decoder._query_dict.get(self.key, [])
            if value != ""
        ]

    @property
    def locator(self):
        return self._locator or self.key


class MultiParameter(Parameter):
    """ Class for selecting different KVP parameters at once.

        :param selector: a function to determine if a key is used for the multi
                         parameter selection
        :param num: defines how many times the key can be present; use any
                    numeric value to set it to a fixed count, "*" for any
                    number, "?" for zero or one time or "+" for one or more
                    times
        :param default: the default value
        :param locator: override the locator in case of exceptions
    """

    def __init__(self, selector, num=1, default=None, locator=None):
        super(MultiParameter, self).__init__(
            "", lambda s: s, num, default, locator
        )
        self.key = selector

    def select(self, decoder):
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


@add_metaclass(DecoderMetaclass)
class Decoder(object):
    """ Base class for KVP decoders.

    :param params: an instance of either :class:`dict`,
                   :class:`django.http.QueryDict` or :class:`basestring` (which
                   will be parsed using :func:`cgi.parse_qs`)

    Decoders should be used as such:
    ::

        from eoxserver.core.decoders import kvp
        from eoxserver.core.decoders import typelist

        class ExampleDecoder(kvp.Decoder):
            mandatory_param = kvp.Parameter(num=1)
            list_param = kvp.Parameter(type=typelist(separator=","))
            multiple_param = kvp.Parameter("multi", num="+")
            optional_param = kvp.Parameter(num="?", default="default_value")

        decoder = ExampleDecoder(
            "mandatory_param=value"
            "&list_param=a,b,c"
            "&multi=a&multi=b&multi=c"
        )

        print decoder.mandatory_param
        print decoder.list_param
        print decoder.multiple_param
        print decoder.optional_param
    """

    __metaclass__ = DecoderMetaclass

    def __init__(self, params):
        query_dict = {}
        if isinstance(params, QueryDict):
            for key, values in params.lists():
                query_dict[key.lower()] = values

        elif isinstance(params, string_types):
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
