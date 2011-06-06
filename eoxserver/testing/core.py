#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import os.path
import logging
from lxml import etree
from xml.dom import minidom

import email

from django.test import TestCase, Client

from eoxserver.core.util.xmltools import XMLDecoder, DOMtoXML

class TestSchemaFactory(object):
    schemas = {}
    
    @classmethod
    def getSchema(cls, schema_location):
#        # Singleton version for usage with remote schemas:
#        # This version provides hugh performance advantages but 
#        # also random segfaults in libxml2.
#        if schema_location in cls.schemas:
#            return cls.schemas[schema_location]
#        else:
#            logging.info("Opening schema: %s" % schema_location)
#            f = open(schema_location)
#            schema = etree.XMLSchema(etree.parse(f))
#            f.close()
#            
#            cls.schemas[schema_location] = schema
#            
#            return schema
        # Non singleton version for usage with locally stored schemas:
        logging.info("Opening schema: %s" % schema_location)
        f = open(schema_location)
        schema = etree.XMLSchema(etree.parse(f))
        f.close()
        
        return schema


class EOxSTestCase(TestCase):
    def setUp(self):
        logging.info("Starting Test Case: %s" % self.__class__.__name__)
        
        request, type = self.getRequest()
        
        client = Client()
        
        if type == "kvp":
            self.response = client.get('/ows?%s' % request)
        elif type == "xml":
            self.response = client.post('/ows', request, "text/xml")
        else:
            raise Exception("Invalid request type '%s'." % type)
    
    def getRequest(self):
        raise Exception("Not implemented.")
    
    def getFileExtension(self):
        return "xml"
    
    def getResponseFileDir(self):
        return os.path.join("../autotest","responses")
    
    def getResponseFileName(self):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension())
    
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, 200)

    def getExpectedFileDir(self):
        return os.path.join("../autotest", "expected")
    
    def getExpectedFileName(self):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension())
    
    def testBinaryComparison(self):
        try:
            f = open(os.path.join(self.getExpectedFileDir(), self.getExpectedFileName()), 'r')
            expected = f.read()
            f.close()
        except:
            expected = ""
        
        if expected != self.response.content:
            f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName()), 'w')
            f.write(self.response.content)
            f.close()
            
            if expected == "":
                self.fail("Expected response in '%s' is not present" % 
                           os.path.join(self.getExpectedFileDir(), self.getExpectedFileName())
                )
            else:
                self.fail("Response returned in '%s' is not equal to expected response in '%s'." % (
                           os.path.join(self.getResponseFileDir(), self.getResponseFileName()),
                           os.path.join(self.getExpectedFileDir(), self.getExpectedFileName()))
                )

class XMLTestCase(EOxSTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEOAll.xsd"
    
    def testValidate(self):
        logging.info("Validating XML ...")
        schema = TestSchemaFactory.getSchema(self.getSchemaLocation())
        
        try:
            schema.assertValid(etree.fromstring(self.response.content))
        except etree.Error as e:
            self.fail(str(e))

class WCS20GetCapabilitiesTestCase(XMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEOGetCapabilities.xsd"

class WCS20DescribeCoverageTestCase(XMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcs/2.0/wcsDescribeCoverage.xsd"

class WCS20DescribeEOCoverageSetTestCase(XMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEODescribeEOCoverageSet.xsd"
    
class WCS20DescribeEOCoverageSetSubsettingTestCase(WCS20DescribeEOCoverageSetTestCase):
    def getExpectedCoverageIds(self):
        return []
    
    def testCoverageIds(self):
        logging.info("Checking Coverage Ids ...")
        decoder = XMLDecoder(self.response.content, {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        
        result_coverage_ids = decoder.getValue("coverageids")
        expected_coverage_ids = self.getExpectedCoverageIds()
        
        for result_coverage_id in result_coverage_ids:
            self.assertTrue(result_coverage_id in expected_coverage_ids)
        for expected_coverage_id in expected_coverage_ids:
            self.assertTrue(expected_coverage_id in result_coverage_ids)

class WCS20DescribeEOCoverageSetPagingTestCase(WCS20DescribeEOCoverageSetTestCase):
# TODO
#    def setUp(self):
#        self.saved_paging_default = System.getConfig().getConfigValue("services.ows.wcs20", "paging_count_default")
#        System.getConfig().paging_count_default = self.getConfigCountOverride()
#        super(WCS20DescribeEOCoverageSetPagingTestCase, self).setUp()
    
#    def tearDown(self):
#        super(WCS20DescribeEOCoverageSetPagingTestCase, self).tearDown()
#        System.getConfig().paging_count_default = self.saved_paging_default
    
    def getExpectedCoverageCount(self):
        return 0
    
#    def getConfigCountOverride(self):
#        return System.getConfig().getConfigValue("services.ows.wcs20", "paging_count_default")
    
    def testCoverageCount(self):
        decoder = XMLDecoder(self.response.content, {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        coverage_ids = decoder.getValue("coverageids")
        self.assertEqual(len(coverage_ids), self.getExpectedCoverageCount())

class ExceptionTestCase(XMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/ows/2.0/owsExceptionReport.xsd"
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return ""
        
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, self.getExpectedHTTPStatus())
    
    def testExceptionCode(self):
        logging.info("Checking OWS Exception Code ...")
        decoder = XMLDecoder(self.response.content, {
            "exceptionCode": {"xml_location": "/ows:Exception/@exceptionCode", "xml_type": "string"}
        })
        
        self.assertEqual(decoder.getValue("exceptionCode"), self.getExpectedExceptionCode())

class WCS20GetCoverageTestCase(EOxSTestCase):    
    def getFileExtension(self):
        return "tif"
    
class WCS20GetCoverageMultipartTestCase(WCS20GetCoverageTestCase):
    def getFileExtension(self,part=None):
        if part == "xml":
            return "xml"
        elif part == "tif":
            return "tif"
        else:
            return "dat"
    
    def getResponseFileName(self,part):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(part))
    
    def getExpectedFileName(self,part):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(part))
    
    def testBinaryComparison(self):
        self.assertTrue(self.response["Content-type"] == "multipart/mixed; boundary=wcs","Response returned '%s' is not of type multipart/mixed.")
        
        response_msg = email.message_from_string("Content-type: multipart/mixed; boundary=wcs\n\n"+self.response.content)
        
        for part in response_msg.walk():
            if part['Content-type'] == "multipart/mixed; boundary=wcs":
                continue
            elif part['Content-type'] == "text/xml":
                logging.info("Validating XML ...")
                schema = TestSchemaFactory.getSchema("../schemas/wcseo/1.0/wcsEOCoverage.xsd")
                try:
                    schema.assertValid(etree.fromstring(part.get_payload()))
                except etree.Error as e:
                    f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName("xml")), 'w')
                    f.write(part.get_payload())
                    f.close()
                    self.fail(str(e))
                
                logging.info("Comparing actual and expected XML responses.")
                
                try:
                    f = open(os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("xml")), 'r')
                    expected = f.read()
                    f.close()
                except:
                    expected = ""
                
                result_dom = minidom.parseString(part.get_payload())
                lineage_date = result_dom.getElementsByTagName("wcseo:lineage").item(0)
                for node in lineage_date.childNodes:
                    if node.tagName == "gml:timePosition":
                        logging.info("Normalizing timePosition in lineage")
                        node.firstChild.data = "2011-01-01T00:00:00Z"
                result_cleared = DOMtoXML(result_dom)
                result_dom.unlink()
                
                if expected != result_cleared:
                    f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName("xml")), 'w')
                    f.write(result_cleared)
                    f.close()
                    
                    if expected == "":
                        self.fail("Expected response '%s' not present" % 
                                   os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("xml"))
                        )
                    else:
                        self.fail("Response returned '%s' is not equal to expected response '%s'." % (
                                   os.path.join(self.getResponseFileDir(), self.getResponseFileName("xml")),
                                   os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("xml")))
                        )
            
            else:
                logging.info("Comparing actual and expected GeoTIFF responses.")
                
                try:
                    f = open(os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("tif")), 'r')
                    expected = f.read()
                    f.close()
                except:
                    expected = ""
                
                if expected != part.get_payload():
                    f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName("tif")), 'w')
                    f.write(part.get_payload())
                    f.close()
                    
                    if expected == "":
                        self.fail("Expected response '%s' not present" % 
                                   os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("tif"))
                        )
                    else:
                        self.fail("Response returned '%s' is not equal to expected response '%s'." % (
                                   os.path.join(self.getResponseFileDir(), self.getResponseFileName("tif")),
                                   os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("tif")))
                        )
