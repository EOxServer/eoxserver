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

class InvalidParameterException(EOxSException):
    pass

class UnknownCRSException(EOxSException):
    pass

class KVPException(EOxSException):
    pass

class XMLException(EOxSException):
    pass

class XMLNodeNotFound(XMLException):
    pass

class XMLContentTypeError(XMLException):
    pass

class XMLEncodingException(XMLException):
    pass

class XMLNodeOccurenceError(XMLException):
    pass
