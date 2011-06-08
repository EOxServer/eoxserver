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
This module contains interfaces and partial implementations for 
parameter decoding. These classes are primarily intended for OWS request
parsing, therefore there are currently two concrete implementations:

* :class:`~.KVPDecoder` which provides KVP parameter parsing and
* :class:`~.XMLDecoder` for XML input parsing

"""

import re
from sys import maxint

from eoxserver.core.interfaces import *
from eoxserver.core.exceptions import (
    InternalError, MissingParameterException
)

# see docs/sphinx/en/developers/core/util/decoders.rst for more
# documentation, especially on schemas

class DecoderInterface(Interface):
    """
    This is the common interface for request parameter decoding.
    
    .. method:: setParams(params)
    
       This method shall set the parameters object to be parsed by the
       decoder implementation
    
    .. method:: setSchema(schema)
    
       This method shall set the schema used by the decoder instance for
       parsing the parameters object. The input is expected to be a
       dictionary that represents the schema.
       
    .. method:: getValueStrict(expr)
    
       This method shall return a parameter value according to the
       expression ``expr``.
    
       :exc:`~.MissingParameterException` or one of its descendants
       shall be raised if the requested value could not be found in the
       parameters.
    
       :exc:`~.InvalidParameterException` or one of its descendants
       shall be raised if:
       
       * the requested value could not be converted to the expected type
       * the occurrence bounds given by the schema are violated
       * some other validation of the content defined in the schema
         fails
    
       :exc:`~.InternalError` shall be raised in case the expression
       ``expr`` is invalid.
    
    .. method:: getValue(expr, default=None)
    
       This method shall return a parameter value according to the
       expression ``expr``.
    
       It shall the optional ``default`` value or ``None`` if the
       requested value could not be found in the parameters.
    
       :exc:`~.InvalidParameterException` or one of its descendants
       shall be raised if:
       
       * the requested value cannot be converted to the expected type
       * the occurrence bounds given by the schema are violated
       * some other validation of the content defined in the schema
         fails
    
    .. method:: getParams()
    
       This method shall return the parameters object the decoder is
       parsing.
    
    .. method:: getParamType()
    
       This method shall return the a significative code for the type
       of parameters the decoder is operating on.
    """
    
    
    setParams = Method(
        Arg("params")
    )
    
    setSchema = Method(
        DictArg("schema")
    )
    
    getValueStrict = Method(
        StringArg("expr"),
        returns=Arg("@return")
    )
    
    getValue = Method(
        StringArg("expr"),
        Arg("default", default=None),
        returns=Arg("@return")
    )

    getParams = Method(
        returns=Arg("@return")
    )

    getParamType = Method(
        returns=StringArg("@return")
    )

class Decoder(object):
    """
    This is a partial implementation of the DecoderInterface which 
    defines the basic structure of parameter decoders. It
    provides canonical implementations of
    :meth:`~.Decoder.getValueStrict`, :meth:`~.Decoder.getValue` and
    the constructor as well as private methods for schema parsing
    support.
    """
    
    def __init__(self, params=None, schema=None):
        """
        The constructor accepts two optional parameters: ``params``
        and ``schema``. ``params`` is expected to be the object to be
        parsed by the decoder. Which objects can be parsed is defined
        by the concrete implementations. ``schema`` represents a
        parameter schema.
        """
        
        if params is not None:
            self.setParams(params)
        else:
            self._setParamsDefault()
        
        if schema is not None:
            self.setSchema(schema)
        else:
            self._setSchemaDefault()
    
    def _setParamsDefault(self):
        """
        This method is invoked if no params are provided to the
        constructor. It must be overridden by implementations; it raises
        :exc:`~.InternalError` by default.
        """
        raise InternalError("Not implemented.")
    
    def _setSchemaDefault(self):
        """
        This method is invoked if no schema is provided to the
        constructor. It can be overridden by implementations
        """
        self.schema = None
    
    def setParams(self, params):
        """
        This method is required by the interface definition. It shall
        set the parameters object to be parsed by the decoder. It may
        also validate and prepare parsing of the input. It must
        be overridden by the concrete implementations;
        :exc:`~.InternalError` is raised by
        default.
        """
        raise InternalError("Not implemented.")
    
    def setSchema(self, schema):
        """
        This method is required by the interface definition. It shall
        set the schema used for parsing. It can be overidden by the
        implementations in order to validate and parse he schema.
        """
        self.schema = schema
    
    def getValueStrict(self, expr):
        """
        This method is required by the interface definition. It
        returns the parsing result for the given expression ``expr``.
        Any occurring exceptions will be passed on to the caller.
        
        The method invokes either :meth:`_getValueSchema` if a schema
        has been defined or :meth:`_getValueDefault` otherwise.
        """
        if self.schema is None:
            return self._getValueDefault(expr)
        else:
            return self._getValueSchema(expr)
    
    def getValue(self, expr, default=None):
        """
        This method is required by the interface definition. It invokes
        :meth:`getValueStrict`, but returns ``None`` or an optional
        default value in case the parameter is not found.
        """
        
        try:
            value = self.getValueStrict(expr)
            if value is None:
                return default
            else:
                return value
        except MissingParameterException:
            return default
    
    def getParams(self):
        """
        This method is required by the interface definition. It shall
        return the parameters object the decoder implementation is
        parsing. It must be overridden by concrete implementations. It
        raises :exc:`~.InternalError` by default.
        """
        raise InternalError("Not implemented.")
    
    def getParamType(self):
        """
        This method is required by the interface definition. It shall
        return a significative code for the type of parameters the
        decoder is operating on. It must be overridden by concrete
        implementations. It raises :exc:`~.InternalError` by default.
        """
            
    def _getValueDefault(self, expr):
        """
        This method is expected to implement the default behaviour of
        the implementation, if any. Default in this context means, that
        no schema is present. The method must be overridden by
        concrete implementations. It raises :exc:`~.InternalError` by
        default.
        """
        raise InternalError("Not implemented.")
        
    def _getValueSchema(self, expr):
        """
        This method is expected to implement parameter parsing according
        to a given schema. It must be overridden by concrete
        implementations. It raises :exc:`~.InternalError` by default.
        """
        raise InternalError("Not implemented.")

    def _parseTypeExpression(self, type_expr):
        """
        This method parses a type expression conveyed with a schema. It
        accepts a string ``type_expr`` as input and returns a triple of
        ``(type, min_occ, max_occ)`` where ``type`` is a string
        containing the base type name, ``min_occ`` and ``max_occ`` are
        integers denoting the minimum and maximum occurrences of the
        object respectively.
        
        This method fails with :exc:`~.InternalError` if the type
        expression could not be parsed.
        """
        
        match = re.match(r'([A-Za-z]+)(\[(\d+)?(:(\d+)?)?\])?', type_expr)
        
        if match is None:
            raise InternalError("Invalid decoding schema type expression '%s'" % type_expr)
        
        type_expr = match.group(1)
        
        if match.group(2):
            if match.group(3) and match.group(5):
                min_occ = int(match.group(3))
                max_occ = int(match.group(5))
            elif match.group(3) and match.group(4):
                min_occ = int(match.group(3))
                max_occ = maxint
            elif match.group(3):
                min_occ = int(match.group(3))
                max_occ = min_occ
            elif match.group(5):
                min_occ = 0
                max_occ = int(match.group(5))
            else:
                min_occ = 0
                max_occ = maxint
        else:
            min_occ = 1
            max_occ = 1
        
        return (type_expr, min_occ, max_occ)
