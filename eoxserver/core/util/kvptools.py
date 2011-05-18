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

from eoxserver.core.exceptions import (InternalError, KVPException,
    XMLException, XMLNodeNotFound, XMLContentTypeError,
    UnknownParameterFormatException, XMLEncodingException,
    XMLNodeOccurenceError
)

import logging

class KVPDecoder(object):
    def __init__(self, kvp, schema=None):
        super(KVPDecoder, self).__init__()
        
        self.kvp = kvp
        self.schema = schema
        
        self.param_dict = self._getParamDict()
        
    def _getParamDict(self):
        if isinstance(self.kvp, QueryDict):
            param_dict = {}
            for key, values in self.kvp.lists():
                param_dict[key.lower()] = values
        
        else:
            tmp = parse_qs(self.kvp)
            param_dict = {}
            for key, values in tmp.items():
                param_dict[key.lower()] = values
        
        return param_dict
    
    def setSchema(self, schema):
        self.schema = schema
        
    def _getValueDefault(self, key):
        if key.lower() in self.param_dict:
            return self.param_dict[key.lower()][-1]
        else:
            return None
    
    def _getValueSchema(self, key):
        if key in self.schema:
            if "kvp_key" in self.schema[key]:
                kvp_key = self.schema[key]["kvp_key"]
            else:
                kvp_key = key
            
            if "kvp_type" in self.schema[key]:
                kvp_type = self.schema[key]["kvp_type"]
            else:
                kvp_type = "string"
            
            if kvp_key.lower() in self.param_dict:
                values = self.param_dict[kvp_key.lower()]
                
                if kvp_type.endswith("[]"):
                    if kvp_type == "string[]":
                        return values
                    elif kvp_type == "int[]":
                        return [int(value) for value in values]
                    elif kvp_type == "float[]":
                        return [float(value) for value in values]
                    else:
                        raise InternalError("Unknown KVP Item Type '%s'." % kvp_type)
                else:
                    if len(values) > 1:
                        raise KVPException("Ambiguous result for KVP key '%s'. Single occurence expected." % kvp_key)
                    else:
                        raw_value = values[0]
                    
                        if kvp_type == "string":
                            return raw_value
                        elif kvp_type == "stringlist":
                            return raw_value.split(",")
                        elif kvp_type == "int":
                            return int(raw_value)
                        elif kvp_type == "intlist":
                            return [int(i) for i in raw_value.split(",")]
                        elif kvp_type == "float":
                            return float(raw_value)
                        elif kvp_type == "floatlist":
                            return [float(f) for f in raw_value.split(",")]
                        else:
                            raise InternalError("Unknown KVP item type '%s'" % kvp_type)
            else:
                return None
            
        else:
            return None
        
    def getValue(self, key):
        if self.schema is None:
            return self._getValueDefault(key)
        else:
            return self._getValueSchema(key)
    
    def getParams(self):
        return self.param_dict
    
    def getParamType(self):
        return "kvp"
