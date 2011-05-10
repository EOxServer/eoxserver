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

def posListToWkt(pos_list):
    return ",".join("%f %f" % (pos_list[2*c], pos_list[2*c+1]) for c in range(0, len(pos_list) / 2))
