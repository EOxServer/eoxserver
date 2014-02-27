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


import sys


ZERO_OR_ONE = "?"
ONE_OR_MORE = "+"
ANY = "*"

SINGLE_VALUES = (ZERO_OR_ONE, 1)


class DecodingException(Exception):
    def __init__(self, message, locator=None):
        super(DecodingException, self).__init__(message)
        self.locator = locator

    def __str__(self):
        if self.locator:
            return "%s: %s" % (self.locator, super(DecodingException, self).__str__())
        return super(DecodingException, self).__str__()

class WrongMultiplicityException(DecodingException):
    pass


class NoChoiceResultException(DecodingException):
    pass


class ExclusiveException(DecodingException):
    pass


# NOTE: The following exceptions may get propagated as OWS exceptions 
#       therefore it is necessary to set the proper OWS exception code.

class InvalidParameterException(DecodingException):
    code = "InvalidParameterValue"
    pass


class MissingParameterException(DecodingException):
    code = "MissingParameterValue"
    pass


# Compound fields


class Choice(object):
    """ Tries all given choices until one does return something.
    """

    def __init__(self, *choices):
        self.choices = choices


    def __get__(self, decoder, decoder_class=None):
        for choice in self.choices:
            try: 
                return choice.__get__(decoder, decoder_class)
            except:
                continue
        raise NoChoiceResultException


class Exclusive(object):
    """ For mutual exclusive Parameters.
    """

    def __init__(self, *choices):
        self.choices = choices


    def __get__(self, decoder, decoder_class=None):
        result = None
        num = 0
        for choice in self.choices:
            try: 
                result = choice.__get__(decoder, decoder_class)
                num += 1
            except:
                continue

        if num != 1:
            raise ExclusiveException

        return result


class Concatenate(object):
    def __init__(self, *choices, **kwargs):
        self.choices = choices
        self.allow_errors = kwargs.get("allow_errors", True)
        

    def __get__(self, decoder, decoder_class=None):
        result = []
        for choice in self.choices:
            try: 
                value = choice.__get__(decoder, decoder_class)
                if isinstance(value, (list, tuple)):
                    result.extend(value)
                else:
                    result.append(value)
            except Exception, e:
                if self.allow_errors:
                    # swallow exception
                    continue

                exc_info = sys.exc_info()
                raise exc_info[0], exc_info[1], exc_info[2]

        return result


# Type conversion helpers


class typelist(object):
    """ Helper for XMLDecoder schemas that expect a string that represents a 
        list of a type separated by some separator.
    """
    
    def __init__(self, typ=None, separator=" "):
        self.typ = typ
        self.separator = separator
        
    
    def __call__(self, value):
        return map(self.typ, value.split(self.separator))


class fixed(object):
    """ Helper for parameters that are expected to be have a fixed value and 
        raises a ValueError if not.
    """

    def __init__(self, value, case_sensitive=True):
        self.value = value if case_sensitive else value.lower()
        self.case_sensitive = case_sensitive


    def __call__(self, value):
        compare = value if self.case_sensitive else value.lower()
        if self.value != compare:
            raise ValueError("Value mismatch, expected %s, got %s." %
                (self.value, value)
            )

        return value


class enum(object):
    """ Helper for parameters that are expected to be in a certain enumeration.
        A ValueError is raised if not.
    """

    def __init__(self, values, case_sensitive=True):
        if not case_sensitive:
            values = map(lambda v: v.lower(), values)
        self.values = values
        self.case_sensitive = case_sensitive


    def __call__(self, value):
        compare = value if self.case_sensitive else value.lower()
        if compare not in self.values:
            raise ValueError("Unexpected value '%s'. Expected one of: %s." %
                (value, ", ".join(self.values))
            )

        return value

def lower(value):
    return value.lower()


def upper(value):
    return value.upper()

def strip(value):
    return value.strip()
