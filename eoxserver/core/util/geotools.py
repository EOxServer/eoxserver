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
import os.path
import xml.dom.minidom
import re
from fnmatch import fnmatch
from datetime import datetime, tzinfo, timedelta
from cgi import escape, parse_qs
from sys import maxint

from django.http import QueryDict

import logging

def getSRIDFromCRSURI(uri):
    match = re.match(r"urn:ogc:def:crs:EPSG:\d*\.?\d*:(\d+)", uri)
    
    if match is not None:
        return int(match.group(1))
    else:
        match = re.match(r"http://www.opengis.net/def/crs/EPSG/\d+\.?\d*/(\d+)", uri)
        
        if match is not None:
            return int(match.group(1))
        else:
            return None

def getSRIDFromCRSIdentifier(identifier):
    ret = getSRIDFromCRSURI(identifier)
    if not ret:
        match = re.match(r"EPSG:(\d*)", identifier, re.I)
        if match is not None:
            return int(match.group(1))
        else:
            return None
    return ret

def posListToWkt(pos_list):
    return ",".join("%f %f" % (pos_list[2*c+1], pos_list[2*c]) for c in range(0, len(pos_list) / 2)) # TODO: Adjust according to axis order of SRID.
