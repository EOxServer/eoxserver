#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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
from datetime import datetime, tzinfo, timedelta

from eoxserver.core.exceptions import InvalidParameterException

# pre-compile the regular expression for date/time matching

date_regex = r"(?P<year>\d{4})[-]?(?P<month>\d{2})[-]?(?P<day>\d{2})"
time_regex = r"(?P<hour>\d{2})(:?(?P<minute>\d{2})(:?(?P<second>\d{2}))?)?"
tz_regex = r"(?P<tz_expr>Z|(?P<tz_sign>[+-])(?P<tz_hours>\d{2}):?(?P<tz_minutes>\d{2})?)?"
datetime_regex = date_regex + r"(T" + time_regex + tz_regex + ")?"

datetime_regex_obj = re.compile(datetime_regex)

class UTCOffsetTimeZoneInfo(tzinfo):
    def __init__(self):
        super(UTCOffsetTimeZoneInfo, self).__init__
        
        self.offset_td = timedelta()
    
    def setOffsets(self, offset_sign, offset_hours, offset_minutes):
        if offset_sign == "+":
            self.offset_td = timedelta(hours = offset_hours, minutes = offset_minutes)
        else:
            self.offset_td = timedelta(hours = -offset_hours, minutes = -offset_minutes)
    
    def utcoffset(self, dt):
        return self.offset_td
    
    def dst(self, dt):
        return timedelta()
    
    def tzname(self, dt):
        return None

def _convert(s):
    if s is None:
        return 0
    else:
        return int(s)

def getDateTime(s):
    match = datetime_regex_obj.match(s)
    if match is None:
        raise InvalidParameterException(
            "'%s' does not match any known datetime format." % s
        )
    
    year = int(match.group("year"))
    month = int(match.group("month"))
    day = int(match.group("day"))
    
    hour = _convert(match.group("hour"))
    minute = _convert(match.group("minute"))
    second = _convert(match.group("second"))
    
    if match.group("tz_expr") in (None, "Z"):
        offset_sign = "+"
        offset_hours = 0
        offset_minutes = 0
    else:
        offset_sign = match.group("tz_sign")
        offset_hours = _convert(match.group("tz_hours"))
        offset_minutes = _convert(match.group("tz_minutes"))
        
    tzi = UTCOffsetTimeZoneInfo()
    tzi.setOffsets(offset_sign, offset_hours, offset_minutes)
    
    try:
        dt = datetime(year, month, day, hour, minute, second, 0, tzi)
    except ValueError:
        raise InvalidParameterException("Invalid date/time '%s'" % s)
    
    utc = UTCOffsetTimeZoneInfo()
    utct = dt.astimezone(utc)
    
    return utct

def isotime(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
