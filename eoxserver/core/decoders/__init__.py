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


import sys

from django.utils.six import reraise


ZERO_OR_ONE = "?"
ONE_OR_MORE = "+"
ANY = "*"

SINGLE_VALUES = (ZERO_OR_ONE, 1)


class DecodingException(Exception):
    """ Base Exception class to be thrown whenever a decoding failed.
    """

    def __init__(self, message, locator=None):
        super(DecodingException, self).__init__(message)
        self.locator = locator


class WrongMultiplicityException(DecodingException):
    """ Decoding Exception to be thrown when the multiplicity of a parameter did
        not match the expected count.
    """

    code = "InvalidParameterValue"

    def __init__(self, locator, expected, result):
        super(WrongMultiplicityException, self).__init__(
            "Parameter '%s': expected %s got %d" % (locator, expected, result),
            locator
        )


class MissingParameterException(DecodingException):
    """ Exception to be thrown, when a decoder could not read one parameter,
        where exactly one was required.
    """
    code = "MissingParameterValue"

    def __init__(self, locator):
        super(MissingParameterException, self).__init__(
            "Missing required parameter '%s'" % locator, locator
        )


class MissingParameterMultipleException(DecodingException):
    """ Exception to be thrown, when a decoder could not read at least one
        parameter, where one ore more were required.
    """
    code = "MissingParameterValue"

    def __init__(self, locator):
        super(MissingParameterMultipleException, self).__init__(
            "Missing at least one required parameter '%s'" % locator, locator
        )


class NoChoiceResultException(DecodingException):
    pass


class ExclusiveException(DecodingException):
    pass

# NOTE: The following exceptions may get propagated as OWS exceptions
#       therefore it is necessary to set the proper OWS exception code.


class InvalidParameterException(DecodingException):
    code = "InvalidParameterValue"


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
    """ Helper to concatenate the results of all sub-parameters to one.
    """
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
            except Exception:
                if self.allow_errors:
                    # swallow exception
                    continue

                exc_info = sys.exc_info()
                reraise(exc_info[0], exc_info[1], exc_info[2])

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
        split = value.split(self.separator)
        if self.typ:
            return [self.typ(v) for v in split]
        return split


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

    def __init__(self, values, case_sensitive=True, error_class=ValueError):
        self.values = values
        self.compare_values = values if case_sensitive else [lower(v) for v in values]
        self.case_sensitive = case_sensitive
        self.error_class = error_class

    def __call__(self, value):
        compare = value if self.case_sensitive else value.lower()
        if compare not in self.compare_values:
            raise self.error_class("Unexpected value '%s'. Expected one of: %s." %
                (value, ", ".join(map(lambda s: "'%s'" % s, self.values)))
            )

        return value


def lower(value):
    """ Functor to return a lower-case string.
    """
    return value.lower()


def upper(value):
    """ Functor to return a upper-case string.
    """
    return value.upper()


def strip(value):
    """ Functor to return a whitespace stripped string.
    """
    return value.strip()


class value_range(object):
    """ Helper to assert that a given parameter is within a specified range.
    """

    def __init__(self, min, max, type=float):
        self._min = min
        self._max = max
        self._type = type

    def __call__(self, raw):
        value = self._type(raw)
        if value < self._min or value > self._max:
            raise ValueError(
                "Given value '%s' exceeds expected bounds (%s, %s)"
                % (value, self._min, self._max)
            )
        return value


def boolean(raw):
    """ Functor to convert "true"/"false" to a boolean.
    """
    raw = raw.lower()
    if not raw in ("true", "false"):
        raise ValueError("Could not parse a boolean value from '%s'." % raw)
    return raw == "true"


def to_dict(decoder, dict_class=dict):
    """ Utility function to get a dictionary representation of the given decoder.
        This function invokes all decoder parameters and sets the dictionary
        fields accordingly
    """
    return dict(
        (name, getattr(decoder, name))
        for name in dir(decoder)
        if not name.startswith("_") and name != "namespaces"
    )
