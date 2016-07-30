#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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

from autotest_services import base as testbase
from autotest_services.tests.wps.base import (
    WPS10ExecuteMixIn, ContentTypeCheckMixIn, ContentDispositionCheckMixIn,
)

XML_CONTENT_TYPE = "application/xml; charset=utf-8"

#===============================================================================
# advanced data types - time-zone aware input
#===============================================================================

class WPS10TZAwareDatetimeInputProcessDescriptionTestCase(ContentTypeCheckMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC04:identity:literal:datetime"
        return (params, "kvp")


class WPS10TZAwareDatetimeInputNaiveTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC04:identity:literal:datetime&DataInputs=TC04:datetime=2016-08-04T09:26:04&lineage=true"
        return (params, "kvp")


class WPS10TZAwareDatetimeInputAwareTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC04:identity:literal:datetime&DataInputs=TC04:datetime=2016-08-04T09:26:04%2B01:30&lineage=true"
        return (params, "kvp")


class WPS10TZAwareDatetimeInputUTCTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC04:identity:literal:datetime&DataInputs=TC04:datetime=2016-08-04T09:26:04Z&lineage=true"
        return (params, "kvp")

#===============================================================================
# advanced data types - time-zone aware input
#===============================================================================

class WPS10TZAwareDatetimeOutputProcessDescriptionTestCase(ContentTypeCheckMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC05:identity:literal:datetime"
        return (params, "kvp")


class WPS10TZAwareDatetimeOutputNaiveTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC05:identity:literal:datetime&DataInputs=TC05:datetime=2016-08-04T09:26:04&lineage=true"
        return (params, "kvp")


class WPS10TZAwareDatetimeOutputAwareTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC05:identity:literal:datetime&DataInputs=TC05:datetime=2016-08-04T09:26:04%2B01:30&lineage=true"
        return (params, "kvp")


class WPS10TZAwareDatetimeOutputUTCTestCase(ContentTypeCheckMixIn, WPS10ExecuteMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC05:identity:literal:datetime&DataInputs=TC05:datetime=2016-08-04T09:26:04Z&lineage=true"
        return (params, "kvp")
