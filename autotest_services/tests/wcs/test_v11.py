#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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
import base as wcsbase
import mapscript


#===============================================================================
# WCS 1.1
#===============================================================================

class WCS11GetCapabilitiesValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCapabilities"
        return (params, "kvp")

class WCS11GetCapabilitiesEmptyTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 1.1 GetCapabilities response (see #41)"""
    fixtures = testbase.BASE_FIXTURES

    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCapabilities"
        return (params, "kvp")

class WCS11DescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=DescribeCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        return (params, "kvp")

class WCS11DescribeCoverageMosaicTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=DescribeCoverage&identifier=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

class WCS11GetCoverageDatasetTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=32,12,46.5,28,urn:ogc:def:crs:EPSG::4326&format=image/tiff"
        return (params, "kvp")

class WCS11GetCoverageMosaicTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_reduced_RGB&boundingbox=32,-4,46.5,28,urn:ogc:def:crs:EPSG::4326&format=image/tiff"
        return (params, "kvp")

class WCS11GetCoverageDatasetSubsetTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=0,0,550,440,urn:ogc:def:crs:OGC::imageCRS&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
        return (params, "kvp")

class WCS11GetCoverageDatasetSubsetEPSG4326TestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=32,12,46.5,28,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
        return (params, "kvp")

class WCS11GetCoverageMosaicSubsetTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_reduced_RGB&boundingbox=300,200,700,350,urn:ogc:def:crs:OGC::imageCRS&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
        return (params, "kvp")

class WCS11GetCoverageMosaicSubsetEPSG4326TestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_reduced_RGB&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

#===============================================================================
# WCS 1.1: Exceptions
#===============================================================================

class WCS11DescribeCoverageNoSuchCoverageFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=DescribeCoverage&identifier=INVALID&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"


class WCS11GetCoverageNoSuchCoverageFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=GetCoverage&identifier=INVALID&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

#NOTE: Support for Referenceable Datasets in WCS < 2.0.0 not avaiable.
#      Any attempt to access Ref.DS via WCS 1.x should be treated as
#      non-existing coverage.
class WCS11DescribeCoverageReferenceableFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=DescribeCoverage&identifier=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS11GetCoverageReferenceableFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=GetCoverage&identifier=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&boundingbox=80,80,90,90,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS11GetCoverageBBoxFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=80,80,90,90,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        # newer versions return a different exception code and message
        if mapscript.MS_VERSION_NUM >= 60400:
            return "bbox"
        return "NoApplicableCode"

class WCS11GetCoverageFormatUnsupportedFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=GetCoverage&identifier=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/jpeg&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

class WCS11GetCoverageFormatUnknownFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=1.1.2&request=GetCoverage&identifier=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=unknown&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 1.1 WCS Transaction tests
#===============================================================================
'''
class WCS11TransactionRectifiedDatasetTestCase(testbase.WCSTransactionRectifiedGridCoverageTestCase):
    """ This test case shall test the synchronous inserting of a new
        RectifiedGridCoverage by means of the WCS 1.1 Transaction operation
        ("Add" action).
    """
    fixtures = testbase.BASE_FIXTURES
    ID = "RECTIFIED_MERIS_ID"
    ADDtiffFile = "meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"
    ADDmetaFile = "meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml"

class WCS11TransactionAsyncRectifiedDatasetTestCase(testbase.WCSTransactionRectifiedGridCoverageTestCase):
    """ This test case shall test the asynchronous inserting of a new
        RectifiedGridCoverage by means of the WCS 1.1 Transaction operation
        ("Add" action).
    """
    fixtures = testbase.BASE_FIXTURES
    ID = "RECTIFIED_MERIS_ID"
    ADDtiffFile = "meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.tif"
    ADDmetaFile = "meris/mosaic_MER_FRS_1P_reduced_RGB/mosaic_ENVISAT-MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced.xml"
    isAsync = True

class WCS11TransactionReferenceableDatasetTestCase(testbase.WCSTransactionReferenceableGridCoverageTestCase):
    """ This test case shall test the synchronous inserting of a new
        ReferenceableGridCoverage by means of the WCS 1.1 Transaction operation
        ("Add" action).
    """
    fixtures = testbase.BASE_FIXTURES
    ID = "REFERENCEABLE_ASAR_ID"
    ADDtiffFile = "asar/ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775.tiff"
'''

#===============================================================================
# WCS 1.1 - POST
#===============================================================================

class WCS11PostGetCapabilitiesValidTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 1.1 GetCapabilities response via POST.
    """
    def getRequest(self):
        params = """<ns:GetCapabilities xmlns:ns="http://www.opengis.net/wcs/1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCapabilities.xsd"
          service="WCS" version="1.1.2"/>"""
        return (params, "xml")

class WCS11PostDescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 1.1 DescribeCoverage response for a
       wcseo:RectifiedDataset via POST.
    """
    def getRequest(self):
        params = """<DescribeCoverage xmlns="http://www.opengis.net/wcs/1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsDescribeCoverage.xsd"
          service="WCS" version="1.1.2">
            <Identifier>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</Identifier>
          </DescribeCoverage>"""
        return (params, "xml")

class WCS11PostDescribeCoverageMosaicTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 1.1 DescribeCoverage response for a
       wcseo:RectifiedStitchedMosaic via POST.
    """
    def getRequest(self):
        params = """<DescribeCoverage xmlns="http://www.opengis.net/wcs/1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsDescribeCoverage.xsd"
          service="WCS" version="1.1.2">
            <Identifier>mosaic_MER_FRS_1P_reduced_RGB</Identifier>
          </DescribeCoverage>"""
        return (params, "xml")

class WCS11PostGetCoverageDatasetTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<GetCoverage xmlns="http://www.opengis.net/wcs/1.1"
          xmlns:ows="http://www.opengis.net/ows/1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCoverage.xsd"
          service="WCS" version="1.1.2">
            <ows:Identifier>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</ows:Identifier>
            <DomainSubset>
              <ows:BoundingBox crs="urn:ogc:def:crs:EPSG::4326">
                <ows:LowerCorner>32 12</ows:LowerCorner>
                <ows:UpperCorner>46.5 28</ows:UpperCorner>
              </ows:BoundingBox>
            </DomainSubset>
            <Output format="image/tiff" />
          </GetCoverage>"""
        return (params, "xml")

class WCS11PostGetCoverageMosaicTestCase(wcsbase.WCS11GetCoverageMixIn, testbase.RectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<GetCoverage xmlns="http://www.opengis.net/wcs/1.1"
          xmlns:ows="http://www.opengis.net/ows/1.1"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCoverage.xsd"
          service="WCS" version="1.1.2">
            <ows:Identifier>mosaic_MER_FRS_1P_reduced_RGB</ows:Identifier>
            <DomainSubset>
              <ows:BoundingBox crs="urn:ogc:def:crs:EPSG::4326">
                <ows:LowerCorner>32 -4</ows:LowerCorner>
                <ows:UpperCorner>46.5 28</ows:UpperCorner>
              </ows:BoundingBox>
            </DomainSubset>
            <Output format="image/tiff" />
          </GetCoverage>"""
        return (params, "xml")

# TODO: Not working because of a bug in MapServer
#class WCS11PostGetCoverageDatasetSubsetTestCase(eoxstest.RectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = """<GetCoverage xmlns="http://www.opengis.net/wcs/1.1"
#          xmlns:ows="http://www.opengis.net/ows/1.1"
#          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCoverage.xsd"
#          service="WCS" version="1.1.2">
#            <ows:Identifier>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</ows:Identifier>
#            <DomainSubset>
#              <ows:BoundingBox crs="urn:ogc:def:crs:OGC::imageCRS">
#                <ows:LowerCorner>0 0</ows:LowerCorner>
#                <ows:UpperCorner>550 440</ows:UpperCorner>
#              </ows:BoundingBox>
#            </DomainSubset>
#            <Output format="image/tiff">
#              <GridCRS>
#                <GridBaseCRS>urn:ogc:def:crs:EPSG::4326</GridBaseCRS>
#                <GridType>urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs</GridType>
#                <GridOrigin>0 0</GridOrigin>
#                <GridOffsets>2 2</GridOffsets>
#                <GridCS>urn:ogc:def:crs:OGC::imageCRS</GridCS>
#              </GridCRS>
#            </Output>
#          </GetCoverage>"""
#        return (params, "xml")

#class WCS11PostGetCoverageDatasetSubsetEPSG4326TestCase(eoxstest.RectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = """"""
##boundingbox=32,12,46.5,28,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
#        return (params, "xml")

#class WCS11PostGetCoverageMosaicSubsetTestCase(eoxstest.RectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = """"""
##boundingbox=300,200,700,350,urn:ogc:def:crs:OGC::imageCRS&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
#        return (params, "xml")

#class WCS11PostGetCoverageMosaicSubsetEPSG4326TestCase(eoxstest.RectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = """"""
##boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
#        return (params, "xml")
