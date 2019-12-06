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

import logging
import os
import datetime
import httplib
import xml.dom.minidom
import eoxserver
from urlparse import urlparse

from django.utils.six import iteritems

from eoxserver.core import implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.decoders import get_decoder
from eoxserver.services.auth.base import BasePDP, AuthConfigReader
from eoxserver.services.auth.interfaces import PolicyDecisionPointInterface
                                         

logger = logging.getLogger(__name__)


attrib_subject       = "urn:oasis:names:tc:xacml:1.0:subject:subject-id"
attrib_auth_time     = "urn:oasis:names:tc:xacml:1.0:subject:authentication-time"
attrib_auth_method   = "urn:oasis:names:tc:xacml:1.0:subject:authn-locality:authentication-method"
attrib_request_time  = "urn:oasis:names:tc:xacml:1.0:subject:request-time"
attrib_start_time    = "urn:oasis:names:tc:xacml:1.0:subject:session-start-time"
attrib_resource      = "urn:oasis:names:tc:xacml:1.0:resource:resource-id"
attrib_action        = "urn:oasis:names:tc:xacml:1.0:action:action"
attrib_action_ns     = "urn:oasis:names:tc:xacml:1.0:action:action-namespace"
attrib_current_date  = "urn:oasis:names:tc:xacml:1.0:environment:current-dateTime"

dt_string = "http://www.w3.org/2001/XMLSchema#string"
dt_date   = "http://www.w3.org/2001/XMLSchema#dateTime"
dt_any    = "http://www.w3.org/2001/XMLSchema#anyURI"


# Template for the XACMLAuthzDecisionQuery
template_request = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" " + \
                   "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" " + \
                   "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">" + \
                   "<soapenv:Header></soapenv:Header><soapenv:Body><XACMLAuthzDecisionQuery "  + \
                   "xmlns=\"urn:oasis:xacml:2.0:saml:protocol:schema:os\">" + \
                   "<Request xmlns=\"urn:oasis:names:tc:xacml:2.0:context:schema:os\">" + \
                   "<Subject>{0}</Subject><Resource>{1}</Resource><Action>{2}</Action>" + \
                   "<Environment>{3}</Environment></Request></XACMLAuthzDecisionQuery>" + \
                   "</soapenv:Body></soapenv:Envelope>"

# Template for the Attributes in the XACMLAuthzDecisionQuery
template_attribute = "<Attribute AttributeId=\"{0}\" DataType=\"{1}\">" + \
                     "<AttributeValue>{2}</AttributeValue></Attribute>"


#-------------------------------------------------------------------------------
# PDP implementation for the CHARON Authorization Service
#-------------------------------------------------------------------------------

class CharonPDP(BasePDP):
    implements(PolicyDecisionPointInterface)
    # please do not remove this dictionary; it is needed for EOxServer internal
    # processes

    pdp_type = "charon"

    def __init__(self, client=None):

        cfgReader = AuthConfigReader(get_eoxserver_config())
        url = cfgReader.authorisationServiceURL

        # For tests
        self.client = client or AuthorisationClient(url)
        self.attribMapping = {}

        self.serviceID = cfgReader.serviceID or "default"

        dictLocation = cfgReader.getAttributeMappingDictionary()
        if not dictLocation or dictLocation == "default":
            basePath = os.path.split(eoxserver.__file__)[0]
            dictLocation = os.path.join(basePath, 'conf', 'defaultAttributeDictionary')

        CHAR_COMMENT = '#'
        CHAR_ASSIGN  = '='

        try:
            logger.debug(
                "Loading attribute dictionary from the file %s" % dictLocation
            )
            with open(dictLocation) as f:
                for line in f:
                    if CHAR_COMMENT in line:
                        line, comment = line.split(CHAR_COMMENT, 1)
                    if CHAR_ASSIGN in line:
                        key, value = line.split(CHAR_ASSIGN, 1)
                        key = key.strip()
                        value = value.strip()
                        self.attribMapping[key] = value
                        logger.debug(
                            "Adding SAML attribute to dictionary: %s = %s" 
                            % (key, value)
                        )
        except IOError :
            logger.warn(
                "Cannot read dictionary for attributes mapping from the path: "
                "%s" % dictLocation
            )


    # Extracts the asserted subject attributes from the OWS Request
    def _getAssertedAttributes(self, request):
        httpHeader = request.META
        attributes = {}

        # adding the REMOTE_ADDR from HTTP header to subject attributes
        attributes['REMOTE_ADDR'] = httpHeader['REMOTE_ADDR']

        for key, value in iteritems(self.attribMapping):
            if key in httpHeader:
                attributes[key] = httpHeader[value]
                logger.debug(
                    "Found SAML attribute %s with value %s in incoming "
                    "request." % (key, httpHeader[value]))
            else:
                logger.info(
                    "The key '%s' specified in the mapping dictionary was not "
                    "found in the HTTP headers." % key
                )

        return attributes


    # Extracts the resource specific attributes from the OWS Request
    def _getResourceAttributes(self, request):
        httpHeader = request.META
        attributes = {}

        if self.serviceID == 'default' :
            attributes[attrib_resource] = httpHeader['SERVER_NAME']
        else :
            attributes[attrib_resource] = self.serviceID

        decoder = get_decoder(request)
        attributes['serviceType'] = decoder.service.lower()
        attributes['serverName'] = httpHeader['SERVER_NAME']

        return attributes


    # performs the actual authz. decision
    def _decide(self, request):

        decoder = get_decoder(request)
        userAttributes     = self._getAssertedAttributes(request)
        resourceAttributes = self._getResourceAttributes(request)

        result = self.client.authorize(
            userAttributes, resourceAttributes, decoder.request.lower()
        )
        return result

#-------------------------------------------------------------------------------
# SOAP client for the CHARON Policy Management and Authorization Service
#-------------------------------------------------------------------------------

class AuthorisationClient(object):
    """
    SOAP client for the CHARON Policy Management and Authorisation
    Service

    .. method::  __init__(authz_service_url)

        Constructor with Authorisation Service URL

    .. method:: authorize(userAttributes, resource, action, request)

        This method performs an authorisation request at the Policy Management and
        Authorisation Service.

    """

    def __init__(self, url):

        urlObject = urlparse(url)

        self.port = 80 if urlObject.scheme == 'http' else \
            443 if urlObject.scheme == 'https' else None
        self.hostname = urlObject.hostname
        self.path = urlObject.path if urlObject.path is not None else ''
        self.port = urlObject.port if urlObject.port is not None else self.port
        self.headers = {"Content-type": "text/xml;charset=UTF-8",
                        "Accept": "text/plain",
                        "SOAPAction": "authorise"}

        if (self.hostname is None or self.port is None):
            raise AuthorisationClientException("Invalid argument in constructor: "+str(url)+\
                                               " is not a valid URL.")
        logger.debug("Created instance of AuthorisationClient with the URL "+str(url))


    def authorize(self, userAttributes, resourceAttributes, action):
        request = self._getFullRequest(userAttributes, resourceAttributes, action)

        logger.debug("Sending XACMLAuthzDecisionQuery to "+\
                      str(self.hostname)+":"+str(self.port)+str(self.path)+":\n"+\
                      request)

        connection = httplib.HTTPConnection(self.hostname, self.port)
        connection.request('POST', self.path, request, self.headers)
        response = connection.getresponse()

        # Check for response codes
        if response.status != 200 :
            message = "Received an invalid status code ("+str(response.status)+") when "+\
                      "trying to perform an authorisation query at "+\
                      str(self.hostname)+":"+str(self.port)+str(self.path)+\
                      " Server Message: "+response.reason
            logger.warn(message)
            return (False, message)


        message = response.read()
        connection.close()
        logger.debug("Received the following response from server:\n" + message)
        dom = xml.dom.minidom.parseString(message)
        decision = dom.getElementsByTagNameNS('urn:oasis:names:tc:xacml:2.0:context:schema:os','Decision')

        for node in decision:
            if node.hasChildNodes and node.firstChild.nodeType == xml.dom.minidom.Node.TEXT_NODE:
                value = node.firstChild.data
                if "Permit" == value:
                    return (True, value)
                else :
                    return (False, "Authorisation Decision: "+value)


        return (False, 'Invalid response from Authorisation Service')


    # Get XML snippet for the Subject part of the XACMLAuthzDecisionQuery
    def _getPartSubject(self, userAttributes):
        part = ""
        for attID in userAttributes:
            part += template_attribute.format(attID, \
                                              dt_string, \
                                              userAttributes[attID])
        return part


    # Get XML snippet for the Resource part of the XACMLAuthzDecisionQuery
    def _getPartResource(self, resourceAttributes):

        part = ""
        for attID in resourceAttributes:
            part += template_attribute.format(attID, \
                                              dt_string, \
                                              resourceAttributes[attID])
        return part



    # Get XML snippet for the Action part of the XACMLAuthzDecisionQuery
    def _getPartAction(self, action):
        return template_attribute.format(attrib_action, \
                                         dt_string, \
                                         action)


    # Get XML snippet for the Environment part of the XACMLAuthzDecisionQuery
    def _getPartEnvironment(self):
        now = datetime.datetime.now()
        formattedNow = now.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        return template_attribute.format(attrib_current_date, \
                                         dt_date, \
                                         formattedNow)


    # Get the full XACMLAuthzDecisionQuery
    def _getFullRequest(self, userAttributes, resourceAttributes, action):
        return template_request.format(self._getPartSubject(userAttributes), \
                                       self._getPartResource(resourceAttributes), \
                                       self._getPartAction(action), \
                                       self._getPartEnvironment())


#-------------------------------------------------------------------------------
# AuthorisationClientException
#-------------------------------------------------------------------------------

class AuthorisationClientException(Exception):
    """ Exception that is thrown by the AuthorisationClient in case of an error
    """
