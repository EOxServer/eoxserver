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
from django.utils.tzinfo import FixedOffset

from eoxserver.core.util.timetools import isoformat, parse_duration


class BaseType(object):
    """ Base literal data type class.
        This class defines the class interface.
    """
    name = None # to be replaced by a name
    dtype = str # to be replaced by a proper type
    zero = None # when applicable to be replaced by a proper zero value
    comparable = True # indicate whether the type can be compared (<,>,==)

    @classmethod
    def parse(cls, raw_value):
        """ Cast or parse input to its proper represenation."""
        return cls.dtype(raw_value)

    @classmethod
    def encode(cls, value):
        """ Encode value to a unicode string."""
        return unicode(value)

    @classmethod
    def get_diff_dtype(cls): # difference type - change if differs from the base
        """ Get type of the differece of this type.
            E.g., `timedelta` for a `datetime`.
        """
        return cls

    @classmethod
    def as_number(cls, value):
        """ convert to a number (e.g., duration)"""
        raise TypeError("Data type %s cannot be converted to a number!" % cls)

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        raise TypeError("Data type %s cannot be substracted!" % cls)


class Boolean(BaseType):
    name = "boolean"
    dtype = bool

    @classmethod
    def parse(cls, raw_value):
        if isinstance(raw_value, basestring):
            raw_value = unicode(raw_value.lower())
            if raw_value in ('1', 'true'):
                return True
            elif raw_value in ('0', 'false'):
                return False
            else:
                raise ValueError("Cannot parse boolean value '%s'!"%raw_value)
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
        """ substract value0 - value1 """
        return value0 - value1


class Integer(BaseType):
    name = "integer"
    dtype = int
    zero = 0

    @classmethod
    def encode(cls, value):
        """ Encode value to a unicode string."""
        return unicode(int(value))

    @classmethod
    def as_number(cls, value):
        return value

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        return value0 - value1


class Double(BaseType):
    name = "double"
    dtype = float
    zero = 0.0

    @classmethod
    def encode(cls, value):
        return u"%.15g"%cls.dtype(value)

    @classmethod
    def as_number(cls, value):
        return value

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        return value0 - value1


class String(BaseType):
    name = "string"
    dtype = unicode
    encoding = 'utf-8'
    comparable = False # disabled although Python implements comarable strings

    @classmethod
    def encode(cls, value):
        """ Encode value to a unicode string."""
        try:
            return unicode(value)
        except UnicodeDecodeError:
            return unicode(value, cls.encoding)

    @classmethod
    def parse(cls, raw_value):
        return cls.dtype(raw_value)

    @classmethod
    def get_diff_dtype(cls): # string has no difference
        return None


class Duration(BaseType):
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
            raise ValueError("Invalid value type '%s'!"%type(value))
        items = []
        if value.days < 0:
            items.append('-')
            value = -value
        items.append('P')
        if value.days != 0:
            items.append('%dD'%value.days)
        elif value.seconds == 0 and value.microseconds == 0:
            items.append('T0S') # zero interaval
        if value.seconds != 0 or value.microseconds != 0:
            minutes, seconds = divmod(value.seconds, 60)
            hours, minutes = divmod(minutes, 60)
            items.append('T')
            if hours != 0:
                items.append('%dH'%hours)
            if minutes != 0:
                items.append('%dM'%minutes)
            if value.microseconds != 0:
                items.append("%.6fS"%(seconds+1e-6*value.microseconds))
            elif seconds != 0:
                items.append('%dS'%seconds)

        return unicode("".join(items))

    @classmethod
    def as_number(cls, value):
        return 86400.0*value.days + 1.0*value.seconds + 1e-6*value.microseconds

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        return value0 - value1


class Date(BaseType):
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
        raise ValueError("Could not parse ISO date from '%s'."%raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return unicode(value.isoformat())
        raise ValueError("Invalid value type '%s'!"%type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        return value0 - value1


class Time(BaseType):
    name = "time"
    dtype = time
    # TODO: proper time-zone handling

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
        raise ValueError("Could not parse ISO time from '%s'."%raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return unicode(value.isoformat())
        raise ValueError("Invalid value type '%s'!"%type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        aux_date = datetime.now().date()
        dt0 = datetime.combine(aux_date, value0)
        dt1 = datetime.combine(aux_date, value1)
        return dt0 - dt1


class DateTime(BaseType):
    name = "dateTime"
    dtype = datetime

    # tzinfo helpers
    UTC = utc               # zulu-time TZ instance
    TZOffset = FixedOffset  # fixed TZ offset class, set mintues to instantiate

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
        raise ValueError("Could not parse ISO date-time from '%s'."%raw_value)

    @classmethod
    def encode(cls, value):
        if isinstance(value, cls.dtype):
            return unicode(isoformat(value))
        raise ValueError("Invalid value type '%s'!"%type(value))

    @classmethod
    def sub(cls, value0, value1):
        """ substract value0 - value1 """
        return value0 - value1


# mapping of plain Python types to data type classes
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
