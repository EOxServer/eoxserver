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
import filecmp
import logging
from lxml import etree

from django.test import TestCase, Client

from eoxserver.lib.config import EOxSConfig
from eoxserver.lib.ows import EOxSOWSCommonHandler
from eoxserver.lib.registry import EOxSRegistry
from eoxserver.lib.util import EOxSXMLDecoder

class EOxSTestSchemaFactory(object):
    schemas = {}
    
    @classmethod
    def getSchema(cls, schema_location):
        if schema_location in cls.schemas:
            return cls.schemas[schema_location]
        else:
            logging.info("Opening schema: %s" % schema_location)
            f = open(schema_location)
            schema = etree.XMLSchema(etree.parse(f))
            f.close()
            
            cls.schemas[schema_location] = schema
            
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
        
        f = open(os.path.join("testing","responses", self.getResponseFileName()), 'w')
        f.write(self.response.content)
        f.close()
    
    def getRequest(self):
        raise Exception("Not implemented.")
    
    def getResponseFileExtension(self):
        return "xml"
    
    def getResponseFileName(self):
        return "response_%s.%s" % (self.__class__.__name__, self.getResponseFileExtension())
    
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, 200)

class EOxSXMLTestCase(EOxSTestCase):
    def getSchemaLocation(self):
        return "testing/schemas/wcseo/1.0/wcsEOAll.xsd"
    
    def testValidate(self):
        logging.info("Validating XML ...")
        schema = EOxSTestSchemaFactory.getSchema(self.getSchemaLocation())
        
        try:
            schema.assertValid(etree.fromstring(self.response.content))
        except etree.Error as e:
            self.fail(str(e))

class EOxSWCS20GetCapabilitiesTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "testing/schemas/wcseo/1.0/wcsEOGetCapabilities.xsd"

class EOxSWCS20DescribeCoverageTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "testing/schemas/wcs/2.0/wcsDescribeCoverage.xsd"

class EOxSWCS20DescribeEOCoverageSetTestCase(EOxSXMLTestCase):
    def getSchemaLocation(self):
        return "testing/schemas/wcseo/1.0/wcsEODescribeEOCoverageSet.xsd"
    
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
        return "testing/schemas/ows/2.0/owsExceptionReport.xsd"
    
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

class EOxSFileTestCase(EOxSTestCase):
    def getExpectedFileDir(self):
        return os.join("testing", "expected")
    
    def getExpectedFileName(self):
        return "expected_%s.%s" % (self.__class__.__name__, self.getExpectedFileExtension())
    
    def testBinaryComparison(self):
        self.assertTrue(filecmp.cmp(os.join(self.getExpectedFileDir(), 
                                            self.getExpectedFileName()),
                                    self.getResponseFileName()))
        
class EOxSWCS20GetCoverageTestCase(EOxSFileTestCase):
    def getResponseFileExtension(self):
        return "tif"
    
    def getExpectedFileExtension(self):
        return "tif"
    
class EOxSWCS20GetCoverageMultipartTestCase(EOxSWCS20GetCoverageTestCase):
    def getResponseFileExtension(self):
        return "dat"

    def getExpectedFileExtension(self):
        return "dat"
