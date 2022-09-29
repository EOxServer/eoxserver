# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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
    ContentTypeCheckMixIn,
)


class WPS20ExecuteCloudCoverage(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["cloud_coverages.json"]

    expectedContentType = "application/json; charset=utf-8"

    def getRequest(self):
        params = """<wps:Execute
        version="2.0.0"
        service="WPS"
        response="raw"
        mode="sync"
        xmlns:wps="http://www.opengis.net/wps/2.0"
        xmlns:ows="http://www.opengis.net/ows/2.0" >
          <ows:Identifier>CloudCoverage</ows:Identifier>
          <wps:Input id="begin_time"><wps:Data>2020-01-01</wps:Data></wps:Input>
          <wps:Input id="end_time"><wps:Data>2020-05-31</wps:Data></wps:Input>
          <wps:Input id="product"><wps:Data>Teststring.</wps:Data></wps:Input>
          <wps:Input id="geometry"><wps:Data>MULTIPOLYGON (((69.1714578 80.1407449, 69.1714578 80.1333736, 69.2069740 80.1333736, 69.2069740 80.1407449, 69.1714578 80.1407449)))</wps:Data></wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageReducedGeometry(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["cloud_coverages.json"]

    expectedContentType = "application/json; charset=utf-8"

    def getRequest(self):
        params = """<wps:Execute
        version="2.0.0"
        service="WPS"
        response="raw"
        mode="sync"
        xmlns:wps="http://www.opengis.net/wps/2.0"
        xmlns:ows="http://www.opengis.net/ows/2.0" >
          <ows:Identifier>CloudCoverage</ows:Identifier>
          <wps:Input id="begin_time"><wps:Data>2020-01-01</wps:Data></wps:Input>
          <wps:Input id="end_time"><wps:Data>2020-05-31</wps:Data></wps:Input>
          <wps:Input id="product"><wps:Data>Teststring.</wps:Data></wps:Input>
          <wps:Input id="geometry"><wps:Data>MULTIPOLYGON (((69.1714578 80.1387449, 69.1714578 80.1333736, 69.1969740 80.1333736, 69.1714578 80.1387449)))</wps:Data></wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")
