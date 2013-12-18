#-------------------------------------------------------------------------------
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

from django.http import HttpResponse

from eoxserver.core import Component, ExtensionPoint, env
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.services.auth.exceptions import AuthorisationException
from eoxserver.services.auth.interfaces import PolicyDecisionPointInterface


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Config reader
#-------------------------------------------------------------------------------

class AuthConfigReader(config.Reader):
    section = "services.auth.base"


    attribute_mapping = config.Option()
    authz_service = config.Option()
    serviceID = config.Option()
    allowLocal = config.Option(type=bool)
    pdp_type = config.Option()


#-------------------------------------------------------------------------------
# PDP Base Class
#-------------------------------------------------------------------------------

class BasePDP(object):
    """
    This is the base class for PDP implementations. It provides a skeleton for
    authorization request handling.
    """

    def authorize(self, request):
        """
        This method handles authorization requests according to the
        requirements given in the :class:`PolicyDecisionPointInterface`
        declaration.

        Internally, it invokes the :meth:`_decide` method that implements the
        actual authorization decision logic.
        """

        reader = AuthConfigReader(get_eoxserver_config())

        # This code segment allows local clients bypassing the
        # Authorisation process.
        if reader.allowLocal:
            remoteAddress = request.META['REMOTE_ADDR']
            # Check all possibilities, also IPv6
            if remoteAddress in ('127.0.0.1', 'localhost', '::1'):
                return True

        authorized, message = self._decide(request)
        if authorized:
            return True
        else:
            raise AuthorisationException(message)


    def _decide(self, request):

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

class PDPComponent(Component):
    pdps = ExtensionPoint(PolicyDecisionPointInterface)

    def get_pdp(self, pdp_type):
        for pdp in self.pdps:
            if pdp.pdp_type == pdp_type:
                return pdp
        return None


def getPDP():
    reader = AuthConfigReader(get_eoxserver_config())
    if not reader.pdp_type or reader.pdp_type == "none":
        logger.debug("Authorization deactivated.")
        return None
    else:
        return PDPComponent(env).get_pdp(reader.pdp_type)
