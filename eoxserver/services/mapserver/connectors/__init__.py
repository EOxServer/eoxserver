# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.services.mapserver.config import (
    DEFAULT_EOXS_MAPSERVER_CONNECTORS
)

MAPSERVER_CONNECTORS = None


def _setup_connectors():
    global MAPSERVER_CONNECTORS
    specifiers = getattr(
        settings, 'EOXS_MAPSERVER_CONNECTORS',
        DEFAULT_EOXS_MAPSERVER_CONNECTORS
    )
    MAPSERVER_CONNECTORS = [
        import_string(specifier)()
        for specifier in specifiers
    ]


def get_connector_by_test(coverage, data_items):
    """ Get a coverage metadata format reader by testing.
    """
    if not MAPSERVER_CONNECTORS:
        _setup_connectors()

    for connector in MAPSERVER_CONNECTORS:
        if connector.supports(coverage, data_items):
            return connector
    return None
