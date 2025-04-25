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


class WPS20ExecuteCloudCoverageNonCloudy(ContentTypeCheckMixIn, testbase.JSONTestCase):
    fixtures = testbase.JSONTestCase.fixtures + ["scl_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON ((69.19913354922439908 80.1406125504016984, 69.19921132386413376 80.13719046625288911, 69.20360559100976161 80.13719046625288911, 69.20364447832963606 80.14065143772157285, 69.20364447832963606 80.14065143772157285, 69.19913354922439908 80.1406125504016984))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageCloudyGeometry(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["scl_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON ((69.19753916910960356 80.14057366308182395, 69.19757805642947801 80.13960148008500539, 69.20484998524568709 80.13956259276513094, 69.20481109792581265 80.1405347757619495, 69.20481109792581265 80.1405347757619495, 69.19753916910960356 80.14057366308182395))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageTinyGeometry(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["scl_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((69.1714578 80.1407449,69.17148193988112 80.14073878013805,69.17149910356903 80.1407419147403,69.1714578 80.1407449))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageCustomMask(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["scl_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON ((69.19913354922439908 80.1406125504016984, 69.19921132386413376 80.13719046625288911, 69.20360559100976161 80.13719046625288911, 69.20364447832963606 80.14065143772157285, 69.20364447832963606 80.14065143772157285, 69.19913354922439908 80.1406125504016984))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Input id="cloud_mask">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">[1, 2, 3, 8]</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")



class WPS20ExecuteCloudCoverageEmptyResponse(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    # Don't add cloud coverage fixture to provoke empty response
    fixtures = testbase.JSONTestCase.fixtures + []

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((69.1714578 80.1407449,69.17148193988112 80.14073878013805,69.17149910356903 80.1407419147403,69.1714578 80.1407449))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageOnCLM(ContentTypeCheckMixIn, testbase.JSONTestCase):
    fixtures = testbase.JSONTestCase.fixtures + ["clm_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((16.69737831605056 47.47325091482521,16.711481970707467 47.50227740341751,16.665977994941493 47.4984370585647,16.65892616761306 47.47649970533886,16.69737831605056 47.47325091482521))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageOnCLMMoreCloudy(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["clm_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((16.689481892710717 47.49088479184637,16.685847177764813 47.49102703651446,16.685862090779757 47.49375416408526,16.689267315989525 47.49363955046273,16.689481892710717 47.49088479184637))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")


class WPS20ExecuteCloudCoverageOnCLMFewClouds(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["clm_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((16.689481892710717 47.49088479184637,16.685862090779757 47.49375416408526,16.717934765940697 47.50045333252222,16.689481892710717 47.49088479184637))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")

class WPS20ExecuteCloudCoverageOnCLMCustomMask(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["clm_cloud_coverages.json"]

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
          <wps:Input id="geometry">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">POLYGON((16.689481892710717 47.49088479184637,16.685862090779757 47.49375416408526,16.717934765940697 47.50045333252222,16.689481892710717 47.49088479184637))</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Input id="cloud_mask">
            <wps:Data>
              <wps:ComplexData mimeType="text/plain">7</wps:ComplexData>
            </wps:Data>
          </wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")

class WPS20ExecuteCloudCoverageOnMG2Mask(
    ContentTypeCheckMixIn, testbase.JSONTestCase
):
    fixtures = testbase.JSONTestCase.fixtures + ["mg2_cloud_coverages.json"]

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
          <wps:Input id="begin_time">
              <wps:Data>2024-07-24T00:00:00</wps:Data>
          </wps:Input>
          <wps:Input id="end_time">
              <wps:Data>2024-09-07T23:59:59.999999</wps:Data>
          </wps:Input>
          <wps:Input id="geometry">
              <wps:Data>
                  <wps:ComplexData mimeType="text/plain">POLYGON ((15.26296613234851 48.58522462654059, 15.26296735097763 48.58522820523471, 15.26296950923901 48.58513721140181, 15.26293893596117 48.58494329218298, 15.26293562146881 48.58491266740388, 15.2628906951924 48.5845887096719, 15.26288918309506 48.58458090727659, 15.26285420179431 48.58435611129113, 15.26284224281491 48.58428649235474, 15.26278921072745 48.58391615404845, 15.26278178059723 48.58390601986801, 15.26277314522215 48.58362419997486, 15.26274651286159 48.58346674304842, 15.26272692413581 48.58329819402794, 15.26266885866426 48.58295276970647, 15.26298491336765 48.58273434323597, 15.26305158064178 48.5832916822765, 15.26308885283483 48.58361765545947, 15.26309211355407 48.58364684163951, 15.26309580485187 48.58370930916529, 15.26316843092786 48.58427725612233, 15.26321277587909 48.58457837134077, 15.26326042238476 48.58489886540605, 15.26334371326326 48.58534211982499, 15.26303031950466 48.58529113679988, 15.26296684142374 48.58523271205242, 15.26296613234851 48.58522462654059))</wps:ComplexData>
              </wps:Data>
          </wps:Input>
          <wps:Output id="result"></wps:Output>
        </wps:Execute>
        """
        return (params, "xml")
