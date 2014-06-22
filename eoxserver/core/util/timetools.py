#-------------------------------------------------------------------------------
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

from datetime import datetime 

from django.utils.timezone import utc, make_aware, is_aware
from django.utils.dateparse import parse_datetime, parse_date


def isoformat(dt):
    """ Formats a datetime object to an ISO string. Timezone naive datetimes are
        are treated as UTC Zulu. UTC Zulu is expressed with the proper "Z" 
        ending and not with the "+00:00" offset declaration.
    """
    if not dt.utcoffset():
        dt = dt.replace(tzinfo=None)
        return dt.isoformat("T") + "Z"
    return dt.isoformat("T")


def parse_iso8601(value):
    """ Parses an ISO 8601 date or datetime string to a python date or datetime.
        Raises a `ValueError` if a conversion was not possible. The returned 
        datetime is always considered time-zone aware and defaulting to UTC 
        Zulu.
    """

    for parser in (parse_datetime, parse_date):
        try:
            temporal = parser(value)
        except Exception, e:
            raise ValueError(
                "Could not parse '%s' to a temporal value. "
                "Error was: %s" % (value, e)
            )
        if temporal:
            # convert to datetime if necessary
            if not isinstance(temporal, datetime):
                temporal = datetime.combine(temporal, datetime.min.time())

            # use UTC, if the datetime is not already time-zone aware
            if not is_aware(temporal):
                temporal = make_aware(temporal, utc)
            
            return temporal

    raise ValueError("Could not parse '%s' to a temporal value" % value)
