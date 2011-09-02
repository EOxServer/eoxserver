#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

import os.path
import logging
from lxml import etree
from xml.dom import minidom
import tempfile
from osgeo import gdal, gdalconst

import email

from django.test import TestCase, Client

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLDecoder, DOMtoXML
from eoxserver.resources.coverages.synchronize import DatasetSeriesSynchronizer,\
    RectifiedStitchedMosaicSynchronizer

System.init()

BASE_FIXTURES = ["initial_rangetypes.json", "testing_base.json"]

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
    
class EOxServerTestCase(TestCase):
    fixtures = BASE_FIXTURES

class SynchronizationTestCase(EOxServerTestCase):
    """ Base class for test cases targeting the 
        synchronization functionalities.
    """
    
    # Additional fixtures can be loaded with this statement:
    # fixtures = BASE_FIXTURES + ['additional_fixtures.json']
    
    def synchronize(self, model, synchronizerCls):
        synchronizer = synchronizerCls(model)
        synchronizer.update()

class DatasetSeriesSynchronizationTestCase(SynchronizationTestCase):
    """ Base class for synchronization test cases 
        for DatasetSeries. 
    """
    
    def synchronize(self, model, synchronizerCls=None, wrapperId=None):
        if wrapperId is None:
            wrapperId = "resources.coverages.wrappers.DatasetSeriesWrapper"
        
        wrapper = System.getRegistry().bind(wrapperId)
        wrapper.setModel(model)
        wrapper.setMutable()
        
        if synchronizerCls is None:
            synchronizerCls = DatasetSeriesSynchronizer
        
        super(DatasetSeriesSynchronizationTestCase, self).synchronize(wrapper, synchronizerCls) 
        

class RectifiedStitchedMosaicSynchronizationTestCase(SynchronizationTestCase):
    """ Base class for synchronization test cases
        involving RectifiedStitchedMoaics.
    """
    
    def synchronize(self, model, synchronizerCls=RectifiedStitchedMosaicSynchronizer):
        wrapperId = "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"
        
        wrapper = System.getRegistry().bind(wrapperId)
        wrapper.setModel(model)
        wrapper.setMutable()
        
        super(RectifiedStitchedMosaicSynchronizationTestCase, self).synchronize(wrapper, synchronizerCls)


class OWSTestCase(EOxServerTestCase):
    """ Main base class for testing the OWS interface
        of EOxServer.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json"]
    
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
    
    def getResponseData(self):
        return self.response.content
    
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
        
        if expected != self.getResponseData():
            f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName()), 'w')
            f.write(self.getResponseData())
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

class XMLTestCase(OWSTestCase):
    def getSchemaLocation(self):
        return "../schemas/wcseo/1.0/wcsEOAll.xsd"
    
    def getXMLData(self):
        return self.response.content
    
    def testValidate(self):
        logging.info("Validating XML ...")
        schema = TestSchemaFactory.getSchema(self.getSchemaLocation())
        
        try:
            schema.assertValid(etree.fromstring(self.getXMLData()))
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
        decoder = XMLDecoder(self.getXMLData(), {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        
        result_coverage_ids = decoder.getValue("coverageids")
        expected_coverage_ids = self.getExpectedCoverageIds()
        self.assertItemsEqual(result_coverage_ids, expected_coverage_ids)
        
        # assert that every coverage ID is unique in the respinse
        for coverage_id in result_coverage_ids:
            self.assertTrue(result_coverage_ids.count(coverage_id) == 1, "CoverageID %s is not unique." % coverage_id)

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
        decoder = XMLDecoder(self.getXMLData(), {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        coverage_ids = decoder.getValue("coverageids")
        self.assertEqual(len(coverage_ids), self.getExpectedCoverageCount())

class WCS20DescribeEOCoverageSetSectionsTestCase(WCS20DescribeEOCoverageSetTestCase):
    def getExpectedSections(self):
        return []
    
    def testSections(self):
        decoder = XMLDecoder(self.getXMLData(), {
            "sections": {"xml_location": "/*", "xml_type": "tagName[]"}
        })
        sections = decoder.getValue("sections")
        self.assertItemsEqual(sections, self.getExpectedSections())

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
        decoder = XMLDecoder(self.getXMLData(), {
            "exceptionCode": {"xml_location": "/ows:Exception/@exceptionCode", "xml_type": "string"}
        })
        
        self.assertEqual(decoder.getValue("exceptionCode"), self.getExpectedExceptionCode())

class WCS20GetCoverageTestCase(OWSTestCase):
    def setUp(self):
        super(WCS20GetCoverageTestCase, self).setUp()
        _, self.tmppath = tempfile.mkstemp("." + self.getFileExtension())
        f = open(self.tmppath, "w")
        f.write(self.getResponseData())
        f.close()
        gdal.AllRegister()
        self.ds = gdal.Open(self.tmppath, gdalconst.GA_ReadOnly)
        
    def tearDown(self):
        del self.ds
        os.remove(self.tmppath)
    
    def getFileExtension(self):
        return "tif"
    

class TestMixin(object):
    def __init__(self, *args, **kwargs):
        super(TestMixin, self).__init__(*args, **kwargs)
        self.has_mixin = True    

class WCS20GetCoverageSizeTestMixin(TestMixin):
    expected_size = None        # (sizex, sizey)
    
    def testSize(self):
        if not self.expected_size:
            self.skipTest("Expected size not set.")
        
        self.assertEqual((self.ds.RasterXSize, self.ds.RasterYSize),
                         self.expected_size)

class WCS20GetCoverageExtentTestMixin(TestMixin):
    expected_extent = None      # (minx, miny, maxx, maxy)
    
    def testExtent(self):
        if not self.expected_extent:
            self.skipTest("Expected extent not set.")
        
        gt = self.ds.GetGeoTransform()
        extent = (gt[0],                                # minx
                  gt[3] + self.ds.RasterYSize * gt[5],  # miny
                  gt[0] + self.ds.RasterXSize * gt[1],  # maxx
                  gt[3])                                # maxy
        self.assertEqual(extent, self.expected_extent)

class WCS20GetCoverageResolutionTestMixin(TestMixin):
    expected_resolution = None  # (resx, abs(resy))
    
    def testResolution(self):
        if not self.expected_resolution:
            self.skipTest("Expected resolution not set.")
            
        gt = self.ds.GetGeoTransform()
        resolution = (gt[1], abs(gt[5]))
        
        self.assertAlmostEqual(resolution[0], self.expected_resolution[0], delta=self.expected_resolution[0]/10)
        self.assertAlmostEqual(resolution[1], self.expected_resolution[1], delta=self.expected_resolution[1]/10)

class WCS20GetCoverageBandCountTestMixin(TestMixin):
    expected_bandcount = None   # num
    
    def testBandCount(self):
        if not self.expected_bandcount:
            self.skipTest("Expected band count not set.")
            
        self.assertEqual(self.ds.RasterCount, self.expected_bandcount)
    
class WCS20GetCoverageMultipartTestCase(WCS20GetCoverageTestCase, XMLTestCase):
    def setUp(self):
        self.xmlData = None
        self.imageData = None
        self.isSetUp = False
        
        super(WCS20GetCoverageMultipartTestCase, self).setUp()
        
        
        self._setUpMultiparts()
        
        
    
    def _setUpMultiparts(self):
        if self.isSetUp: return
        response_msg = email.message_from_string("Content-type: multipart/mixed; boundary=wcs\n\n"
                                                 + self.response.content)
        for part in response_msg.walk():
            if part['Content-type'] == "multipart/mixed; boundary=wcs":
                continue
            elif part['Content-type'] == "text/xml":
                self.xmlData = part.get_payload()
            else:
                self.imageData = part.get_payload()
        
        self.isSetUp = True
    
    def getFileExtension(self,part=None):
        if part == "xml":
            return "xml"
        elif part == "tif":
            return "tif"
        else:
            return "dat"
    
    def getResponseFileName(self,part):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(part))
    
    def getXMLData(self):
        self._setUpMultiparts()
        return self.xmlData
    
    def getResponseData(self):
        self._setUpMultiparts()
        return self.imageData
        
    def getExpectedFileName(self,part):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(part))
    
    def testValidate(self):
        logging.info("Validating XML ...")
        schema = TestSchemaFactory.getSchema("../schemas/wcseo/1.0/wcsEOCoverage.xsd")
        try:
            schema.assertValid(etree.fromstring(self.getXMLData()))
        except etree.Error as e:
            f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName("xml")), 'w')
            f.write(self.getXMLData())
            f.close()
            self.fail(str(e))
        
        logging.info("Comparing actual and expected XML responses.")
        
        try:
            f = open(os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("xml")), 'r')
            expected = f.read()
            f.close()
        except:
            expected = ""
        
        result_dom = minidom.parseString(self.getXMLData())
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
    
    def testBinaryComparison(self):
        logging.info("Comparing actual and expected GeoTIFF responses.")
        
        try:
            f = open(os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("tif")), 'r')
            expected = f.read()
            f.close()
        except:
            expected = ""
        
        if expected != self.getResponseData():
            f = open(os.path.join(self.getResponseFileDir(), self.getResponseFileName("tif")), 'w')
            f.write(self.getResponseData())
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
