#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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
