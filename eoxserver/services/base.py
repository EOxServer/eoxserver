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

from traceback import format_exc
import logging

from django.conf import settings

from eoxserver.core.exceptions import InternalError
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.services.requests import Response
from eoxserver.services.exceptions import (
    InvalidRequestException, VersionNegotiationException
)

class BaseRequestHandler(object):
    """
    Base class for all EOxServer Handler Implementations.
    """
    def _handleException(self, req, exception):
        """
        Abstract method which must be overridden by child classes to
        provide specific exception reports. If the exception report
        cannot be generated in this specific handler, the exception
        should be re-raised. This is also the default behaviour.
        
        @param  req     The {@link eoxserver.services.requests.OWSRequest}
                        object that was being processed when the
                        exception was raised
        @param  exception The <tt>Exception</tt> raised by the request
                        handling method
        @return         An {@link eoxserver.services.requests.Response}
                        object containing an exception report
        """
        raise
    
    def _processRequest(self, req):
        """
        Abstract method which must be overridden to provide the specific
        request handling logic. Should not be invoked from external code,
        use the {@link #handle handle} method instead.
        
        @param  req An {@link eoxserver.services.requests.OWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.services.requests.Response} object
                    containing the response content, headers and status
        """
        pass

    def handle(self, req):
        """
        Basic request handling method which should be invoked from
        external code.
        
        @param  req An {@link eoxserver.services.requests.OWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.services.requests.Response} object
                    containing the response content, headers and status
        """

        try:
            return self._processRequest(req)
        except Exception, e:
            return self._handleException(req, e)

class BaseExceptionHandler(object):
    def __init__(self, schemas=None):
        self.schemas = schemas
    
    def _filterExceptions(self, exception):
        raise
    
    def _getEncoder(self):
        raise InternalError("Not implemented.")
    
    def _getExceptionReport(self, req, exception, encoder):
        if isinstance(exception, VersionNegotiationException):
            return DOMElementToXML(encoder.encodeVersionNegotiationException(exception))
        elif isinstance(exception, InvalidRequestException):
            return DOMElementToXML(encoder.encodeInvalidRequestException(exception))
        else:
            return DOMElementToXML(encoder.encodeException(exception))
        
    def _getHTTPStatus(self, exception):
        return 400
        
    def _logError(self, req, exception):
        logging.error(str(req.getParams()))
        logging.error(str(exception))
        if settings.DEBUG:
            logging.error(format_exc())

    def _getContentType(self, exception):
        raise InternalError("Not implemented.")
    
    def handleException(self, req, exception):
        self._logError(req, exception)
        
        if settings.DEBUG:
            self._filterExceptions(exception)
        
        encoder = self._getEncoder()
        
        content = self._getExceptionReport(req, exception, encoder)
        
        status = self._getHTTPStatus(exception)
        
        return Response(
            content = content,
            content_type = self._getContentType(exception),
            headers = {},
            status = status
        )
