#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

import re 
import os.path
import logging
from lxml import etree
import tempfile
import mimetypes
from cStringIO import StringIO

from django.test import Client
from django.conf import settings

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLDecoder
from eoxserver.core.util.multiparttools import (
    mpUnpack, getMimeType, getMultipartBoundary
)
from eoxserver.contrib import gdal, osr
from eoxserver.testing.core import (
    EOxServerTestCase, BASE_FIXTURES
)
from eoxserver.testing.xcomp import xmlCompareFiles


logger = logging.getLogger(__name__)

# THIS IS INTENTIONALLY DOUBLED DUE TO A BUG IN MIMETYPES!
mimetypes.init()
mimetypes.init()

# precompile regular expression
RE_MIME_TYPE_XML = re.compile("^text/xml|application/(?:[a-z]+\+)?xml$",re.IGNORECASE)

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

def _getMime( s ) : 
    return s.partition(';')[0].strip().lower() 
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
        
        logger.info("Starting Test Case: %s" % self.__class__.__name__)
        
        rq = self.getRequest()

        if ( len(rq) == 2 ):
            request, req_type = rq
            headers = {}
        else:
            request, req_type, headers = rq

        client = Client()

        if req_type == "kvp":
            self.response = client.get('/ows?%s' % request, {}, **headers)

        elif req_type == "xml":
            self.response = client.post('/ows', request, "text/xml", {}, **headers)

        else:
            raise Exception("Invalid request type '%s'." % req_type)
    
    def isRequestConfigEnabled(self, config_key, default=False):
        value = System.getConfig().getConfigValue("testing", config_key)
        if value is None:
            return default
        elif value.lower() in ("yes", "y", "true", "on"):
            return True
        elif value.lower() in ("no", "n", "false", "off"):
            return False
        else:
            return default
    
    def getRequest(self):
        raise Exception("Not implemented.")
    
    def getFileExtension(self, file_type):
        return "xml"
    
    def getResponseFileDir(self):
        return os.path.join(settings.PROJECT_DIR,"responses")

    def getDataFileDir(self):
        return os.path.join(settings.PROJECT_DIR,"data")
    
    def getResponseFileName(self, file_type):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(file_type))
    
    def getResponseData(self):
        return self.response.content
    
    def getExpectedFileDir(self):
        return os.path.join(settings.PROJECT_DIR, "expected")
    
    def getExpectedFileName(self, file_type):
        return "%s.%s" % (self.__class__.__name__, self.getFileExtension(file_type))
    
    def getXMLData(self):
        raise Exception("Not implemented.")
    
    def _testXMLComparison( self , suffix = "xml" , response = None ): 
        """
        Helper function for the basic XML tree comparison to be used by `testXMLComparison`.
        """
        expected_path = os.path.join( self.getExpectedFileDir(), self.getExpectedFileName(suffix) )
        response_path = os.path.join( self.getResponseFileDir(), self.getResponseFileName(suffix) )
        
        # store the XML response 
        if response is None : response = self.getXMLData()
        
        # check that the expected XML response exists 
        if not os.path.isfile( expected_path ) : 
            with file(response_path, 'w') as fid : fid.write(response)
            self.skipTest( "Missing the expected XML response '%s'." % expected_path )
        
        # perform the actual comparison 
        try: 
            xmlCompareFiles( expected_path , StringIO(response) ) 
        except Exception as e : 
            with file(response_path, 'w') as fid : fid.write(response)
            self.fail( "Response returned in '%s' is not equal to expected response in '%s'. REASON: %s " % \
                    ( response_path , expected_path , str(e) ) )


    def _testBinaryComparison(self, file_type, Data=None):
        """
        Helper function for the `testBinaryComparisonRaster` function.
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
        if Data is None:
            if file_type in ("raster", "html"):
                actual_response = self.getResponseData()
            elif file_type == "xml":
                actual_response = self.getXMLData()
            else:
                self.fail("Unknown file_type '%s'." % file_type)
        else:
            actual_response = Data

        if expected != actual_response:
            if self.getFileExtension("raster") in ("hdf", "nc"):
                self.skipTest("Skipping binary comparison for HDF or NetCDF file '%s'." % expected_path)
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
        logger.info("Checking HTTP Status ...")
        #pylint: disable=E1103
        self.assertEqual(self.response.status_code, 200)


class RasterTestCase(OWSTestCase):
    """
    Base class for test cases that expect a raster as response.
    """
    
    def getFileExtension(self, file_type):
        return "tif"
    
    def testBinaryComparisonRaster(self):
        if not self.isRequestConfigEnabled("binary_raster_comparison_enabled", True):
            self.skipTest("Binary raster comparison is explicitly disabled.")
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
            self.res_ds = gdal.Open(self.tmppath, gdal.GA_ReadOnly)
        except RuntimeError, e:
            self.fail("Response could not be opened with GDAL. Error was %s" % e)
        
        try:
            self.exp_ds = gdal.Open(exp_path, gdal.GA_ReadOnly)
        except RuntimeError:
            self.skipTest("Expected response in '%s' is not present" % exp_path)

class RectifiedGridCoverageTestCase(GDALDatasetTestCase):
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

class ReferenceableGridCoverageTestCase(GDALDatasetTestCase):
    def testSize(self):
        self._openDatasets()
        self.assertEqual((self.res_ds.RasterXSize, self.res_ds.RasterYSize),
                         (self.exp_ds.RasterXSize, self.exp_ds.RasterYSize))
    
    def testBandCount(self):
        self._openDatasets()
        self.assertEqual(self.res_ds.RasterCount, self.exp_ds.RasterCount)
        
    def testGCPs(self):
        self._openDatasets()
        self.assertEqual(self.res_ds.GetGCPCount(), self.exp_ds.GetGCPCount())
        
    def testGCPProjection(self):
        self._openDatasets()
        
        res_proj = self.res_ds.GetGCPProjection()
        if not res_proj:
            self.fail("Response Dataset has no GCP Projection defined")
        res_srs = osr.SpatialReference(res_proj)
        
        exp_proj = self.exp_ds.GetGCPProjection()
        if not exp_proj:
            self.fail("Expected Dataset has no GCP Projection defined")
        exp_srs = osr.SpatialReference(exp_proj)
        
        self.assert_(res_srs.IsSame(exp_srs))

class XMLTestCase(OWSTestCase):
    """
    Base class for test cases that expects XML output, which is parsed
    and validated against a schema definition.
    """
    
    def getXMLData(self):
        return self.response.content
    
    def testValidate(self, XMLData=None):
        logger.info("Validating XML ...")
        
        if XMLData is None:
            doc = etree.XML(self.getXMLData())
        else:
            doc = etree.XML(XMLData)
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
            if location == "../owsCoverages.xsd":
                location = "http://schemas.opengis.net/wcs/1.1/wcsAll.xsd"
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
        
    def testXMLComparison(self):
        self._testXMLComparison()

class SchematronTestMixIn(object): # requires to be mixed in with XMLTestCase
    """
    Mixin class for XML test cases that uses XML schematrons for validation.
    Use the `schematron_locations`
    """
    schematron_locations = ()
    
    def testSchematron(self):
        errors = []
        doc = etree.XML(self.getXMLData())
        
        schematron_def = etree.Element("schema", attrib={
                "queryBinding": "xslt2",
            }, nsmap={
                None: "http://purl.oclc.org/dsdl/schematron"
            }
        )
        etree.SubElement(schematron_def, "pattern")
        
# TODO: Check if this is even possible:
#        for ns, location in zip(self.schematron_locations[::2], self.schematron_locations[1::2]):
#            etree.SubElement(schematron_def, "import", attrib={
#                    "namespace": ns,
#                    "schemaLocation": location
#                }
#            )
        
        # TODO: ugly workaround. But otherwise, the doc is not recognized as schema
        schematron = etree.Schematron(etree.XML(etree.tostring(schematron_def)))
                    
        try:
            schematron.assertValid(doc)
        except etree.DocumentInvalid, e:
            errors.append(str(e))
        except etree.SchematronValidateError:
            self.skipTest("Schematron Testing is not enabled.")

        if len(errors):
            self.fail(str(errors))


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
        logger.info("Checking HTTP Status ...")
        #pylint: disable=E1103
        self.assertEqual(self.response.status_code, self.getExpectedHTTPStatus())
    
    def testExceptionCode(self):
        logger.info("Checking OWS Exception Code ...")
        decoder = XMLDecoder(self.getXMLData(), {
            "exceptionCode": {"xml_location": self.getExceptionCodeLocation(), "xml_type": "string"}
        })
        self.assertEqual(decoder.getValue("exceptionCode"), self.getExpectedExceptionCode())      

class HTMLTestCase(OWSTestCase):
    """
    HTML test cases expect to receive HTML text.
    """
    
    def getFileExtension(self, file_type):
        return "html"
    
    def testBinaryComparisonHTML(self):
        self._testBinaryComparison("html")

class MultipartTestCase(XMLTestCase):
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
    

    def _mangleXML( self , cbuffer ) : 
        """ remove variable parts of selected XML elements text and attributes """ 

        #define XML names to be used 

        N0 = "{http://www.opengis.net/gml/3.2}rangeSet/" \
             "{http://www.opengis.net/gml/3.2}File/" \
             "{http://www.opengis.net/gml/3.2}rangeParameters"

        N1 = "{http://www.opengis.net/gml/3.2}rangeSet/" \
             "{http://www.opengis.net/gml/3.2}File/" \
             "{http://www.opengis.net/gml/3.2}fileReference"

        N2 = "{http://www.opengis.net/wcs/1.1}Coverage/" \
             "{http://www.opengis.net/ows/1.1}Reference"

        HREF  = "{http://www.w3.org/1999/xlink}href"

        # define handy closures 

        def cropFileName( name ) : 
            base , _ , ext = name.rpartition(".")
            base , _ , _   = base.rpartition("_")
            return "%s.%s"%(base,ext) 

        def changeHref( e ) : 
            if e is not None : e.set( HREF , cropFileName( e.get( HREF ) ) )
                
        def changeText( e ) : 
            if e is not None: e.text = cropFileName( e.text )

        # parse XML Note: etree.parse respects the encoding reported in XML delaration!
        xml = etree.parse( StringIO( cbuffer ) )

        # mangle XML content to get rid of variable content

        # WCS 2.0.x - rangeSet/File
        changeHref( xml.find( N0 ) ) 
        changeText( xml.find( N1 ) )
        # WCS 1.1.x - Coverage/Reference 
        changeHref( xml.find( N2 ) ) 

        # output xml - force UTF-8 encoding including the XML delaration 
        return etree.tostring( xml , encoding="UTF-8" , xml_declaration=True )

    def _unpackMultipartContent( self , response ) : 

        content      = response.content
        content_type = response['Content-Type']

        # check the content type 
        if getMimeType( content_type ) \
            not in ( "multipart/mixed" , "multipart/related" ) :
            raise Exception , "Received content is neither mixed nor related multipart! Content-Type: %s" % content_type 

        # extract multipart boundary  
        boundary = getMultipartBoundary( content_type ) 
        
        # unpack the multipart content 
        for header,offset,size in mpUnpack(content,boundary) :
            match = RE_MIME_TYPE_XML.match( _getMime(header['content-type']) ) 
            if match is not None : 
                # store XML response 
                self.xmlData = content[offset:(offset+size)]
            else : 
                # store coverage data 
                self.imageData = content[offset:(offset+size)]


    def _setUpMultiparts(self):
        if self.isSetUp: return

        self._unpackMultipartContent( self.response ) 
        
        # mangle XML data 
        if self.xmlData : self.xmlData = self._mangleXML( self.xmlData ) 

        self.isSetUp = True

    
    def getFileExtension(self, part=None):
        if part == "xml":
            return "xml"
        elif part == "raster":
            return "tif"
        elif part == "TransactionDescribeCoverage":
            return "TransactionDescribeCoverage.xml"
        elif part == "TransactionDeleteCoverage":
            return "TransactionDeleteCoverage.xml"
        elif part == "TransactionDescribeCoverageDeleted":
            return "TransactionDescribeCoverageDeleted.xml"
        else:
            return "dat"
    
    def getXMLData(self):
        self._setUpMultiparts()
        return self.xmlData
    
    def getResponseData(self):
        self._setUpMultiparts()
        return self.imageData
        
class RectifiedGridCoverageMultipartTestCase(
    MultipartTestCase,
    RectifiedGridCoverageTestCase
):
    pass

class ReferenceableGridCoverageMultipartTestCase(
    MultipartTestCase,
    ReferenceableGridCoverageTestCase
):
    pass

#===============================================================================
# WCS-T
#===============================================================================

class WCSTransactionTestCase(XMLTestCase):
    """
    Base class for WCS Transactional test cases.
    """
    ADDmetaFile = None
    ADDtiffFile = None
    isAsync = False
    ID = None

    def setUp(self):
        super(WCSTransactionTestCase, self).setUp()
        logger.debug("WCSTransactionTestCase for ID: %s" % self.ID)
        
        if self.isAsync:
            from eoxserver.resources.processes.tracker import (
                dequeueTask, TaskStatus, startTask, stopTaskSuccessIfNotFinished
            )

            # get a pending task from the queue
            taskId = dequeueTask(1)[0]

            # create instance of TaskStatus class
            pStatus = TaskStatus( taskId )
            try:
                # get task parameters and change status to STARTED
                requestType , requestID , requestHandler , inputs = startTask( taskId )
                # load the handler
                module , _ , funct = requestHandler.rpartition(".")
                handler = getattr( __import__(module,fromlist=[funct]) , funct )
                # execute handler
                handler( pStatus , inputs )
                # if no terminating status has been set do it right now
                stopTaskSuccessIfNotFinished( taskId )
            except Exception as e :
                pStatus.setFailure( unicode(e) )
        
        # Add DescribeCoverage request/response
        request = "service=WCS&version=2.0.0&request=DescribeCoverage&coverageid=%s" % str( self.ID )
        self.responseDescribeCoverage = self.client.get('/ows?%s' % request)

        # Add GetCoverage request/response
        request = "service=WCS&version=2.0.0&request=GetCoverage&format=image/tiff&mediatype=multipart/mixed&coverageid=%s" % str( self.ID )
        self.responseGetCoverage = self.client.get('/ows?%s' % request)
        
        # Add delete coverage request/response
        requestBegin = """<wcst:Transaction service="WCS" version="1.1"
            xmlns:wcst="http://www.opengis.net/wcs/1.1/wcst" 
            xmlns:ows="http://www.opengis.net/ows/1.1" 
            xmlns:xlink="http://www.w3.org/1999/xlink" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
            <wcst:InputCoverages>
                <wcst:Coverage>
                    <ows:Identifier>"""
        requestEnd = """</ows:Identifier>
                    <wcst:Action codeSpace=\"http://schemas.opengis.net/wcs/1.1.0/actions.xml\">
                        Delete
                    </wcst:Action>"
                </wcst:Coverage>
            </wcst:InputCoverages>
        </wcst:Transaction>"""
        request =  requestBegin + self.ID + requestEnd
        self.responseDeleteCoverage = self.client.post('/ows', request, "text/xml")

        # Add DescribeCoverage request/response after delete
        request = "service=WCS&version=2.0.0&request=DescribeCoverage&coverageid=%s" % str( self.ID )
        self.responseDescribeCoverageDeleted = self.client.get('/ows?%s' % request)

    def getRequest(self):
        requestBegin = """<wcst:Transaction service="WCS" version="1.1"
            xmlns:wcst="http://www.opengis.net/wcs/1.1/wcst" 
            xmlns:ows="http://www.opengis.net/ows/1.1" 
            xmlns:xlink="http://www.w3.org/1999/xlink" 
            xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">
            <wcst:InputCoverages>
                <wcst:Coverage>
                    <ows:Identifier>"""
        requestMid1 = """</ows:Identifier>
                    <ows:Reference  xlink:href="file:///"""
        requestMid2 = """" xlink:role="urn:ogc:def:role:WCS:1.1:Pixels"/>"""
        requestMid3 = """<ows:Metadata  xlink:href="file:///"""
        requestMid4 = """" xlink:role="http://www.opengis.net/eop/2.0/EarthObservation"/>"""
        requestMid5 = """<wcst:Action codeSpace="http://schemas.opengis.net/wcs/1.1.0/actions.xml">Add</wcst:Action>
                </wcst:Coverage>
            </wcst:InputCoverages>"""
        requestAsync = """<wcst:ResponseHandler>http://NOTUSED</wcst:ResponseHandler>"""
        requestEnd = """</wcst:Transaction>"""        

        params =  requestBegin + self.ID + requestMid1 + self.getDataFullPath(self.ADDtiffFile) + requestMid2
        if self.ADDmetaFile is not None:
            params += requestMid3 + self.getDataFullPath(self.ADDmetaFile) + requestMid4
        params += requestMid5
        if self.isAsync:
            params += requestAsync
        params += requestEnd
        return (params, "xml")

    def getDataFullPath(self , path_to):
        return os.path.abspath( os.path.join( self.getDataFileDir() , path_to) )

    def testXMLComparison(self):
        # the TimeStamp and RequestId elements are set during ingestion and 
        # thus have to be explicitly unified
        tree = etree.fromstring(self.getXMLData())
        for node in tree.findall("{http://www.opengis.net/wcs/1.1/wcst}RequestId"):
            node.text = "identifier"
        for node in tree.findall("{http://www.opengis.net/wcs/1.1/wcst}TimeStamp"):
            node.text = "2011-01-01T00:00:00Z"
        self.response.content = etree.tostring(tree, encoding="ISO-8859-1")
        super(WCSTransactionTestCase, self).testXMLComparison()

    def testResponseIdComparisonAdd(self):
        """
        Tests that the <ows:Identifier> in the XML request and response is the 
        same
        """
        logger.debug("IDCompare testResponseIdComparison for ID: %s" % self.ID)
        self._testResponseIdComparison( self.ID  , self.getXMLData()  )

    def testStatusDescribeCoverage(self):
        """
        Tests that the inserted coverage is available in a DescribeCoverage
        request
        """
        #pylint: disable=E1103
        self.assertEqual(self.responseDescribeCoverage.status_code, 200)

    def testValidateDescribeCoverage(self):
        self.testValidate(self.responseDescribeCoverage.content)

    def testXMLComparisonDescribeCoverage(self):
        #self._testBinaryComparison("TransactionDescribeCoverage", self.responseDescribeCoverage.content)
        self._testXMLComparison( "TransactionDescribeCoverage" , self.responseDescribeCoverage.content ) 

    def testStatusGetCoverage(self):
        """
        Validate the inserted coverage via a GetCoverage request
        """
        #pylint: disable=E1103
        self.assertEqual(self.responseGetCoverage.status_code, 200)

    def testStatusDeleteCoverage(self):
        """
        Test to delete the previously inserted coaverage
        """
        #pylint: disable=E1103
        self.assertEqual(self.responseDeleteCoverage.status_code, 200)

    def testValidateDeleteCoverage(self):
        self.testValidate(self.responseDeleteCoverage.content)

    def testXMLComparisonDeleteCoverage(self):
        tree = etree.fromstring(self.responseDeleteCoverage.content)
        for node in tree.findall("{http://www.opengis.net/wcs/1.1/wcst}RequestId"):
            node.text = "identifier"
        #self._testBinaryComparison("TransactionDeleteCoverage", etree.tostring(tree, encoding="ISO-8859-1"))
        self._testXMLComparison( "TransactionDeleteCoverage" , etree.tostring(tree, encoding="ISO-8859-1"))

    def testResponseIdComparisonDelete(self):
        """
        Tests that the <ows:Identifier> in the XML request and response is the 
        same
        """
        logger.debug("IDCompare testResponseIdComparison for ID: %s" % self.ID)
        self._testResponseIdComparison( self.ID , self.responseDeleteCoverage.content )

    def testStatusDescribeCoverageDeleted(self):
        """
        Tests that the deletec coverage is not longer available in a 
        DescribeCoverage request
        """
        #pylint: disable=E1103
        self.assertEqual(self.responseDescribeCoverageDeleted.status_code, 404)

    def testValidateDescribeCoverageDeleted(self):
        self.testValidate(self.responseDescribeCoverageDeleted.content)

    def testXMLComparisonDescribeCoverageDeleted(self):
        #self._testBinaryComparison("TransactionDescribeCoverageDeleted", self.responseDescribeCoverageDeleted.content)
        self._testXMLComparison( "TransactionDescribeCoverageDeleted" , self.responseDescribeCoverageDeleted.content )

    def _testResponseIdComparison(self , id , rcontent ):
        """
        Tests that the <ows:Identifier> in the XML request and response is the 
        same
        """
        logger.debug("_testResponseIdComparison for ID: %s" % id)
        tree = etree.fromstring( rcontent )
        for node in tree.findall("{http://www.opengis.net/ows/1.1}Identifier"):
            self.assertEqual( node.text, id )

class WCSTransactionRectifiedGridCoverageTestCase(
    RectifiedGridCoverageMultipartTestCase,
    WCSTransactionTestCase
):
    """
    WCS-T test cases for RectifiedGridCoverages
    """
    # Overwrite _setUpMultiparts() to return the GetCoverage response to be used
    # in MultipartTestCase tests
    def _setUpMultiparts(self):
        if self.isSetUp: return

        self._unpackMultipartContent( self.responseGetCoverage ) 

        self.isSetUp = True

    def getXMLData(self):
        return self.response.content

class WCSTransactionReferenceableGridCoverageTestCase(
    ReferenceableGridCoverageMultipartTestCase,
    WCSTransactionTestCase
):
    """
    WCS-T test cases for ReferenceableGridCoverages
    """
    # Overwrite _setUpMultiparts() to return the GetCoverage response to be used
    # in MultipartTestCase tests
    def _setUpMultiparts(self):
        if self.isSetUp: return

        self._unpackMultipartContent( self.responseGetCoverage ) 

        self.isSetUp = True

    def getXMLData(self):
        return self.response.content

#===============================================================================
# WCS 2.0
#===============================================================================
    
class WCS20DescribeEOCoverageSetSubsettingTestCase(XMLTestCase):
    def getExpectedCoverageIds(self):
        return []
    
    def testCoverageIds(self):
        logger.info("Checking Coverage Ids ...")
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
    def testXMLComparison(self):
        # The timePosition tag depends on the actual time the request was 
        # answered. It has to be explicitly unified.
        tree = etree.fromstring(self.getXMLData())
        for node in tree.findall("{http://www.opengis.net/gmlcov/1.0}metadata/" \
                                 "{http://www.opengis.net/gmlcov/1.0}Extension/" \
                                 "{http://www.opengis.net/wcseo/1.0}EOMetadata/" \
                                 "{http://www.opengis.net/wcseo/1.0}lineage/" \
                                 "{http://www.opengis.net/gml/3.2}timePosition"):
            node.text = "2011-01-01T00:00:00Z"
        self.xmlData = etree.tostring(tree, encoding="ISO-8859-1")
        
        super(WCS20GetCoverageMultipartTestCase, self).testXMLComparison()

class WCS20GetCoverageRectifiedGridCoverageMultipartTestCase(
    WCS20GetCoverageMultipartTestCase, 
    RectifiedGridCoverageTestCase
):
    pass

class WCS20GetCoverageReferenceableGridCoverageMultipartTestCase(
    WCS20GetCoverageMultipartTestCase, 
    ReferenceableGridCoverageTestCase
):
    pass

class RasdamanTestCaseMixIn(object):
    fixtures = BASE_FIXTURES + ["testing_rasdaman_coverages.json"]
    
    def setUp(self):
        # TODO check if connection to DB server is possible
        # TODO check if datasets are configured within the DB

        gdal.AllRegister()
        if gdal.GetDriverByName("RASDAMAN") is None:
            self.skipTest("Rasdaman driver is not enabled.")
        
        if not self.isRequestConfigEnabled("rasdaman_enabled"):
            self.skipTest("Rasdaman tests are not enabled. Use the "
                          "configuration option 'rasdaman_enabled' to allow "
                          "rasdaman tests.")
        
        super(RasdamanTestCaseMixIn, self).setUp()
    
#===============================================================================
# WMS test classes
#===============================================================================

class WMS11GetMapTestCase(RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    time = None
    dim_band = None
    
    swap_axes = True
    
    httpHeaders = None
    
    def getFileExtension(self, part=None):
        return mimetypes.guess_extension(self.frmt, False)[1:]
    
    def getRequest(self):
        params = "service=WMS&request=GetMap&version=1.1.1&" \
                 "layers=%s&styles=%s&srs=%s&bbox=%s&" \
                 "width=%d&height=%d&format=%s" % (
                     ",".join(self.layers), ",".join(self.styles), self.crs,
                     ",".join(map(str, self.bbox)),
                     self.width, self.height, self.frmt
                 )
        
        if self.time:
            params += "&time=%s" % self.time
            
        if self.dim_band:
            params += "&dim_band=%s" % self.dim_band
        
        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)

class WMS13GetMapTestCase(RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    time = None
    dim_band = None
    
    swap_axes = True
    
    httpHeaders = None
    
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
        
        if self.time:
            params += "&time=%s" % self.time
            
        if self.dim_band:
            params += "&dim_band=%s" % self.dim_band
        
        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)

class WMS13ExceptionTestCase(ExceptionTestCase):
    def getExceptionCodeLocation(self):
        return "/{http://www.opengis.net/ogc}ServiceException/@code"
