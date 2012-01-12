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

from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface
from eoxserver.services.requests import OWSRequest, Response

class RequestHandlerInterface(RegisteredInterface):
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
    REGISTRY_CONF = {
        "name": "Service Handler Interface",
        "intf_id": "services.interfaces.ServiceHandler",
        "binding_method": "kvp",
        "registry_keys": (
            "services.interfaces.service",
        )
    }

class VersionHandlerInterface(RequestHandlerInterface):
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
