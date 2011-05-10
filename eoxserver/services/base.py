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

import logging

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
        
        @param  req     The {@link eoxserver.lib.requests.EOxSOWSRequest}
                        object that was being processed when the
                        exception was raised
        @param  exception The <tt>Exception</tt> raised by the request
                        handling method
        @return         An {@link eoxserver.lib.requests.EOxSResponse}
                        object containing an exception report
        """
        raise
    
    def _processRequest(self, req):
        """
        Abstract method which must be overridden to provide the specific
        request handling logic. Should not be invoked from external code,
        use the {@link #handle handle} method instead.
        
        @param  req An {@link eoxserver.lib.requests.EOxSOWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.lib.requests.EOxSResponse} object
                    containing the response content, headers and status
        """
        pass

    def handle(self, req):
        """
        Basic request handling method which should be invoked from
        external code.
        
        @param  req An {@link eoxserver.lib.requests.EOxSOWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.lib.requests.EOxSResponse} object
                    containing the response content, headers and status
        """

        try:
            return self._processRequest(req)
        except Exception, e:
            return self._handleException(req, e)

class BaseExceptionHandler(object):
    def _filterExceptions(self, exception):
        raise
    
    def _getEncoder(self):
        raise EOxSInternalError("Not implemented.")
    
    def _getExceptionReport(self, req, exception, encoder):
        if isinstance(exception, EOxSVersionNegotiationException):
            return DOMElementToXML(encoder.encodeVersionNegotiationException(exception))
        elif isinstance(exception, EOxSInvalidRequestException):
            return DOMElementToXML(encoder.encodeInvalidRequestException(exception))
        
    def _getHTTPStatus(self, exception):
        return 400
        
    def _logError(self, req, exception):
        logging.error(str(req.getParams()))
        logging.error(str(exception))
        
    def _getContentType(self, exception):
        raise InternalError("Not implemented.")
    
    def handleException(self, req, exception):
        self._filterExceptions(exception)
        
        encoder = self._getEncoder()
        
        content = self._getExceptionReport(req, exception, encoder)
        status = self._getHTTPStatus(exception)
        
        self._logError(req, exception)
        
        return Response(
            content = content,
            content_type = self._getContentType(exception),
            headers = {},
            status = status
        )
