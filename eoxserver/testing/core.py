#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
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

import email
from email.parser import Parser as MIMEParser
from email.message import Message
from email import message_from_string

from django.test import TestCase, Client

from eoxserver.lib.config import EOxSConfig
from eoxserver.lib.ows import EOxSOWSCommonHandler
from eoxserver.lib.registry import EOxSRegistry
from eoxserver.lib.util import EOxSXMLDecoder

class EOxSTestSchemaFactory(object):
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
        return "expected_%s.%s" % (self.__class__.__name__, self.getFileExtension())
    
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, 200)

    def getExpectedFileDir(self):
        return os.path.join("../autotest", "expected")
    
    def getExpectedFileName(self):
        return "expected_%s.%s" % (self.__class__.__name__, self.getFileExtension())
    
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

            self.fail("Response returned is not equal to expected response. %s %s" % (os.path.join(self.getResponseFileDir(), self.getResponseFileName()), os.path.join(self.getExpectedFileDir(), self.getExpectedFileName())))

class EOxSXMLTestCase(EOxSTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEOAll.xsd"
    
    def testValidate(self):
        logging.info("Validating XML ...")
        schema = EOxSTestSchemaFactory.getSchema(self.getSchemaLocation())
        
        try:
            schema.assertValid(etree.fromstring(self.response.content))
        except etree.Error as e:
            self.fail(str(e))

class EOxSWCS20GetCapabilitiesTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEOGetCapabilities.xsd"

class EOxSWCS20DescribeCoverageTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcs/2.0/wcsDescribeCoverage.xsd"

class EOxSWCS20DescribeEOCoverageSetTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEODescribeEOCoverageSet.xsd"
    
class EOxSWCS20DescribeEOCoverageSetSubsettingTestCase(EOxSWCS20DescribeEOCoverageSetTestCase):
    def getExpectedCoverageIds(self):
        return []
    
    def testCoverageIds(self):
        logging.info("Checking Coverage Ids ...")
        decoder = EOxSXMLDecoder(self.response.content, {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        
        result_coverage_ids = decoder.getValue("coverageids")
        expected_coverage_ids = self.getExpectedCoverageIds()
        
        for result_coverage_id in result_coverage_ids:
            self.assertTrue(result_coverage_id in expected_coverage_ids)
        for expected_coverage_id in expected_coverage_ids:
            self.assertTrue(expected_coverage_id in result_coverage_ids)

class EOxSExceptionTestCase(EOxSXMLTestCase):
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
        decoder = EOxSXMLDecoder(self.response.content, {
            "exceptionCode": {"xml_location": "/ows:Exception/@exceptionCode", "xml_type": "string"}
        })
        
        self.assertEqual(decoder.getValue("exceptionCode"), self.getExpectedExceptionCode())

class EOxSWCS20GetCoverageTestCase(EOxSTestCase):    
    def getFileExtension(self):
        return "tif"
    
class EOxSWCS20GetCoverageMultipartTestCase(EOxSWCS20GetCoverageTestCase):
    def getFileExtension(self):
        return "dat"
    
#    def testBinaryComparison(self):
# TODO: Validate first part against "../schemas/wcseo/1.0/wcsEOCoverage.xsd" and compare second part to expected.
#        expected_msg = email.message_from_file(open(os.path.join(self.getExpectedFileDir(), 
#                                                                 self.getExpectedFileName())))
#        
#        response_msg = email.message_from_file(open(os.path.join(self.getResponseFileDir(), 
#                                                                 self.getResponseFileName())))
#        
#        self.assertTrue(response_msg.is_multipart())
#        
#        for i in range(0, len(response_msg.get_payload())):
#            if response_msg['content-type'] == 'text/xml':
#                continue
#            else:
#                self.assertEqual(response_msg.get_payload(i).get_payload(),
#                                 expected_msg.get_payload(i).get_payload())
