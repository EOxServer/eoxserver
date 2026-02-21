import logging
import os
import datetime
import httplib
import xml.dom.minidom

from urllib.parse import urlparse

import eoxserver
from eoxserver.core import implements
from eoxserver.services.auth.base import BasePDP
from eoxserver.services.auth.interfaces import PolicyDecisionPointInterface
from eoxserver.services.auth.charonpdp import CharonPDP


logger = logging.getLogger(__name__)

validUser = {
    'uid': 'jdoe',
    'cn': 'Doe John',
    'sn': 'Doe',
    'description': 'Authorized User'
}

class DummyPDP(BasePDP):
    implements(PolicyDecisionPointInterface)

    def __init__(self):
        self.pdp = CharonPDP(DummyAuthzClient())

    def _decide(self, request):
        httpHeader = request.META

        #checks if a attribute 'DUMMY_MODE' is in the headers
        if 'DUMMY_MODE' in httpHeader:
            logger.info("Security Test: 'DUMMY_MODE' parameter in HTTP header")
            return self.pdp._decide(request)
        else :
            return (True, 'No authorisation testing')


class DummyAuthzClient(object):
    def authorize(self, userAttributes, resourceAttributes, action):
        for key, value in validUser.items():
            if key in userAttributes:
                if value != userAttributes[key]:
                    return (False, 'Not Authorised')
            else:
                return (False, 'Not Authorised')

        return (True, 'Authorised')
