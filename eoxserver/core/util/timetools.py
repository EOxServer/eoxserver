#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import os
import re
from datetime import datetime, tzinfo, timedelta

from eoxserver.core.exceptions import UnknownParameterFormatException

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
        raise UnknownParameterFormatException("Invalid date/time '%s'" % s) # TODO: change to InvalidParameterException
    
    utc = UTCOffsetTimeZoneInfo()
    utct = dt.astimezone(utc)
    
    #logging.debug("Original datetime: %s" % dt.strftime("%Y-%m-%dT%H:%M:%S"))
    #logging.debug("UTC Offset: %s" % str(dt.utcoffset()))
    #logging.debug("offset_sign: %s, offset_hours: %d, offset_minutes: %d" % (offset_sign, offset_hours, offset_minutes))
    #logging.debug("UTC Time: %s" % utct.strftime("%Y-%m-%dT%H:%M:%S"))
    
    return utct

def isotime(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
