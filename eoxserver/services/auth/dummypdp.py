import logging
import os
import datetime
import httplib
import xml.dom.minidom
import eoxserver
from urlparse import urlparse
from eoxserver.services.auth.base import BasePDP, \
                                         PolicyDecisionPointInterface, \
                                         AuthConfigReader
from eoxserver.services.auth.charonpdp import CharonPDP


logger = logging.getLogger(__name__)

validUser = {'uid': 'jdoe', 'cn': 'Doe John', 'sn': 'Doe', 'description': 'Authorized User'}


class DummyPDP(BasePDP):

    REGISTRY_CONF = {
        "name": "Dummy Policy Decision Point",
        "impl_id": "services.auth.dummypdp.DummyPDP",
        "registry_values": {
            "services.auth.base.pdp_type": "dummypdp"
        }
    }

    def __init__(self):
        self.pdp = CharonPDP(DummyAuthzClient())

    def _decide(self, ows_req):

        httpHeader = ows_req.http_req.META

        #checks if a attribute 'DUMMY_MODE' is in the headers
        if 'DUMMY_MODE' in httpHeader:
            logger.info("Security Test: 'DUMMY_MODE' parameter in HTTP header")
            return self.pdp._decide(ows_req)
        else :
            return (True, 'No authorisation testing')

DummyPDPImplementation = PolicyDecisionPointInterface.implement(DummyPDP)

class DummyAuthzClient(object):

    def authorize(self, userAttributes, resourceAttributes, action):

        for key, value in validUser.iteritems():
            if key in userAttributes:
                if value != userAttributes[key]:
                    return (False, 'Not Authorised')
            else:
                return (False, 'Not Authorised')

        return (True, 'Authorised')
