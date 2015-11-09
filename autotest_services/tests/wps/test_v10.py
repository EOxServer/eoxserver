#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

#===============================================================================
# WCS 1.0 GetCapabilities
#===============================================================================

class WPS10GetCapabilitiesValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WPS10PostGetCapabilitiesValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:GetCapabilities updateSequence="u2001" service="WPS"
          xmlns:wps="http://www.opengis.net/wps/1.0"
          xmlns:ows="http://www.opengis.net/ows/1.1">
            <ows:AcceptVersions><ows:Version>1.0.0</ows:Version></ows:AcceptVersions>
          </wps:GetCapabilities>
        """
        return (params, "xml")


#===============================================================================
# WCS 1.0 DescribeProcess
#===============================================================================


class WPS10DescribeProcessValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC00:identity:literal"
        return (params, "kvp")

class WPS10PostDescribeProcessValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:DescribeProcess service="WPS" version="1.0.0"
          xmlns:wps="http://www.opengis.net/wps/1.0"
          xmlns:ows="http://www.opengis.net/ows/1.1">
            <ows:Identifier>TC00:identity:literal</ows:Identifier>
          </wps:DescribeProcess>
        """
        return (params, "xml")

class WPS10DescribeProcessValidTC01TestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC01:identity:bbox"
        return (params, "kvp")

class WPS10DescribeProcessValidTC02TestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC02:identity:complex"
        return (params, "kvp")

class WPS10DescribeProcessValidTC03TestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=DescribeProcess&identifier=TC03:image_generator:complex"
        return (params, "kvp")

#TODO: Error - invalid process identifier

#===============================================================================
# WCS 1.0 Execute - Literal Data Tests
#===============================================================================

class WPS10ExecuteTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC00:identity:literal</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>input00</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>Test string.</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC00:identity:literal&DataInputs=input00=Test+string."
        return (params, "kvp")

class WPS10ExecuteLiteralDataTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC00:identity:literal</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>input00</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>Test string.</wps:LiteralData>
              </wps:Data>
            </wps:Input>
           <wps:Input>
              <ows:Identifier>TC00:input02</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>low</wps:LiteralData>
              </wps:Data>
            </wps:Input>
           <wps:Input>
              <ows:Identifier>TC00:input03</ows:Identifier>
              <wps:Data>
                <wps:LiteralData uom="mm">734</wps:LiteralData>
              </wps:Data>
            </wps:Input>
           <wps:Input>
              <ows:Identifier>TC00:input04</ows:Identifier>
              <wps:Data>
                <wps:LiteralData uom="C">15</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true" storeExecuteResponse="false" status="false">
              <wps:Output>
                <ows:Identifier>output00</ows:Identifier>
                <ows:Title>Userdefined title.</ows:Title>
                <ows:Abstract>Userdefined abstract.</ows:Abstract>
              </wps:Output>
              <wps:Output asReference="false" uom="cm">
                <ows:Identifier>TC00:output03</ows:Identifier>
              </wps:Output>
              <wps:Output asReference="false" uom="F">
                <ows:Identifier>TC00:output04</ows:Identifier>
              </wps:Output>
            </wps:ResponseDocument>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteLiteralDataKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC00:identity:literal&DataInputs=input00=Some+text.%3BTC00%3Ainput03=123@uom=mm%3BTC00%3Ainput04=19.5@uom=C&ResponseDocument=TC00%3Aoutput03@uom=cm%3BTC00%3Aoutput04@uom=F&lineage=true"
        return (params, "kvp")

class WPS10ExecuteLiteralDataRawOutputTestCase(ContentTypeCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain; charset=utf-8"
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC00:identity:literal</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>input00</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>Test string.</wps:LiteralData>
              </wps:Data>
            </wps:Input>
            <wps:Input>
              <ows:Identifier>TC00:input04</ows:Identifier>
              <wps:Data>
                <wps:LiteralData uom="C">15</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:RawDataOutput asReference="false" uom="F">
              <ows:Identifier>TC00:output04</ows:Identifier>
            </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        # response: 59
        return (params, "xml")

class WPS10ExecuteLiteralDataRawOutputKVPTestCase(ContentTypeCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain; charset=utf-8"
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC00:identity:literal&DataInputs=input00=Some+text.%3BTC00%3Ainput04=19.5@uom=C&RawDataOutput=TC00%3Aoutput04@uom=F"
        # response: 67.1
        return (params, "kvp")

#TODO: Error - malformed XML request
#TODO: Error - malformed KVP request
#TODO: Error - invalid process identifier
#TODO: Error - missing required input
#TODO: Error - invalid input (identifier)
#TODO: Error - invalid input (value type)
#TODO: Error - invalid input (out of the allowed range)
#TODO: DateTime test

#===============================================================================
# WCS 1.0 Execute - Bounding Box Data Tests
#===============================================================================

class WPS10ExecuteBoundingBoxTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC01:identity:bbox</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC01:input00</ows:Identifier>
              <wps:Data>
                <wps:BoundingBoxData crs="EPSG:4326">
                  <ows:LowerCorner>0 1</ows:LowerCorner>
                  <ows:UpperCorner>2 3</ows:UpperCorner>
                </wps:BoundingBoxData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true" storeExecuteResponse="false" status="false" />
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteBoundingBoxKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC01:identity:bbox&DataInputs=TC01:input00=0,1,2,3,urn:ogc:def:crs:EPSG::4326&lineage=true"
        return (params, "kvp")

class WPS10ExecuteBoundingBoxRawOutputTestCase(ContentTypeCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain"
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC01:identity:bbox</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC01:input00</ows:Identifier>
              <wps:Data>
                <wps:BoundingBoxData crs="http://www.opengis.net/def/crs/EPSG/0/4326">
                  <ows:LowerCorner>0 1</ows:LowerCorner>
                  <ows:UpperCorner>2 3</ows:UpperCorner>
                </wps:BoundingBoxData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
           <wps:RawDataOutput>
             <ows:Identifier>TC01:output00</ows:Identifier>
           </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        # response: 0,1,2,3,http://www.opengis.net/def/crs/EPSG/0/4326
        return (params, "xml")


class WPS10ExecuteBoundingBoxRawOutputKVPTestCase(ContentTypeCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain"
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC01:identity:bbox&DataInputs=TC01:input00=0,1,2,3,ImageCRS&RawDataOutput=TC01:output00"
        # response: 0,1,2,3,ImageCRS
        return (params, "kvp")

#TODO: Error - invalid input CRS
#TODO: Error - invalid output CRS

#===============================================================================
# WCS 1.0 Execute - Complex Data Tests (text-based payload)
#===============================================================================

class WPS10ExecuteComplexDataTextTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData>Sample
text
complex
payload.</wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataJSONTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData mimeType="application/json">{"numbers":[1,2,3,1.23456789012345678901e-124],"string":"Hallo world!"}</wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true">
              <wps:Output mimeType="application/json">
                <ows:Identifier>TC02:output00</ows:Identifier>
              </wps:Output>
            </wps:ResponseDocument>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataXMLTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData mimeType="text/xml">
                  <test:testXML xmlns:test="http://xml.eox.at/test" />
                </wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true">
              <wps:Output mimeType="text/xml">
                <ows:Identifier>TC02:output00</ows:Identifier>
              </wps:Output>
            </wps:ResponseDocument>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataTextKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00=P%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.&lineage=true"
        return (params, "kvp")

class WPS10ExecuteComplexDataJSONKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00={%22text%22:%22P%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.%22}@mimeType=application%2Fjson&ResponseDocument=TC02:output00@mimeType=application%2Fjson&lineage=true"
        return (params, "kvp")

class WPS10ExecuteComplexDataXMLKVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00=%3Ctest%3AtestXML+xmlns%3Atest%3D%22http%3A%2F%2Fxml.eox.at%2Ftest%22%3EP%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.%3C%2Ftest%3AtestXML%3E@mimeType=text%2Fxml&ResponseDocument=TC02:output00@mimeType=text%2Fxml&lineage=true"
        return (params, "kvp")


class WPS10ExecuteComplexDataTextRawOutputTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.txt"'
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData>Sample
text
complex
payload.</wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:RawDataOutput>
              <ows:Identifier>TC02:output00</ows:Identifier>
            </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataJSONRawOutputTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.JSONTestCase):
    expectedContentType = "application/json; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.json"'
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData mimeType="application/json">{"numbers":[1,2,3,1.23456789012345678901e-124],"string":"Hallo world!"}</wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:RawDataOutput mimeType="application/json">
              <ows:Identifier>TC02:output00</ows:Identifier>
            </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataXMLRawOutputTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.XMLNoValTestCase):
    expectedContentType = "text/xml; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.xml"'
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC02:identity:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC02:input00</ows:Identifier>
              <wps:Data>
                <wps:ComplexData mimeType="text/xml">
                  <test:testXML xmlns:test="http://xml.eox.at/test" />
                </wps:ComplexData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
           <wps:RawDataOutput mimeType="text/xml">
             <ows:Identifier>TC02:output00</ows:Identifier>
           </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")


class WPS10ExecuteComplexDataTextRawOutputKVPTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.PlainTextTestCase):
    expectedContentType = "text/plain; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.txt"'
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00=P%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.&RawDataOutput=TC02:output00"
        return (params, "kvp")

class WPS10ExecuteComplexDataJSONRawOutputKVPTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.JSONTestCase):
    expectedContentType = "application/json; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.json"'
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00={%22text%22:%22P%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.%22}@mimeType=application%2Fjson&ResponseDocument=TC02:output00@mimeType=application%2Fjson&RawDataOutput=TC02:output00@mimeType=application%2Fjson"
        return (params, "kvp")

class WPS10ExecuteComplexDataXMLRawOutputKVPTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.XMLNoValTestCase):
    expectedContentType = "text/xml; charset=utf-8"
    expectedContentDisposition = 'attachment; filename="test02_identity_complex.xml"'
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC02:identity:complex&DataInputs=TC02:input00=%3Ctest%3AtestXML+xmlns%3Atest%3D%22http%3A%2F%2Fxml.eox.at%2Ftest%22%3EP%C5%99%C3%ADli%C5%A1%20%C5%BElu%C5%A5ou%C4%8Dk%C3%BD%20k%C5%AF%C5%88%20%C3%BAp%C4%9Bl%20%C4%8F%C3%A1belsk%C3%A9%20%C3%B3dy.%3C%2Ftest%3AtestXML%3E@mimeType=text%2Fxml&RawDataOutput=TC02:output00@mimeType=text%2Fxml"
        return (params, "kvp")

#===============================================================================
# WCS 1.0 Execute - Complex Data Tests (binary payload)
#===============================================================================

class WPS10ExecuteComplexDataPNGBase64FileTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC03:image_generator:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC03:method</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>file</wps:LiteralData>
              </wps:Data>
            </wps:Input>
            <wps:Input>
              <ows:Identifier>TC03:seed</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>0</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true" storeExecuteResponse="false" status="false">
              <wps:Output mimeType="image/png" encoding="base64">
                <ows:Identifier>TC03:output00</ows:Identifier>
              </wps:Output>
            </wps:ResponseDocument>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataTIFBase64InMemTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC03:image_generator:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC03:method</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>in-memory-buffer</wps:LiteralData>
              </wps:Data>
            </wps:Input>
            <wps:Input>
              <ows:Identifier>TC03:seed</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>0</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
            <wps:ResponseDocument lineage="true" storeExecuteResponse="false" status="false">
              <wps:Output mimeType="image/tiff" encoding="base64">
                <ows:Identifier>TC03:output00</ows:Identifier>
              </wps:Output>
            </wps:ResponseDocument>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")

class WPS10ExecuteComplexDataJPGBase64KVPTestCase(WPS10ExecuteMixIn, testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC03:image_generator:complex&DataInputs=TC03:seed=0&ResponseDocument=TC03:output00@mimeType=image%2Fjpeg@encoding=base64&lineage=true"
        return (params, "kvp")

class WPS10ExecuteComplexDataPNGRawOutputKVPTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.GDALDatasetTestCase):
    expectedContentType = "image/png"
    expectedContentDisposition = 'attachment; filename="test03_binary_complex.png"'
    def getFileExtension(self, file_type):
        return "png"
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC03:image_generator:complex&DataInputs=TC03:seed=0&RawDataOutput=TC03:output00"
        return (params, "kvp")

class WPS10ExecuteComplexDataTIFRawOutputKVPTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.GDALDatasetTestCase):
    expectedContentType = "image/tiff"
    expectedContentDisposition = 'attachment; filename="test03_binary_complex.tif"'
    def getFileExtension(self, file_type):
        return "tif"
    def getRequest(self):
        params = "service=WPS&version=1.0.0&request=Execute&identifier=TC03:image_generator:complex&DataInputs=TC03:seed=0&RawDataOutput=TC03:output00@mimeType=image%2Ftiff"
        return (params, "kvp")

class WPS10ExecuteComplexDataJPGRawOutputTestCase(ContentTypeCheckMixIn, ContentDispositionCheckMixIn, testbase.GDALDatasetTestCase):
    expectedContentType = "image/jpeg"
    expectedContentDisposition = 'attachment; filename="test03_binary_complex.jpg"'
    def getFileExtension(self, file_type):
        return "jpg"
    def getRequest(self):
        params = """<wps:Execute version="1.0.0" service="WPS"
        xmlns:wps="http://www.opengis.net/wps/1.0.0"
        xmlns:ows="http://www.opengis.net/ows/1.1">
          <ows:Identifier>TC03:image_generator:complex</ows:Identifier>
          <wps:DataInputs>
            <wps:Input>
              <ows:Identifier>TC03:seed</ows:Identifier>
              <wps:Data>
                <wps:LiteralData>0</wps:LiteralData>
              </wps:Data>
            </wps:Input>
          </wps:DataInputs>
          <wps:ResponseForm>
           <wps:RawDataOutput mimeType="image/jpeg">
             <ows:Identifier>TC03:output00</ows:Identifier>
           </wps:RawDataOutput>
          </wps:ResponseForm>
        </wps:Execute>
        """
        return (params, "xml")
