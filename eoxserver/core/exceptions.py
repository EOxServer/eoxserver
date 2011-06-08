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

class EOxSException(Exception):
    def __init__(self, msg):
        super(EOxSException, self).__init__(msg)
        
        self.msg = msg
    
class InternalError(EOxSException):
    pass

class ConfigError(EOxSException):
    pass

class ImplementationNotFound(EOxSException):
    pass

class ImplementationAmbiguous(EOxSException):
    pass

class ImplementationDisabled(EOxSException):
    pass

class BindingMethodError(EOxSException):
    pass

class TypeMismatch(InternalError):
    pass

class IpcException(EOxSException):
    pass

class UnknownParameterFormatException(EOxSException):
    pass

class MissingParameterException(EOxSException):
    pass

class InvalidParameterException(EOxSException):
    pass

class UnknownCRSException(EOxSException):
    pass

class DecoderException(EOxSException):
    pass

class KVPDecoderException(DecoderException):
    pass

class KVPKeyNotFound(KVPDecoderException, MissingParameterException):
    pass

class KVPKeyOccurrenceError(KVPDecoderException, InvalidParameterException):
    pass

class KVPTypeError(KVPDecoderException, InvalidParameterException):
    pass

class XMLDecoderException(DecoderException):
    pass

class XMLNodeNotFound(XMLDecoderException, MissingParameterException):
    pass

class XMLNodeOccurrenceError(XMLDecoderException, InvalidParameterException):
    pass
    
class XMLTypeError(XMLDecoderException, InvalidParameterException):
    pass

class XMLEncoderException(EOxSException):
    pass

