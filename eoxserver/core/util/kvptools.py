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

"""
This module contains the parameter decoder implementation for
key-value-pair encoded URL parameters. See also
:ref:`module_core_util_decoders` for general information on parameter
decoders.
"""

from cgi import parse_qs

from django.http import QueryDict

from eoxserver.core.exceptions import (
    InternalError, KVPKeyNotFound,
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
