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
This module contains exception classes used throughout EOxServer.
"""


class EOxSException(Exception):
    """
    Base class for EOxServer exceptions. Expects the error message as its
    single constructor argument.
    """
    
    def __init__(self, msg):
        super(EOxSException, self).__init__(msg)
        
        self.msg = msg
    
class InternalError(EOxSException):
    """
    :exc:`InternalError` shall be raised by EOxServer modules whenever they
    detect a fault that stems from errors in the EOxServer implementation. It
    shall NOT be used for error conditions that are caused by incorrect or
    invalid user or service input or that originate from the individual system
    configuration.
    
    In a web service environment, an :exc:`InternalError` should lead to the
    server responding with a HTTP Status of ``500 INTERNAL SERVER ERROR``.
    """
    
    pass

class ConfigError(EOxSException):
    """
    This exception shall be raised if the system configuration is invalid.
    """
    
    pass

class ImplementationNotFound(EOxSException):
    """
    This exception shall be raised by the registry if an implementation ID is
    not found.
    """
    pass

class ImplementationAmbiguous(EOxSException):
    """
    This exception shall be raised by the registry if the input data matches
    more than one implementation.
    """
    
    pass

class ImplementationDisabled(EOxSException):
    """
    This exception shall be raised by the registry if the requested
    implementation is disabled.
    """
    
    pass

class BindingMethodError(EOxSException):
    """
    This exception shall be raised by the registry if it cannot bind to
    implementations of a given interface because the binding method does not
    allow it.
    """
    
    pass

class TypeMismatch(InternalError):
    """
    This exception shall be raised by interfaces in case they detect that
    an implementation method has been called within an argument of the wrong
    type.
    """
    
    pass

class InvalidExpressionError(EOxSException):
    """
    This exception shall be raised if a filter expression statement is invalid,
    e.g. because of incorrect operands.
    """

    pass

class UnknownAttribute(EOxSException):
    """
    This exception shall be raised if an unknown or invalid attribute is
    requested from a resource.
    """
    
    pass
    
class IDInUse(EOxSException):
    """
    This exception shall be raised if a requested unique ID is already in use.
    """
    
    pass
    
class UniquenessViolation(EOxSException):
    """
    This excetion shall be raised if a database record cannot be created due
    to uniqueness constraints.
    """
    
    pass

class IpcException(EOxSException):
    """
    This exception shall be raised in case of communication faults in the IPC
    system.
    """
    
    pass

class UnknownParameterFormatException(EOxSException):
    """
    This exception shall be raised if a parameter is not in the format
    expected by the implementation.
    """
    pass

class MissingParameterException(EOxSException):
    """
    This exception shall be raised if an expected parameter is not found.
    """
    pass

class InvalidParameterException(EOxSException):
    """
    This exception shall be raised if a parameter is found to be invalid.
    """
    pass

class DecoderException(EOxSException):
    """
    This is the base class for exceptions raised by decoders as defined in
    :mod:`eoxserver.core.util.decoders`.
    """
    pass

class KVPDecoderException(DecoderException):
    """
    This is the base class for exceptions raised by the KVP decoder.
    """
    pass

class KVPKeyNotFound(KVPDecoderException, MissingParameterException):
    """
    This exception shall be raised if the KVP decoder does not encounter a
    given key. It inherits from :exc:`KVPDecoderException` and
    :exc:`MissingParameterException`.
    """
    
    pass

class KVPKeyOccurrenceError(KVPDecoderException, InvalidParameterException):
    """
    This exception shall be raised if the number of occurrences of a given
    KVP key does not lay within the occurrence range defined by the applicable
    decoding schema. It inherits from :exc:`KVPDecoderException` and
    :exc:`InvalidParameterException`.
    """
    
    pass

class KVPTypeError(KVPDecoderException, InvalidParameterException):
    """
    This exception shall be raised if the requested KVP value is of another
    type than defined in the decoding schema. It inherits from
    :exc:`KVPDecoderException` and :exc:`InvalidParameterException`.
    """
    
    pass

class XMLDecoderException(DecoderException):
    """
    This is the base class for exceptions raised by the XML decoder.
    """
    
    pass

class XMLNodeNotFound(XMLDecoderException, MissingParameterException):
    """
    This exception shall be raised if the XML decoder does not encounter a
    given XML node. It inherits from :exc:`XMLDecoderException` and
    :exc:`MissingParameterException`.
    """
    
    pass

class XMLNodeOccurrenceError(XMLDecoderException, InvalidParameterException):
    """
    This exception shall be raised if the number of occurrences of a given
    XML node does not lay within the occurrence range defined by the applicable
    decoding schema. It inherits from :exc:`XMLDecoderException` and
    :exc:`InvalidParameterException`.
    """
    
    pass
    
class XMLTypeError(XMLDecoderException, InvalidParameterException):
    """
    This exception shall be raised if the requested XML node value is of another
    type than defined in the decoding schema. It inherits from
    :exc:`XMLDecoderException` and :exc:`InvalidParameterException`.
    """
    
    pass

class XMLEncoderException(EOxSException):
    """
    This exception shall be raised if the XML encoder finds an error in an
    encoding schema.
    """
    
    pass

class FactoryQueryAmbiguous(EOxSException):
    """
    This exception shall be raised when ... TODO
    """
    pass
