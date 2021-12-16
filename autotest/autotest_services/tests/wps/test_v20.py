#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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
#pylint: disable=missing-docstring,line-too-long,too-many-ancestors

from autotest_services import base as testbase
from autotest_services.tests.wps.base import (
    WPS10ExecuteMixIn, ContentTypeCheckMixIn, ContentDispositionCheckMixIn,
    WPS10CapabilitiesMixIn,
)

XML_CONTENT_TYPE = "application/xml; charset=utf-8"

#===============================================================================
# WCS 2.0 GetCapabilities
#===============================================================================

class WPS20GetCapabilitiesValidTestCase(ContentTypeCheckMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=2.0.0&request=GetCapabilities"
        return (params, "kvp")
