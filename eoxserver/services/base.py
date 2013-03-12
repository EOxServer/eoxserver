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


logger = logging.getLogger(__name__)

class BaseRequestHandler(object):
    """
    Base class for all EOxServer Handler Implementations.
    
    There are two private methods that have to be overridden by child classes.
    
    .. method:: _handleException(req, exception)
    
        Abstract method which must be overridden by child classes to
        provide specific exception reports. If the exception report
        cannot be generated in this specific handler, the exception
        should be re-raised. This is also the default behaviour.
        
        The method expects an :class:`~.OWSRequest` object ``req`` and
        the exception that has been raised as input. It should return a 
        :class:`~.Response` object containing the exception report.
    
    .. method:: _processRequest(req)

        Abstract method which must be overridden to provide the specific
        request handling logic. Should not be invoked from external code,
        use the :meth:`handle` method instead. It expects an
        :class:`~.OWSRequest` object ``req`` as input and should return a
        :class:`~.Response` object containing the response to the request.
        The default method does not do anything.
    """
    def _handleException(self, req, exception):
        raise
    
    def _processRequest(self, req):
        pass

    def handle(self, req):
        """
        Basic request handling method which should be invoked from
        external code. This method invokes the :meth:`_processRequest` method
        and returns the resulting :class:`~.Response` object unless an
        exception is raised. In the latter case :meth:`_handleException` is
        called and the appropriate response is returned.
        """

        try:
            return self._processRequest(req)
        except Exception, e:
            return self._handleException(req, e)

class BaseExceptionHandler(object):
    """
    This is the basic handler for exceptions. It allows to generate exception
    reports.
    """
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
        logger.error(str(req.getParams()))
        logger.error(str(exception))
        logger.debug(format_exc())

    def _getContentType(self, exception):
        raise InternalError("Not implemented.")
    
    def handleException(self, req, exception):
        """
        This method can be invoked in order to handle an exception and produce
        an exception report. It starts by logging the error to the default
        log. Then the appropriate XML encoder is fetched (the
        :meth:`_getEncoder` method has to be overridden by the subclass).
        Finally, the exception report itself is encoded and the appropriate HTTP
        status code determined. The method returns a :class:`~.Response` object
        containing this information.
        """
        
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
