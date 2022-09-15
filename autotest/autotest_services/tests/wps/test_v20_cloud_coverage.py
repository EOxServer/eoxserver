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
          <wps:Input id="geometry"><wps:Data>MULTIPOLYGON (((-0.7697718236173799 46.21844540418552, 0.288547363821689 46.08290644415141, 2.733419759721718 45.73636263672618, 4.815657039292408 45.39947037754385, 6.894775798282314 45.00948175187284, 8.154913571318612 44.75018471574041, 9.634245839133294 44.41952395308687, 11.00618247148604 44.10606584164272, 12.27883282764158 43.79980935386448, 12.87473445741455 43.64035642239579, 12.22874811272635 42.2970241539363, 11.42842470078386 40.54055904761669, 10.66098787948851 38.74418401722271, 9.927539260629768 36.9630879853842, 9.239587579469651 35.18226041011476, 8.728287480275119 33.80781071010245, 8.174463354403226 32.26454057758526, 7.346658308388547 32.47445746391359, 5.48900097684443 32.9147209085525, 3.594912710998026 33.32929471736243, 1.679561673218221 33.71894896552116, -0.256213475006078 34.08288220106373, -1.744083689584682 34.34057243249224, -3.43798101398678 34.6029479595267, -3.312138031931722 35.20050022128398, -2.96861379128801 36.75709370137025, -2.682010254826003 38.05579573474809, -2.350758514252345 39.51733579731436, -1.942069312500661 41.30092067756908, -1.553859522839208 42.94621606148156, -1.166995203885614 44.59251101422208, -0.7697718236173799 46.21844540418552)))</wps:Data></wps:Input>
          <wps:Output id="result" >
          </wps:Output>
        </wps:Execute>
        """
        return (params, "xml")
