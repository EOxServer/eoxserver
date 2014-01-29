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


import re
from datetime import datetime, date, time, timedelta

from django.utils.dateparse import parse_date, parse_datetime, parse_time


class Parameter(object):
    def __init__(self, identifier=None, title=None, description=None, 
                 metadata=None):
        self.identifier = identifier
        self.title = title
        self.description = description
        self.metadata = metadata or ()



LITERAL_DATA_NAME = {
    str: "string",
    unicode: "string",
    bool: "boolean",
    int: "integer",
    long: "integer",
    float: "float",
    #complex: "",
    date: "date",
    datetime: "dateTime",
    time: "time",
    timedelta: "duration"
}


def parse_date_ext(raw_value):
    value = parse_date(raw_value)
    if not value:
        raise ValueError("Could not parse ISO date from '%s'." % raw_value)
    return value

def parse_datetime_ext(raw_value):
    value = parse_datetime(raw_value)
    if not value:
        raise ValueError("Could not parse ISO date time from '%s'." % raw_value)
    return value


def parse_time_ext(raw_value):
    value = parse_time(raw_value)
    if not value:
        raise ValueError("Could not parse ISO time from '%s'." % raw_value)
    return value


ISO_8601_DURATION_RE = re.compile(
    r"^(?P<sign>[+-])?P"
    r"(?P<years>\d+Y)?"
    r"(?P<months>\d+M)?"
    r"(?P<days>\d+D)?"
    r"(?P<hours>\d+H)?"
    r"(?P<minutes>\d+M)?"
    r"(?P<seconds>\d+S)?"
    r"$"
)

def parse_timedelta(raw_value):
    match = ISO_8601_DURATION_R.match(raw_value)
    
    if not match:
        raise ValueError("Could not parse ISO duration from '%s'." % raw_value) 

    days = 0
    seconds = 0
    negative = False

    for key, value in match.items():
        if key == "sign" and value == "-":
            negative = True
        elif key == "years":
            days += int(value) * 365
        elif key == "months":
            days += int(value) * 30 #???
        elif key == "days":
            days += int(value)
        elif key == "hours":
            seconds += int(value) * 24 * 60
        elif key == "minutes":
            seconds += int(value) * 60
        elif key == "seconds":
            seconds += int(value)

    dt = timedelta(days, seconds)
    if negative:
        return -dt
    return dt


LITERL_DATA_PARSER = {
    date: parse_date_ext,
    datetime: parse_datetime_ext,
    time: parse_time_ext,
    timedelta: parse_timedelta
}


def is_literal_type(type_):
    return type_ in LITERAL_DATA_NAME


class LiteralData(Parameter):

    def __init__(self, identifier=None, type=str, uoms=None, default=None, 
                 allowed_values=None, values_reference=None, *args, **kwargs):
        super(LiteralData, self).__init__(identifier, *args, **kwargs)
        self.type = type
        self.uoms = uoms or ()
        self.default = default
        self.allowed_values = allowed_values or ()
        self.values_reference = values_reference

    def parse_value(self, raw_value):
        try:
            parser = LITERL_DATA_PARSER.get(self.type, self.type)
            return parser(raw_value)
        except (ValueError, TypeError), e:
            raise Exception("%s: Input parsing error: '%s' (raw value '%s')" % (self.identifier, str(e), raw_value))

    @property
    def type_name(self):
        return LITERAL_DATA_NAME.get(self.type)


class ComplexData(Parameter):
    def __init__(self, identifier=None, formats=None, *args, **kwargs):
        super(ComplexData, self).__init__(identifier, *args, **kwargs)
        self.formats = formats


class BoundingBoxData(Parameter):
    def __init__(self, identifier, *args, **kwargs):
        super(BoundingBoxData, self).__init__(identifier, *args, **kwargs)
        # TODO: CRSs


class Format(object):
    def __init__(self, mime_type, encoding=None, schema=None):
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema
