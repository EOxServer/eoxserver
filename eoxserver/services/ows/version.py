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


from functools import wraps
try:
    from functools import total_ordering
except ImportError:
    from eoxserver.core.util.functools import total_ordering

from django.utils.six import string_types


__all__ = ["parse_version_string", "Version"]


def parse_version_string(version_string):
    """ Convenience function to parse a version from a string.
    """
    return Version(*map(int, version_string.split(".")))


def convert_to_version(f):
    """ Decorator to automatically parse a ``Version`` from a string.
    """

    @wraps(f)
    def wrapper(self, other):
        if isinstance(other, Version):
            return f(self, other)
        elif isinstance(other, string_types):
            return f(self, parse_version_string(other))
        try:
            return f(self, Version(*other))
        except TypeError:
            pass
        raise TypeError("Cannot convert '%s' to version" % type(other).__name__)
    return wrapper


@total_ordering
class Version(object):
    """ Abstraction for OWS versions. Must be in the form 'x.y(.z)', where all
        components must be positive integers or zero. The last component may be
        unspecified (None).

        Versions can be compared with other versions. Strings and tuples of the
        correct layout are also compareable.

        Versions are compared by the "major" and the "minor" number. Only if
        both versions provide a "revision" it is taken into account. So Versions
        "1.0" and "1.0.1" are considered equal!
    """

    def __init__(self, major, minor, revision=None):
        try:
            assert(isinstance(major, int) and major >= 0)
            assert(isinstance(minor, int) and minor >= 0)
            assert(revision is None
                   or (isinstance(revision, int) and revision >= 0))
        except AssertionError:
            raise ValueError("Invalid version components supplied.")

        if revision is None:
            self._values = (major, minor)
        else:
            self._values = (major, minor, revision)

    @property
    def major(self):
        return self._values[0]

    @property
    def minor(self):
        return self._values[1]

    @property
    def revision(self):
        try:
            return self._values[2]
        except IndexError:
            return None

    @convert_to_version
    def __eq__(self, other):
        for self_v, other_v in zip(self._values, other._values):
            if self_v != other_v:
                return False
        return True

    @convert_to_version
    def __lt__(self, other):
        for self_v, other_v in zip(self._values, other._values):
            if self_v < other_v:
                return True
            elif self_v > other_v:
                return False
        return False

    def __str__(self):
        return ".".join(map(str, self._values))

    def __repr__(self):
        return '<%s.%s ("%s") instance at 0x%x>' % (
            __name__, type(self).__name__, str(self), id(self)
        )
