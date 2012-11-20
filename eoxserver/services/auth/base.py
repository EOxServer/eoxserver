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
This module contains basic classes and functions for the security layer (which
is integrated in the service layer for now).
"""

import logging

from eoxserver.core.system import System
from eoxserver.core.interfaces import Method, ObjectArg
from eoxserver.core.registry import RegisteredInterface
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.services.requests import OWSRequest, Response
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.services.owscommon import OWSCommonExceptionHandler, OWSCommonExceptionEncoder


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Config reader
#-------------------------------------------------------------------------------

class AuthConfigReader(object):
    REGISTRY_CONF = {
        "name": "Authorization Config Reader",
        "impl_id": "services.auth.base.AuthConfigReader"
    }

    def validate(self, config):
        pass

    def getAttributeMappingDictionary(self):
        return \
            System.getConfig().getConfigValue("services.auth.base", "attribute_mapping")

    def getAuthorisationServiceURL(self):
        return \
            System.getConfig().getConfigValue("services.auth.base", "authz_service")

    def getServiceID(self):
        return \
            System.getConfig().getConfigValue("services.auth.base", "serviceID")

    def getAllowLocal(self):
        if System.getConfig().getConfigValue("services.auth.base", "allowLocal") == 'True':
            return True
        return False

    def getPDPType(self):
        return \
            System.getConfig().getConfigValue("services.auth.base", "pdp_type")

AuthConfigReaderImplementation = \
ConfigReaderInterface.implement(AuthConfigReader)


#-------------------------------------------------------------------------------
# AuthorizationResponse
#-------------------------------------------------------------------------------

class AuthorizationResponse(Response):
    """
    A simple base class that contains a response text, content type, headers
    and status, as well as an ``authorized`` flag. It inherits from
    :class:`~.Response`.
    """

    def __init__(self, content='', content_type='text/xml', headers={}, status=None, authorized=False):
        super(AuthorizationResponse, self).__init__(
            content, content_type, headers, status
        )

        self.authorized = authorized

#-------------------------------------------------------------------------------
# PDP Interface
#-------------------------------------------------------------------------------

class PolicyDecisionPointInterface(RegisteredInterface):
    """
    This is the interface for Policy Decision Point (PDP) implementations.

    .. method:: authorize(ows_req)

       This method takes an :class:`~.OWSRequest` object as input and returns an
       :class:`~.AuthorizationResponse` instance. It is expected to check if
       the authenticated user (if any) is authorized to access the requested
       resource and set the ``authorized`` flag of the response accordingly.

       In case the user is not authorized, the content and status of the
       response shall be filled with an error message and the appropriate
       HTTP Status Code (403).

       The method shall not raise any exceptions.
    """

    REGISTRY_CONF = {
        "name": "Policy Decision Point Interface",
        "intf_id": "services.auth.base.PolicyDecisionPointInterface",
        "binding_method": "kvp",
        "registry_keys": (
            "services.auth.base.pdp_type",
        )
    }

    authorize = Method(
        ObjectArg("ows_req", arg_class=OWSRequest),
        returns = ObjectArg("@return", arg_class=AuthorizationResponse)
    )

#-------------------------------------------------------------------------------
# PDP Base Class
#-------------------------------------------------------------------------------

class BasePDP(object):
    """
    This is the base class for PDP implementations. It provides a skeleton for
    authorization request handling.
    """

    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }


    def authorize(self, ows_req):
        """
        This method handles authorization requests according to the
        requirements given in the :class:`PolicyDecisionPointInterface`
        declaration.

        Internally, it invokes the :meth:`_decide` method that implements the
        actual authorization decision logic.
        """

        ows_req.setSchema(self.PARAM_SCHEMA)

        # This code segment allows local clients bypassing the
        # Authorisation process.
        if (AuthConfigReader().getAllowLocal()):
            remoteAddress = ows_req.http_req.META['REMOTE_ADDR']
            # Check all possibilities, also IPv6
            if remoteAddress == '127.0.0.1' or \
               remoteAddress == 'localhost' or \
               remoteAddress == '::1' :
                return AuthorizationResponse(authorized = True)

        schemas = {
            "http://www.opengis.net/ows/2.0": "http://schemas.opengis.net/ows/2.0/owsAll.xsd"
        }
        try:
            authorized, message = self._decide(ows_req)
            if authorized:
                return AuthorizationResponse(authorized = True)
            else:
                return AuthorizationResponse(
                    content = DOMElementToXML(
                                    OWSCommonExceptionEncoder(schemas).encodeExceptionReport(
                                        message, "AccessForbidden"
                                    )),
                                    content_type = "text/xml",
                                    status = 403,
                                    authorized = False
                                )
        except Exception, e:
            logger.error(str(e))
            return AuthorizationResponse(
                content =  DOMElementToXML(
                                    OWSCommonExceptionEncoder(schemas).encodeExceptionReport(
                                         "Internal Server Error", "NoApplicableCode"
                                    )),
                                    content_type = "text/xml",
                                    status = 500,
                                    authorized = False
                                )


    def _decide(self, ows_req):

        # This method shall implement the actual authorization decision
        # logic. It gets an :class:`~.OWSRequest` object as input and shall
        # return a tuple of ``(authorized, message)`` where ``authorized`` is
        # a boolean flag and ``message`` is a string containing an error
        # message in case authorization is not granted.
        #
        # This method must be overridden by concrete implementations.

        return (True, "")

#-------------------------------------------------------------------------------
# utility functions
#-------------------------------------------------------------------------------

def getPDP():
    pdp_type = System.getRegistry().bind(
        "services.auth.base.AuthConfigReader"
    ).getPDPType()

    if not pdp_type or pdp_type == "none":
        logger.debug("Authorization deactivated.")
        return None

    else:

        return System.getRegistry().findAndBind(
            intf_id = "services.auth.base.PolicyDecisionPointInterface",
            params = {
                "services.auth.base.pdp_type": pdp_type
            }
        )
