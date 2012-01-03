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

import os
import re
from datetime import datetime, tzinfo, timedelta

from eoxserver.core.exceptions import InvalidParameterException

import logging

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

def getDateTime(s):
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})(T(\d{2}):(\d{2}):(\d{2})(Z|([+-])(\d{2}):?(\d{2})?)?)?", s)
    if match is None:
        raise UnknownParameterFormatException("'%s' does not match any known datetime format." % s)
    
    year = int(match.group(1))
    month = int(match.group(2))
    day = int(match.group(3))
    
    if match.group(4) is None:
        hour = 0
        minute = 0
        second = 0
        offset_sign = "+"
        offset_hours = 0
        offset_minutes = 0
    else:
        hour = int(match.group(5))
        minute = int(match.group(6))
        second = int(match.group(7))
        
        if match.group(8) is None or match.group(8) == "Z":
            offset_sign = "+"
            offset_hours = 0
            offset_minutes = 0
        else:
            offset_sign = match.group(9)
            offset_hours = int(match.group(10))
            if match.group(11) is None:
                offset_minutes = 0
            else:
                offset_minutes = int(match.group(11))
    
    tzi = UTCOffsetTimeZoneInfo()
    tzi.setOffsets(offset_sign, offset_hours, offset_minutes)
    
    try:
        dt = datetime(year, month, day, hour, minute, second, 0, tzi)
    except ValueError, e:
        raise InvalidParameterException("Invalid date/time '%s'" % s)
    
    utc = UTCOffsetTimeZoneInfo()
    utct = dt.astimezone(utc)
    
    #logging.debug("Original datetime: %s" % dt.strftime("%Y-%m-%dT%H:%M:%S"))
    #logging.debug("UTC Offset: %s" % str(dt.utcoffset()))
    #logging.debug("offset_sign: %s, offset_hours: %d, offset_minutes: %d" % (offset_sign, offset_hours, offset_minutes))
    #logging.debug("UTC Time: %s" % utct.strftime("%Y-%m-%dT%H:%M:%S"))
    
    return utct

def isotime(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
