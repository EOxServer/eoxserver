# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
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
# -------------------------------------------------------------------------------
# pylint: disable=missing-docstring,line-too-long,too-many-ancestors

from autotest_services import base as testbase
from autotest_services.tests.wps.base import (
    WPS10ExecuteMixIn,
    ContentTypeCheckMixIn,
    ContentDispositionCheckMixIn,
    WPS10CapabilitiesMixIn,
)

XML_CONTENT_TYPE = "application/xml"

# ===============================================================================
# WPS 2.0 GetCapabilities
# ===============================================================================


class WPS20GetCapabilitiesValidTestCase(ContentTypeCheckMixIn, testbase.XMLTestCase):
    expectedContentType = XML_CONTENT_TYPE

    def getRequest(self):
        params = "service=WPS&version=2.0.0&request=GetCapabilities"
        return (params, "kvp")


# ===============================================================================
# WPS 2.0 DescribeProcess
# ===============================================================================


class WPS20DescribeProcessTC06MinimalValidProcess(
    ContentTypeCheckMixIn, testbase.XMLTestCase
):
    expectedContentType = XML_CONTENT_TYPE

    def getRequest(self):
        params = "service=WPS&version=2.0.0&request=DescribeProcess&identifier=Test06MinimalValidProcess"
        return (params, "kvp")


# ===============================================================================
# WPS 2.0 Execute
# ===============================================================================


class WPS20ExecuteTC06MinimalValidProcess(
    ContentTypeCheckMixIn, testbase.PlainTextTestCase
):
    expectedContentType = "text/plain; charset=utf-8"

    def getRequest(self):
        # example as defined in
        # http://schemas.opengis.net/wps/2.0/xml-examples/wpsExecuteRequestExample.xml
        params = """<wps:Execute
        version="2.0.0"
        service="WPS"
        response="raw"
        mode="sync"
        xmlns:wps="http://www.opengis.net/wps/2.0"
        xmlns:ows="http://www.opengis.net/ows/2.0" >
          <ows:Identifier>Test06MinimalValidProcess</ows:Identifier>
          <wps:Input id="input">
            <wps:Data>Teststring.</wps:Data>
          </wps:Input>
          <wps:Output id="output" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


GET_STATISTICS_REQUEST = """<wps:Execute service="WPS" version="2.0.0"
  xmlns:wps="http://www.opengis.net/wps/2.0"
  xmlns:ows="http://www.opengis.net/ows/2.0"
  xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/wps/2.0 http://schemas.opengis.net/wps/2.0/wpsExecute.xsd"
  response="raw"
  mode="sync"
>
  <ows:Identifier>{identifier}</ows:Identifier>
  <wps:Input id="bbox">
     <wps:Data>
        <ows:BoundingBox crs="EPSG:4326">
          <ows:LowerCorner>44.0972 38.4119</ows:LowerCorner>
          <ows:UpperCorner>48.8435 42.4293</ows:UpperCorner>
        </ows:BoundingBox>
    </wps:Data>
  </wps:Input>
  <wps:Input id="collection">
    <wps:Data mimeType="text/xml">
      <wps:LiteralValue>DEM</wps:LiteralValue>
    </wps:Data>
  </wps:Input>
  <wps:Output id="statistics" transmission="value" mimeType="application/json"></wps:Output>
</wps:Execute>
"""


class WPS20ExecuteGetStatisticsRaw(ContentTypeCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "application/json; charset=utf-8"

    def getRequest(self):
        return (
            GET_STATISTICS_REQUEST.format(identifier="TC:GetStatistics"),
            "xml",
        )


class WPS20ExecuteGetStatisticsComplexRaw(
    ContentTypeCheckMixIn, testbase.PlainTextTestCase
):
    expectedContentType = "application/json; charset=utf-8"

    def getRequest(self):
        return (
            GET_STATISTICS_REQUEST.format(identifier="TC:GetStatisticsComplex"),
            "xml",
        )
