# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

import re
import logging
import hashlib
import json

from django.core.cache import caches, InvalidCacheBackendError
from django.utils import timezone
from keystoneclient import exceptions as ksexceptions
from keystoneclient.v2_0 import client as ksclient_v2
from keystoneclient.v3 import client as ksclient_v3
from swiftclient.exceptions import ClientException
from django.utils.six.moves.urllib import parse

from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.backends.storage_auths import BaseStorageAuthHandler

logger = logging.getLogger(__name__)


VERSIONFUL_AUTH_PATH = re.compile(r'v[2-3](?:\.0)?$')
AUTH_VERSIONS_V2 = ('2.0', '2', 2)
AUTH_VERSIONS_V3 = ('3.0', '3', 3)


def get_keystone_client(auth_url, user, key, os_options, **kwargs):
    """
    Authenticate against a keystone server.
    We are using the keystoneclient library for authentication.
    """

    insecure = kwargs.get('insecure', False)
    timeout = kwargs.get('timeout', None)
    auth_version = os_options.get('auth_version', None)
    debug = logger.isEnabledFor(logging.DEBUG)

    # Add the version suffix in case of versionless Keystone endpoints. If
    # auth_version is also unset it is likely that it is v3
    if not VERSIONFUL_AUTH_PATH.match(
            parse.urlparse(auth_url).path.rstrip('/').rsplit('/', 1)[-1]):
        # Normalize auth_url to end in a slash because urljoin
        auth_url = auth_url.rstrip('/') + '/'
        if auth_version and auth_version in AUTH_VERSIONS_V2:
            auth_url = parse.urljoin(auth_url, "v2.0")
        else:
            auth_url = parse.urljoin(auth_url, "v3")
            auth_version = '3'
        logger.debug("Versionless auth_url - using %s as endpoint" % auth_url)

    # Legacy default if not set
    if auth_version is None:
        auth_version = '2'

    ksclient = None
    if auth_version in AUTH_VERSIONS_V3:
        if ksclient_v3 is not None:
            ksclient = ksclient_v3
    else:
        if ksclient_v2 is not None:
            ksclient = ksclient_v2

    if ksclient is None:
        raise ClientException('''
Auth versions 2.0 and 3 require python-keystoneclient, install it or use Auth
version 1.0 which requires ST_AUTH, ST_USER, and ST_KEY environment
variables to be set or overridden with -A, -U, or -K.''')

    try:
        client = ksclient.Client(
            username=user,
            password=key,
            token=os_options.get('auth_token'),
            tenant_name=os_options.get('tenant_name'),
            tenant_id=os_options.get('tenant_id'),
            user_id=os_options.get('user_id'),
            user_domain_name=os_options.get('user_domain_name'),
            user_domain_id=os_options.get('user_domain_id'),
            project_name=os_options.get('project_name'),
            project_id=os_options.get('project_id'),
            project_domain_name=os_options.get('project_domain_name'),
            project_domain_id=os_options.get('project_domain_id'),
            debug=debug,
            cacert=kwargs.get('cacert'),
            cert=kwargs.get('cert'),
            key=kwargs.get('cert_key'),
            auth_url=auth_url, insecure=insecure, timeout=timeout)
    except ksexceptions.Unauthorized:
        msg = 'Unauthorized. Check username, password and tenant name/id.'
        if auth_version in AUTH_VERSIONS_V3:
            msg = ('Unauthorized. Check username/id, password, '
                   'tenant name/id and user/tenant domain name/id.')
        raise ClientException(msg)
    except ksexceptions.AuthorizationFailure as err:
        raise ClientException('Authorization Failure. %s' % err)

    return client


def get_endpoint_url_and_token(client, os_options):
    service_type = os_options.get('service_type') or 'object-store'
    endpoint_type = os_options.get('endpoint_type') or 'publicURL'
    try:
        filter_kwargs = {}
        if os_options.get('region_name'):
            filter_kwargs['attr'] = 'region'
            filter_kwargs['filter_value'] = os_options['region_name']
        endpoint = client.service_catalog.url_for(
            service_type=service_type,
            endpoint_type=endpoint_type,
            **filter_kwargs)
    except ksexceptions.EndpointNotFound:
        raise ClientException('Endpoint for %s not found - '
                              'have you specified a region?' % service_type)
    return endpoint, client.auth_token


def get_auth_expires_at(client):
    return parse_iso8601(client.auth_ref['expires_at'])


class KeystoneStorageAuthHandler(BaseStorageAuthHandler):
    name = 'keystone'

    def _get_url_and_token(self):
        url, token = self.get_auth()
        return url, token

    def get_auth(self):
        parameters = {
            key.replace("-", "_"): value for key, value in self.parameters.items()
        }

        os_options = {
            key: parameters.get(key)
            for key in [
                'tenant_id', 'auth_token', 'service_type', 'endpoint_type',
                'tenant_name', 'region_name',
                'auth_version', 'project_name', 'user_domain_name',
                'user_domain_id', 'project_id', 'project_domain_name',
                'project_domain_id',
            ]
        }
        try:
            cache = caches['default']
        except InvalidCacheBackendError:
            cache = None

        if cache:
            base_key = '%s' % hashlib.sha256(json.dumps(dict(
                url=self.url,
                user=self.parameters.get('username'),
                key=self.parameters.get('password'),
                os_options=os_options,
            )).encode('utf-8')).hexdigest()

            token_key = 'keystone_auth_token_%s' % base_key
            url_key = 'keystone_storage_url_%s' % base_key
            token = cache.get(token_key)
            url = cache.get(url_key)
            if url and token:
                logger.debug(
                    'Using cached swift storage URL and access token'
                )
                return url, token

        logger.debug(
            'Fetching swift storage URL and access token'
        )
        client = get_keystone_client(
            self.url,
            user=self.parameters.get('username'),
            key=self.parameters.get('password'),
            os_options=os_options,
        )
        expires_in = (
            get_auth_expires_at(client) - timezone.now()
        ).total_seconds()
        url, token = get_endpoint_url_and_token(client, os_options)

        if cache:
            logger.debug(
                'Caching swift storage URL and access token. '
                'Valid for %f seconds.'
                % expires_in
            )
            cache.set(url_key, url, expires_in)
            cache.set(token_key, token, expires_in)

        return url, token

    def get_vsi_env(self):
        url, token = self._get_url_and_token()
        return {
            'SWIFT_STORAGE_URL': url,
            'SWIFT_AUTH_TOKEN': token,
        }
