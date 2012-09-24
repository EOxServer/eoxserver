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
This module defines interfaces for service request handlers.

EOxServer follows a cascaded approach for handling OWS requests: First, a
service handler takes in all requests for a specific service, e.g. WMS or WCS.
Second, the request gets passed on to the appropriate version handler. Last,
the actual operation handler for that request is invoked.

This cascaded approach shall ensure that features that relate to every operation
of a service or service version (most importantly exception handling) can be
implemented centrally.
"""

from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface
from eoxserver.services.requests import OWSRequest, Response

class RequestHandlerInterface(RegisteredInterface):
    """
    This is the basic interface for OWS request handling. It is the parent
    class of the other handler interfaces. The binding method is KVP. The
    interface does not define any keys though, which is done by the child
    classes.
    
    .. method:: handle(req)
    
        This method shall be called for handling the request. It expects an
        :class:`~.OWSRequest` object as input ``req`` and shall return a
        :class:`~.Response` object.
    
    """
    REGISTRY_CONF = {
        "name": "Request Handler Interface",
        "intf_id": "services.interfaces.RequestHandler",
        "binding_method": "kvp",
        "registry_keys": ()
    }
    
    handle = Method(
        ObjectArg("req", arg_class=OWSRequest),
        returns = ObjectArg("@return", arg_class=Response)
    )

class ServiceHandlerInterface(RequestHandlerInterface):
    """
    This interface inherits from :class:`RequestHandlerInterface`. It adds
    no methods, but a registry key ``services.interfaces.service`` which
    allows to bind to an implementation given the name of the service.
    """
    REGISTRY_CONF = {
        "name": "Service Handler Interface",
        "intf_id": "services.interfaces.ServiceHandler",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.service",
        )
    }

class VersionHandlerInterface(RequestHandlerInterface):
    """
    This interface inherits from :class:`RequestHandlerInterface`. It adds
    no methods, but the registry keys ``services.interfaces.service`` and 
    ``services.interface.version`` which allow to bind to an implementation
    given the name of the service and the version descriptor.
    """

    REGISTRY_CONF = {
        "name": "Service Handler Interface",
        "intf_id": "services.interfaces.VersionHandler",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.service",
            "services.interfaces.version"
        )
    }

class OperationHandlerInterface(RequestHandlerInterface):
    """
    This interface inherits from :class:`RequestHandlerInterface`. It adds
    no methods, but the registry keys ``services.interfaces.service``, 
    ``services.interface.version`` and ``services.interfaces.operation`` which
    allow to bind to an implementation given the name of the service, the
    version descriptor and the operation name.
    """

    REGISTRY_CONF = {
        "name": "Service Handler Interface",
        "intf_id": "services.interfaces.OperationHandler",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.service",
            "services.interfaces.version",
            "services.interfaces.operation"
        )
    }

class ExceptionHandlerInterface(RegisteredInterface):
    """
    This interface is intended for exception handlers. These handlers shall
    be invoked when an exception is raised during the processing of an OWS
    request.
    
    .. method:: handleException(req, exception)
    
        This method shall handle an exception. It expects the original
        :class:`~.OWSRequest` object ``req`` as well as the exception object as
        input. The expected output is a :class:`~.Response` object which shall
        contain an exception report and whose content will be sent to the client.
        
        In case the exception handler does not recognize a given type of exception
        or cannot produce an appropriate exception report, the exception shall
        be re-raised.
    """
    REGISTRY_CONF = {
        "name": "Exception Handler Interface",
        "intf_id": "services.interfaces.ExceptionHandler",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.exception_scheme",
        )
    }
    
    handleException = Method(
        ObjectArg("req", arg_class=OWSRequest),
        ObjectArg("exception", arg_class=Exception),
        returns = ObjectArg("@return", arg_class=Response)
    )

class ExceptionEncoderInterface(RegisteredInterface):
    """
    This interface is intended for encoding OWS exception reports.
    
    .. method:: encodeInvalidRequestException(exception)
    
        This method shall return an exception report for an
        :class:`~.InvalidRequestException`.
    
    .. method:: encodeVersionNegotiationException(exception)
    
        This method shall return an exception report for a
        :class:`~.VersionNegotiationException`.
    
    .. method:: encodeException(exception)
    
        This method shall return an exception report for any kind of exception.    
    """
    REGISTRY_CONF = {
        "name": "OWS Exception Report XML Encoder Interface",
        "intf_id": "services.interfaces.ExceptionEncoder",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.exception_scheme",
        )
    }
    
    encodeInvalidRequestException = Method(
        ObjectArg("exception", arg_class=Exception),
        returns = StringArg("@return")
    )
    
    encodeVersionNegotiationException = Method(
        ObjectArg("exception", arg_class=Exception),
        returns = StringArg("@return")
    )

    encodeException = Method(
        ObjectArg("exception", arg_class=Exception),
        returns = StringArg("@return")
    )
