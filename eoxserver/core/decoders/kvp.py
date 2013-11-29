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

from eoxserver.core.decoders import (
    ZERO_OR_ONE, ONE_OR_MORE, ANY, SINGLE_VALUES, WrongMultiplicityException, 
    InvalidParameterException, MissingParameterException
)


class Parameter(object):
    key = None

    def __init__(self, key=None, type=None, separator=None, num=1, default=None,
                 locator=None):
        self.key = key.lower() if key is not None else None
        self.type = type
        self.separator = separator
        self.num = num
        self.default = default
        self.locator = locator

    def __get__(self, decoder, decoder_class=None):
        multiple = self.num not in SINGLE_VALUES
        locator = self.locator or self.key

        # TODO: allow simple dicts aswell
        results = decoder._query_dict.get(self.key, [])

        
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


class DecoderMetaclass(type):
    def __init__(cls, name, bases, dct):
        for key, value in dct.items():
            if isinstance(value, Parameter) and value.key is None:
                value.key = key.lower()

        return super(DecoderMetaclass, cls).__init__(name, bases, dct)


class Decoder(object):
    __metaclass__ = DecoderMetaclass
    
    def __init__(self, params):
        query_dict = {}
        if isinstance(params, QueryDict):
            for key, values in params.lists():
                query_dict[key.lower()] = values
        
        else:
            tmp = parse_qs(params)
            for key, values in tmp.items():
                query_dict[key.lower()] = values
        
        self.kvp = params
        self._query_dict = query_dict
