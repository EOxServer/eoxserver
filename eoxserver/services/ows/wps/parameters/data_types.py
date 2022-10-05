#-------------------------------------------------------------------------------
#
#  Library of primitive data type classes.
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from datetime import datetime, date, time, timedelta
from django.utils.dateparse import parse_date, parse_datetime, parse_time, utc
from django.utils.six import PY2, PY3, string_types
from django.utils.encoding import smart_str
from eoxserver.core.util.timetools import parse_duration

try:
    from datetime import timezone

    # as this class will be deprecated in Django 3.1, offer a constructor
    def FixedOffset(offset, name=None):
        if isinstance(offset, timedelta):
            pass
        else:
            offset = timedelta(minutes=offset)
        return timezone(offset) if name is None else timezone(offset, name)

except ImportError:
    from django.utils.timezone import FixedOffset


class BaseType(object):
    """ Base literal data type class.
        This class defines the class interface.
    """
    name = None  # to be replaced by a name
    if PY2:
        dtype = str
    elif PY3:
        dtype = bytes
    zero = None  # when applicable to be replaced by a proper zero value
    comparable = True  # indicate whether the type can be compared (<,>,==)

    @classmethod
    def parse(cls, raw_value):
        """ Cast or parse input to its proper representation."""
        return cls.dtype(raw_value)

    @classmethod
    def encode(cls, value):
        """ Encode value to a Unicode string."""
        return smart_str(value)

    @classmethod
    def get_diff_dtype(cls):  # difference type - change if differs from the base
        """ Get type of the difference of this type.
            E.g., `timedelta` for a `datetime`.
        """
        return cls

    @classmethod
    def as_number(cls, value):  # pylint: disable=unused-argument
        """ convert to a number (e.g., duration)"""
        raise TypeError("Data type %s cannot be converted to a number!" % cls)

    @classmethod
    def sub(cls, value0, value1):  # pylint: disable=unused-argument
        """ subtract value0 - value1 """
        raise TypeError("Data type %s cannot be subtracted!" % cls)


class Boolean(BaseType):
    """ Boolean literal data type class. """
    name = "boolean"
    dtype = bool

    @classmethod
    def parse(cls, raw_value):

        if isinstance(raw_value, string_types):
            raw_value = smart_str(raw_value.lower())
            if raw_value in ('1', 'true'):
                return True
            elif raw_value in ('0', 'false'):
                return False
            else:
                raise ValueError("Cannot parse boolean value '%s'!" % raw_value)
        else:
            return bool(raw_value)

    @classmethod
    def encode(cls, value):
        return u'true' if value else u'false'

    @classmethod
    def as_number(cls, value):
        return int(value)

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1


class Integer(BaseType):
    """ Integer literal data type class. """
    name = "integer"
    dtype = int
    zero = 0

    @classmethod
    def encode(cls, value):
        """ Encode value to a Unicode string."""
        return smart_str(int(value))

    @classmethod
    def as_number(cls, value):
        return value

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1


class Double(BaseType):
    """ Double precision float literal data type class. """
    name = "double"
    dtype = float
    zero = 0.0

    @classmethod
    def encode(cls, value):
        return u"%.15g" % cls.dtype(value)

    @classmethod
    def as_number(cls, value):
        return value

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1


class String(BaseType):
    """ Unicode character string literal data type class. """
    name = "string"
    if PY2:
        dtype = unicode
    elif PY3:
        dtype = str
    encoding = 'utf-8'
    comparable = False  # disabled although Python implements comparable strings

    @classmethod
    def encode(cls, value):
        """ Encode value to a Unicode string."""
        try:
            return smart_str(value)
        except UnicodeDecodeError:
            return smart_str(value, cls.encoding)

    @classmethod
    def parse(cls, raw_value):
        return cls.dtype(raw_value)

    @classmethod
    def get_diff_dtype(cls):  # string has no difference
        return None


class Duration(BaseType):
    """ Duration (`datetime.timedelta`) literal data type class. """
    name = "duration"
    dtype = timedelta
    zero = timedelta(0)

    @classmethod
    def parse(cls, raw_value):
        if isinstance(raw_value, cls.dtype):
            return raw_value
        return parse_duration(raw_value)

    @classmethod
    def encode(cls, value):
        # NOTE: USE OF MONTH AND YEAR IS AMBIGUOUS! WE DO NOT ENCODE THEM!
        if not isinstance(value, cls.dtype):
            raise ValueError("Invalid value type '%s'!" % type(value))
        items = []
        if value.days < 0:
            items.append('-')
            value = -value
        items.append('P')
        if value.days != 0:
            items.append('%dD' % value.days)
        elif value.seconds == 0 and value.microseconds == 0:
            items.append('T0S')  # zero interval
        if value.seconds != 0 or value.microseconds != 0:
            minutes, seconds = divmod(value.seconds, 60)
            hours, minutes = divmod(minutes, 60)
            items.append('T')
            if hours != 0:
                items.append('%dH' % hours)
            if minutes != 0:
                items.append('%dM' % minutes)
            if value.microseconds != 0:
                items.append("%.6fS" % (seconds + 1e-6*value.microseconds))
            elif seconds != 0:
                items.append('%dS' % seconds)

        return smart_str("".join(items))

    @classmethod
    def as_number(cls, value):
        return 86400.0*value.days + 1.0*value.seconds + 1e-6*value.microseconds

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1


class Date(BaseType):
    """ Date (`datetime.date`) literal data type class. """
    name = "date"
    dtype = date

    @classmethod
    def get_diff_dtype(cls):
        return Duration

    @classmethod
    def parse(cls, raw_value):
        if isinstance(raw_value, cls.dtype):
            return raw_value
        value = parse_date(raw_value)
        if value:
            return value
        raise ValueError("Could not parse ISO date from '%s'." % raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return smart_str(value.isoformat())
        raise ValueError("Invalid value type '%s'!" % type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1


class Time(BaseType):
    """ Time (`datetime.time`) literal data type class. """
    name = "time"
    dtype = time
    # TODO: implement proper Time time-zone handling

    @classmethod
    def get_diff_dtype(cls):
        return Duration

    @classmethod
    def parse(cls, raw_value):
        if isinstance(raw_value, cls.dtype):
            return raw_value
        value = parse_time(raw_value)
        if value is not None:
            return value
        raise ValueError("Could not parse ISO time from '%s'." % raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return smart_str(value.isoformat())
        raise ValueError("Invalid value type '%s'!" % type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        aux_date = datetime.now().date()
        dt0 = datetime.combine(aux_date, value0)
        dt1 = datetime.combine(aux_date, value1)
        return dt0 - dt1


class DateTime(BaseType):
    """ Date-time (`datetime.datetime`) literal data type class. """
    name = "dateTime"
    dtype = datetime

    # tzinfo helpers
    UTC = utc               # Zulu-time TZ instance
    TZOffset = FixedOffset  # fixed TZ offset class, set minutes to instantiate

    @classmethod
    def get_diff_dtype(cls):
        return Duration

    @classmethod
    def parse(cls, raw_value):
        if isinstance(raw_value, cls.dtype):
            return raw_value
        value = parse_datetime(raw_value)
        if value:
            return value
        raise ValueError("Could not parse ISO date-time from '%s'." % raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return smart_str(cls._isoformat(value))
        raise ValueError("Invalid value type '%s'!" % type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ subtract value0 - value1 """
        return value0 - value1

    @staticmethod
    def _isoformat(value):
        """ Covert date-time object to ISO 8601 date-time string. """
        if value.tzinfo and not value.utcoffset():
            return value.replace(tzinfo=None).isoformat("T") + "Z"
        return value.isoformat("T")


class DateTimeTZAware(DateTime):
    """ Time-zone aware date-time (`datetime.datetime`) literal data type class.

    This data-type is a variant of the `DateTime` which assures that
    the parsed date-time is time-zone aware and optionally
    also converted to a common target time-zone.

    The default time-zone applied to the unaware time-input is passed trough
    the constructor. By default the UTC time-zone is used.
    By default the target time-zone is set to None which means that
    the original time-zone is preserved.

    Unlike the `DateTime` this class must be instantiated and it cannot be used
    directly as a data-type.

    Constructor parameters:
        default_tz  default time-zone
        target_tz   optional target time-zone
    """
    def __init__(self, default_tz=DateTime.UTC, target_tz=None):
        self.default_tz = default_tz
        self.target_tz = target_tz

    def set_time_zone(self, value):
        """ Make a date-time value time-zone aware by setting the default
        time-zone and convert the time-zone if the target time-zone is given.
        """
        if value.tzinfo is None:
            value = value.replace(tzinfo=self.default_tz)
        if self.target_tz:
            value = value.astimezone(self.target_tz)
        return value

    def parse(self, raw_value):
        return self.set_time_zone(super(DateTimeTZAware, self).parse(raw_value))

    def encode(self, value):
        return super(DateTimeTZAware, self).encode(self.set_time_zone(value))


# mapping of plain Python types to data type classes
if PY3:

    DTYPES = {
        bytes: String,
        str: String,
        bool: Boolean,
        int: Integer,
        float: Double,
        date: Date,
        datetime: DateTime,
        time: Time,
        timedelta: Duration,
    }
elif PY2:

    DTYPES = {
        str: String,
        unicode: String,
        bool: Boolean,
        int: Integer,
        long: Integer,
        float: Double,
        date: Date,
        datetime: DateTime,
        time: Time,
        timedelta: Duration,
    }
