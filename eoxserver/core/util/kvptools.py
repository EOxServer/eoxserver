#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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

"""
This module contains the parameter decoder implementation for
key-value-pair encoded URL parameters. See also
:ref:`module_core_util_decoders` for general information on parameter
decoders.
"""

import re
from cgi import escape, parse_qs
import logging

from django.http import QueryDict

from eoxserver.core.exceptions import (
    InternalError, KVPDecoderException, KVPKeyNotFound,
    KVPKeyOccurrenceError, KVPTypeError
)
from eoxserver.core.util.decoders import Decoder, DecoderInterface

class KVPDecoder(Decoder):
    """
    This class provides a parameter decoder for key-value-pair
    parameters.
    
    See docs/sphinx/en/developers/core/util/kvptools.rst for
    comprehensive documentation.
    """
    def _setParamsDefault(self):
        self.kvp = None
        self.param_dict = None
    
    def setParams(self, params):
        if isinstance(params, QueryDict):
            param_dict = {}
            for key, values in params.lists():
                param_dict[key.lower()] = values
        
        else:
            tmp = parse_qs(params)
            param_dict = {}
            for key, values in tmp.items():
                param_dict[key.lower()] = values
        
        self.kvp = params
        self.param_dict = param_dict
    
    def setSchema(self, schema):
        self.schema = schema
        
    def _getValueDefault(self, key):
        if key.lower() in self.param_dict:
            return self.param_dict[key.lower()][-1]
        else:
            raise KVPKeyNotFound("Could not find KVP key '%s'." % key)
    
    def _getValueSchema(self, key):
        if key in self.schema:
            if "kvp_key" in self.schema[key]:
                kvp_key = self.schema[key]["kvp_key"]
            else:
                raise InternalError("Parameter schema does not contain a 'kvp_key' entry for '%s'" % key)
            
            if "kvp_type" in self.schema[key]:
                type_expr = self.schema[key]["kvp_type"]
            else:
                raise InternalError("Parameter schema does not contain a 'kvp_type' entry for '%s'" % key)
        else:
            raise InternalError("Parameter schema has no entry for key '%s'" % key)
                
        type_name, min_occ, max_occ = self._parseTypeExpression(type_expr)
            
        if kvp_key.lower() in self.param_dict:
            values = self.param_dict[kvp_key.lower()]
        else:
            if min_occ > 0:
                raise KVPKeyNotFound("Parameter with key '%s' not found." % kvp_key)
            else:
                if max_occ <= 1:
                    return None
                else:
                    return []
        
        if len(values) < min_occ:
            raise KVPKeyOccurrenceError("Parameter '%s' expected at least %d times. Found %d occurrences." % (
                kvp_key, min_occ, len(values)
            ))
        elif len(values) > max_occ:
            raise KVPKeyOccurrenceError("Parameter '%s' expected at most %d times. Found %d occurrences." % (
                kvp_key, max_occ, len(values)
            ))
        
        if max_occ > 1:
            return [self._cast(value, type_name) for value in values]
        else:
            if len(values) == 1:
                return self._cast(values[0], type_name)
            else:
                return None
            

    def _cast(self, raw_value, type_name):        
        if type_name == "string":
            return raw_value
        elif type_name == "stringlist":
            return raw_value.split(",")
        elif type_name == "int":
            try:
                return int(raw_value)
            except:
                raise KVPTypeError("Could not convert '%s' to integer." % raw_value)
        elif type_name == "intlist":
            try:
                return [int(i) for i in raw_value.split(",")]
            except:
                raise KVPTypeError("Could not convert '%s' to integer list." % raw_value)
        elif type_name == "float":
            try:
                return float(raw_value)
            except:
                raise KVPTypeError("Could not convert '%s' to float." % raw_value)
        elif type_name == "floatlist":
            try:
                return [float(f) for f in raw_value.split(",")]
            except:
                raise KVPTypeError("Could not convert '%s' to float list." % raw_value)
        else:
            raise InternalError("Unknown KVP item type '%s'" % type_name)
    
    def getParams(self):
        return self.param_dict
    
    def getParamType(self):
        return "kvp"

KVPDecoder = DecoderInterface.implement(KVPDecoder)
