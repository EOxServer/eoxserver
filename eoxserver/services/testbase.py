#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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
import tempfile
import mimetypes
import email

from osgeo import gdal, gdalconst

from django.test import Client

from eoxserver.testing.core import (
    EOxServerTestCase, BASE_FIXTURES
)
from eoxserver.core.util.xmltools import XMLDecoder

# THIS IS INTENTIONALLY DOUBLED DUE TO A BUG IN MIMETYPES!
mimetypes.init()
mimetypes.init()

#===============================================================================
# Helper functions
#===============================================================================

def extent_from_ds(ds):
    gt = ds.GetGeoTransform()
    size_x = ds.RasterXSize
    size_y = ds.RasterYSize
    
    return (gt[0],                   # minx
            gt[3] + size_x * gt[5],  # miny
            gt[0] + size_y * gt[1],  # maxx
            gt[3])                   # maxy

def resolution_from_ds(ds):
    gt = ds.GetGeoTransform()
    return (gt[1], abs(gt[5]))

#===============================================================================
# Common classes
#===============================================================================

class OWSTestCase(EOxServerTestCase):
    """ Main base class for testing the OWS interface
        of EOxServer.
    """
    
    fixtures = BASE_FIXTURES + ["testing_coverages.json", "testing_asar.json"]
    
    def setUp(self):
        super(OWSTestCase,self).setUp()
        
        logging.info("Starting Test Case: %s" % self.__class__.__name__)
        
        request, req_type = self.getRequest()
        
        client = Client()
        
        if req_type == "kvp":
            self.response = client.get('/ows?%s' % request)
        elif req_type == "xml":
            self.response = client.post('/ows', request, "text/xml")
        else:
            raise Exception("Invalid request type '%s'." % req_type)
    
    def getRequest(self):
        raise Exception("Not implemented.")
    
    def getFileExtension(self, file_type):
        return "xml"
    
    def getResponseFileDir(self):
        return os.path.join("../autotest","responses")
    
    def getResponseFileName(self, file_type):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(file_type))
    
    def getResponseData(self):
        return self.response.content
    
    def getExpectedFileDir(self):
        return os.path.join("../autotest", "expected")
    
    def getExpectedFileName(self, file_type):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(file_type))
    
    def _testBinaryComparison(self, file_type):
        """
        Helper function for the `testBinaryComparisonXML` and
        `testBinaryComparisonRaster` functions.
        """
        expected_path = os.path.join(self.getExpectedFileDir(), self.getExpectedFileName(file_type))
        response_path = os.path.join(self.getResponseFileDir(), self.getResponseFileName(file_type))

        try:
            f = open(expected_path, 'r')
            expected = f.read()
            f.close()
        except IOError:
            expected = None
        
        actual_response = None
        if file_type == "raster":
            actual_response = self.getResponseData()
        elif file_type == "xml":
            actual_response = self.getXMLData()
        else:
            self.fail("Unknown file_type '%s'." % file_type)

        if expected != actual_response:
            if self.getFileExtension("raster") == "hdf":
                self.skipTest("Skipping binary comparison for HDF file '%s'." % expected_path)
            f = open(response_path, 'w')
            f.write(actual_response)
            f.close()
            
            if expected is None:
                self.skipTest("Expected response in '%s' is not present" % expected_path)
            else:
                self.fail("Response returned in '%s' is not equal to expected response in '%s'." % (
                           response_path, expected_path)
                )
            
    
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, 200)

class RasterTestCase(OWSTestCase):
    """
    Base class for test cases that expect a raster as response.
    """
    
    def getFileExtension(self, file_type):
        return "tif"
    
    def testBinaryComparisonRaster(self):
        self._testBinaryComparison("raster")

class GDALDatasetTestCase(RasterTestCase):
    """
    Extended RasterTestCases that open the result with GDAL and
    perform several tests.
    """
    
    def tearDown(self):
        super(GDALDatasetTestCase, self).tearDown()
        try:
            del self.res_ds
            del self.exp_ds
            os.remove(self.tmppath)
        except AttributeError:
            pass

    def _openDatasets(self):
        _, self.tmppath = tempfile.mkstemp("." + self.getFileExtension("raster"))
        f = open(self.tmppath, "w")
        f.write(self.getResponseData())
        f.close()
        gdal.AllRegister()
        
        exp_path = os.path.join(self.getExpectedFileDir(), self.getExpectedFileName("raster"))
        
        try:
            self.res_ds = gdal.Open(self.tmppath, gdalconst.GA_ReadOnly)
        except RuntimeError, e:
            self.fail("Response could not be opened with GDAL. Error was %s" % e)
        
        try:
            self.exp_ds = gdal.Open(exp_path, gdalconst.GA_ReadOnly)
        except RuntimeError:
            self.skipTest("Expected response in '%s' is not present" % exp_path)
            
    def testSize(self):
        self._openDatasets()
        self.assertEqual((self.res_ds.RasterXSize, self.res_ds.RasterYSize),
                         (self.exp_ds.RasterXSize, self.exp_ds.RasterYSize))

    def testExtent(self):
        self._openDatasets()
        EPSILON = 1e-8
        
        res_extent = extent_from_ds(self.res_ds)
        exp_extent = extent_from_ds(self.exp_ds)
        
        self.assert_(
            max([
                abs(res_extent[i] - exp_extent[i]) for i in range(0, 4)
            ]) < EPSILON
        )

    def testResolution(self):
        self._openDatasets()
        res_resolution = resolution_from_ds(self.res_ds)
        exp_resolution = resolution_from_ds(self.exp_ds)
        self.assertAlmostEqual(res_resolution[0], exp_resolution[0], delta=exp_resolution[0]/10)
        self.assertAlmostEqual(res_resolution[1], exp_resolution[1], delta=exp_resolution[1]/10)

    def testBandCount(self):
        self._openDatasets()
        self.assertEqual(self.res_ds.RasterCount, self.exp_ds.RasterCount)

class XMLTestCase(OWSTestCase):
    """
    Base class for test cases that expects XML output, which is parsed
    and validated against a schema definition.
    """
    
    def getXMLData(self):
        return self.response.content
    
    def testValidate(self):
        logging.info("Validating XML ...")
        
        doc = etree.XML(self.getXMLData())
        schema_locations = doc.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation")
        locations = schema_locations.split()
        
        # get schema locations
        schema_def = etree.Element("schema", attrib={
                "elementFormDefault": "qualified",
                "version": "1.0.0",
            }, nsmap={
                None: "http://www.w3.org/2001/XMLSchema"
            }
        )
        
        for ns, location in zip(locations[::2], locations[1::2]):
            etree.SubElement(schema_def, "import", attrib={
                    "namespace": ns,
                    "schemaLocation": location
                }
            )
        
        # TODO: ugly workaround. But otherwise, the doc is not recognized as schema
        schema = etree.XMLSchema(etree.XML(etree.tostring(schema_def)))
            
        try:
            schema.assertValid(doc)
        except etree.Error as e:
            self.fail(str(e))
        
    def testBinaryComparisonXML(self):
        self._testBinaryComparison("xml")

class ExceptionTestCase(XMLTestCase):
    """
    Exception test cases expect the request to fail and examine the 
    exception response.
    """
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return ""
    
    def getExceptionCodeLocation(self):
        return "/ows:Exception/@exceptionCode"
        
    def testStatus(self):
        logging.info("Checking HTTP Status ...")
        self.assertEqual(self.response.status_code, self.getExpectedHTTPStatus())
    
    def testExceptionCode(self):
        logging.info("Checking OWS Exception Code ...")
        decoder = XMLDecoder(self.getXMLData(), {
            "exceptionCode": {"xml_location": self.getExceptionCodeLocation(), "xml_type": "string"}
        })
        
        self.assertEqual(decoder.getValue("exceptionCode"), self.getExpectedExceptionCode())      

class MultipartTestCase(XMLTestCase, GDALDatasetTestCase):
    """
    Multipart tests combine XML and raster tests and split the response
    into a xml and a raster part which are examined separately. 
    """
    
    def setUp(self):
        self.xmlData = None
        self.imageData = None
        self.isSetUp = False
        super(MultipartTestCase, self).setUp()
        
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
    
    def getFileExtension(self, part=None):
        if part == "xml":
            return "xml"
        elif part == "raster":
            return "tif"
        else:
            return "dat"
    
    def getXMLData(self):
        self._setUpMultiparts()
        return self.xmlData
    
    def getResponseData(self):
        self._setUpMultiparts()
        return self.imageData

#===============================================================================
# WCS 2.0
#===============================================================================
    
class WCS20DescribeEOCoverageSetSubsettingTestCase(XMLTestCase):
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
        
        # assert that every coverage ID is unique in the response
        for coverage_id in result_coverage_ids:
            self.assertTrue(result_coverage_ids.count(coverage_id) == 1, "CoverageID %s is not unique." % coverage_id)

class WCS20DescribeEOCoverageSetPagingTestCase(XMLTestCase):
    def getExpectedCoverageCount(self):
        return 0
    
    def testCoverageCount(self):
        decoder = XMLDecoder(self.getXMLData(), {
            "coverageids": {"xml_location": "/wcs:CoverageDescriptions/wcs:CoverageDescription/wcs:CoverageId", "xml_type": "string[]"}
        })
        coverage_ids = decoder.getValue("coverageids")
        self.assertEqual(len(coverage_ids), self.getExpectedCoverageCount())

class WCS20DescribeEOCoverageSetSectionsTestCase(XMLTestCase):
    def getExpectedSections(self):
        return []
    
    def testSections(self):
        decoder = XMLDecoder(self.getXMLData(), {
            "sections": {"xml_location": "/*", "xml_type": "tagName[]"}
        })
        sections = decoder.getValue("sections")
        self.assertItemsEqual(sections, self.getExpectedSections())
    
class WCS20GetCoverageMultipartTestCase(MultipartTestCase):
    def testBinaryComparisonXML(self):
        # the timePosition tag depends on the actual time the
        # request was answered. It has to be explicitly unified
        tree = etree.fromstring(self.getXMLData())
        for node in tree.findall("{http://www.opengis.net/gmlcov/1.0}metadata/" \
                                 "{http://www.opengis.net/wcseo/1.0}EOMetadata/" \
                                 "{http://www.opengis.net/wcseo/1.0}lineage/" \
                                 "{http://www.opengis.net/gml/3.2}timePosition"):
            node.text = "2011-01-01T00:00:00Z"
            
        self.xmlData = etree.tostring(tree, encoding="ISO-8859-1")
        
        super(WCS20GetCoverageMultipartTestCase, self).testBinaryComparisonXML()

class RasdamanTestCaseMixIn(object):
    fixtures = BASE_FIXTURES + ["testing_rasdaman_coverages.json"]
    
    def setUp(self):
        # TODO check if connection to DB server is possible
        # TODO check if datasets are configured within the DB

        gdal.AllRegister()
        if gdal.GetDriverByName("RASDAMAN") is None:
            self.skipTest("Rasdaman driver is not enabled.")
        
        super(RasdamanTestCaseMixIn, self).setUp()
    
#===============================================================================
# WMS 1.3 test classes
#===============================================================================

class WMS13GetMapTestCase(RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    
    swap_axes = True
    
    def getFileExtension(self, part=None):
        return mimetypes.guess_extension(self.frmt, False)[1:]
    
    def getRequest(self):
        bbox = self.bbox if not self.swap_axes else (
            self.bbox[1], self.bbox[0],
            self.bbox[3], self.bbox[2]
        )
        
        params = "service=WMS&request=GetMap&version=1.3.0&" \
                 "layers=%s&styles=%s&crs=%s&bbox=%s&" \
                 "width=%d&height=%d&format=%s" % (
                     ",".join(self.layers), ",".join(self.styles), self.crs,
                     ",".join(map(str, bbox)),
                     self.width, self.height, self.frmt
                 )
        return (params, "kvp")

class WMS13ExceptionTestCase(ExceptionTestCase):
    def getExceptionCodeLocation(self):
        return "/{http://www.opengis.net/ogc}ServiceException/@code"
