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

import eoxserver.services.testbase as eoxstest
from eoxserver.testing.core import BASE_FIXTURES
import unittest

from urllib import quote

#===============================================================================
# WCS 1.0
#===============================================================================

class WCS10GetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCS10GetCapabilitiesEmptyTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 1.0 GetCapabilities response (see #41)"""
    fixtures = BASE_FIXTURES
    
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCS10DescribeCoverageDatasetTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=DescribeCoverage&coverage=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        return (params, "kvp")

class WCS10DescribeCoverageMosaicTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=DescribeCoverage&coverage=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS10GetCoverageDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=image/tiff"
        return (params, "kvp")

class WCS10GetCoverageMosaicTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1P_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=image/tiff"
        return (params, "kvp")

#===============================================================================
# WCS 1.1
#===============================================================================

class WCS11GetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCapabilities"
        return (params, "kvp")
    
class WCS11GetCapabilitiesEmptyTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 1.1 GetCapabilities response (see #41)"""
    fixtures = BASE_FIXTURES
    
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCapabilities"
        return (params, "kvp")

class WCS11DescribeCoverageDatasetTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=DescribeCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        return (params, "kvp")

class WCS11DescribeCoverageMosaicTestCase(eoxstest.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=DescribeCoverage&identifier=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS11GetCoverageDatasetTestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&crs=epsg:4326&bbox=12,32,28,46.5&format=image/tiff"
        return (params, "kvp")

class WCS11GetCoverageMosaicTestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&format=image/tiff"
        return (params, "kvp")

class WCS11GetCoverageDatasetSubsetTestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=0,0,550,440,urn:ogc:def:crs:OGC::imageCRS&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
        return (params, "kvp")

class WCS11GetCoverageDatasetSubsetEPSG4326TestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&boundingbox=32,12,46.5,28,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
        return (params, "kvp")

class WCS11GetCoverageMosaicSubsetTestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_RGB_reduced&boundingbox=300,200,700,350,urn:ogc:def:crs:OGC::imageCRS&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
        return (params, "kvp")

class WCS11GetCoverageMosaicSubsetEPSG4326TestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.1.2&request=GetCoverage&identifier=mosaic_MER_FRS_1P_RGB_reduced&boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&format=image/tiff&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridBaseCRS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        return (params, "kvp")

#===============================================================================
# WCS 2.0 Get Capabilities
#===============================================================================

class WCS20GetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP GetCapabilities response"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCS20GetCapabilitiesEmptyTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 2.0 EO-AP GetCapabilities response (see #41)"""
    fixtures = BASE_FIXTURES
    
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationOldStyleTestCase(eoxstest.XMLTestCase):
    """This test shall check old style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&version=3.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationNewStyleTestCase(eoxstest.XMLTestCase):
    """This test shall check new style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&acceptversions=2.0.0,1.1.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationFaultTestCase(eoxstest.ExceptionTestCase):
    """This test shall check new style version negotiation. A valid ows:ExceptionReport shall be returned"""
    def getRequest(self):
        params = "service=wcs&acceptversions=3.0.0&request=GetCapabilities"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "VersionNegotiationFailed"

#===============================================================================
# WCS 2.0 DescribeCoverage
#===============================================================================
    
class WCS20DescribeCoverageDatasetTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeCoverageMosaicTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedStitchedMosaic."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS20DescribeCoverageDatasetSeriesFaultTestCase(eoxstest.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a non-coverage. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1P_reduced"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"
        
class WCS20DescribeCoverageFaultTestCase(eoxstest.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a coverage that does not exist. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=some_coverage"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS20DescribeCoverageMissingParameterFaultTestCase(eoxstest.ExceptionTestCase):
    """This test shall yield a valid ows:ExceptionReport for a missing parameter"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

#===============================================================================
# WCS 2.0 DescribeEOCoverageSet 
#===============================================================================

class WCS20DescribeEOCoverageSetDatasetTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDataset"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetMosaicTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetDatasetSeriesTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDatasetSeries."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetFaultTestCase(eoxstest.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription set for an wcseo-Object that does not exist. It shall yield a valid ows:ExceptionReport."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=some_eo_object"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS20DescribeEOCoverageSetMissingParameterFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsOverlapsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=overlaps"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsContainsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetOverlapsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")&containment=overlaps"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetContainsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")&containment=contains"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetOverlapsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=overlaps"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetContainsTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-22T09:22:00Z\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(11,33)&containment=contains"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        ]

class WCS20DescribeEOCoverageSetIncorrectTemporalSubsetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(2006-08-01,2006-08-22)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"
    
class WCS20DescribeEOCoverageSetInvalidTemporalSubsetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-31-31\")"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class WCS20DescribeEOCoverageSetIncorrectSpatialSubsetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(some_lat,some_other_lat)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class WCS20DescribeEOCoverageSetInvalidSpatialSubsetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,32)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

# EOxServer allows and understands certain additional axis labels like "lat", or "long".
class WCS20DescribeEOCoverageSetInvalidAxisLabelFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=x_axis,http://www.opengis.net/def/crs/EPSG/0/4326(32,47)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidAxisLabel"
    
    
#===============================================================================
# WCS 2.0: Paging testcases
#===============================================================================

class WCS20DescribeEOCoverageSetDatasetPagingCountTestCase(eoxstest.WCS20DescribeEOCoverageSetPagingTestCase):
    def getExpectedCoverageCount(self):
        return 2
    
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&count=2"
        return (params, "kvp")

#===============================================================================
# WCS 2.0: Section test cases
#===============================================================================

class WCS20DescribeEOCoverageSetSectionsAllTestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcs:CoverageDescriptions",
            "wcseo:DatasetSeriesDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=All"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsAll2TestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcs:CoverageDescriptions",
            "wcseo:DatasetSeriesDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions,DatasetSeriesDescriptions"
        return (params, "kvp")
    
class WCS20DescribeEOCoverageSetSectionsAll3TestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcs:CoverageDescriptions",
            "wcseo:DatasetSeriesDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=All,DatasetSeriesDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsAll4TestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcs:CoverageDescriptions",
            "wcseo:DatasetSeriesDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions,All"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsCoverageDescriptionsTestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcs:CoverageDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsDatasetSeriesDescriptionsTestCase(eoxstest.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "wcseo:DatasetSeriesDescriptions"
        ]
        
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=DatasetSeriesDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&sections=WrongSection"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"


class WCS20DescribeEOCoverageSetDatasetUniqueTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase): 
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed,MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetDatasetOutOfSubsetTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed&ubset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(0,1)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(0,1)"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return []
    
class WCS20DescribeEOCoverageSetDatasetSeriesStitchedMosaicTestCase(eoxstest.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced,mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
            "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

#===============================================================================
# WCS 2.0: Exceptions
#===============================================================================

class WCS20GetCoverageFormatMissingFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class WCS20GetCoverageFormatUnsupportedFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/jpeg"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

class WCS20GetCoverageFormatUnknownFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=unknown"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Simple requests
#===============================================================================

class WCS20GetCoverageMosaicTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff"
        return (params, "kvp")

class WCS20GetCoverageDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"
        return (params, "kvp")

#==============================================================================
# WCS 2.0: Formats
#==============================================================================

class WCS20GetCoverageJPEG2000TestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/jp2"
        return (params, "kvp")
    
    def getFileExtension(self, part=None):
        return "jp2"

class WCS20GetCoverageNetCDFTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=application/x-netcdf"
        return (params, "kvp")
    
    def getFileExtension(self, part=None):
        return "nc"

class WCS20GetCoverageHDFTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=application/x-hdf"
        return (params, "kvp")
    
    def getFileExtension(self, part=None):
        return "hdf"

class WCS20GetCoverageCompressionLZWTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=%s" % quote("image/tiff;compress=LZW")
        return (params, "kvp")

class WCS20GetCoverageCompressionJPEGTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=%s" % quote("image/tiff;compress=JPEG;jpeg_quality=50")
        return (params, "kvp")

class WCS20GetCoverageTiledTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=%s" % quote ("image/tiff;tiled=YES")
        return (params, "kvp")

#===============================================================================
# WCS 2.0: Multipart requests
#===============================================================================

class WCS20GetCoverageMultipartMosaicTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/mixed"
        return (params, "kvp")

class WCS20GetCoverageMultipartDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed"
        return (params, "kvp")

# TODO: wrong multipart parameters only result in non-multipart images. Uncomment, when implemented
#class WCS20GetCoverageWrongMultipartParameterFaultTestCase(eoxstest.ExceptionTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/something"
#        return (params, "kvp")
#
#    def getExpectedExceptionCode(self):
#        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Subset requests
#===============================================================================

class WCS20GetCoverageSubsetDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageMultipartSubsetMosaicTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/mixed&subset=x(100,1000)&subset=y(0,99)"
        return (params, "kvp")

class WCS20GetCoverageMultipartSubsetDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326DatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326MosaicTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(0,30)"
        return (params, "kvp")

class WCS20GetCoverageSubsetInvalidEPSGFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/99999(38,40)&subset=y,http://www.opengis.net/def/crs/EPSG/0/99999(20,22)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: OutputCRS
#===============================================================================

class WCS20GetCoverageOutputCRSDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035"
        return (params, "kvp")

#===============================================================================
# WCS 2.0: Size
#===============================================================================

class WCS20GetCoverageSizeDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&size=x(200)&size=y(200)"
        return (params, "kvp")

class WCS20GetCoverageSizeMosaicTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(200)&size=y(400)"
        return (params, "kvp")

class WCS20GetCoverageSubsetSizeDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=x(20)&size=y(20)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326SizeDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&size=lat(20)&size=long(20)"
        return (params, "kvp")

class WCS20GetCoverageInvalidSizeFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(1.11)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Resolution
#===============================================================================

class WCS20GetCoverageResolutionDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")
    
class WCS20GetCoverageResolutionMosaicTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageSubsetResolutionDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326ResolutionLatLonDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&resolution=lat(0.01)&resolution=long(0.01)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326ResolutionInvalidAxisDatasetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&resolution=x(0.01)&resolution=y(0.01)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Rangesubset
#===============================================================================

class WCS20GetCoverageRangeSubsetIndicesDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=1,2,3"
        return (params, "kvp")

class WCS20GetCoverageRangeSubsetNamesDatasetTestCase(eoxstest.GDALDatasetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

class WCS20GetCoverageMultipartRangeSubsetNamesDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

class WCS20GetCoverageSubsetSizeResolutionOutputCRSRangeSubsetIndicesDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=y(100)&resolution=x(0.1)&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&rangesubset=1,2,3&mediatype=multipart/mixed"
        return (params, "kvp")

#===============================================================================
# WCS 2.0 Rasdaman test cases
#===============================================================================

class WCS20GetCoverageRasdamanMultipartDatasetTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed"
        return (params, "kvp")   

class WCS20GetCoverageRasdamanMultipartDatasetSubsetTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSizeTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&size=x(100)&size=y(100)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetResolutionTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetOutputCRSTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSubsetSizeTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(200,300)&size=x(20)&size=y(20)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSubsetResolutionTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(200,300)&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetRangeSubsetTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/mixed&rangesubset=1"
        return (params, "kvp")

class WCS20GetCoverageRasdamanSubsetSizeResolutionOutputCRSRangeSubsetIndicesDatasetTestCase(eoxstest.RasdamanTestCaseMixIn, eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=y(100)&resolution=x(0.1)&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&rangesubset=1,2,3&mediatype=multipart/mixed"
        return (params, "kvp")

#===============================================================================
# WCS 2.0 Referenceable Grid Coverages
#===============================================================================

#class WCS20GetCoverageReferenceableDatasetTestCase(eoxstest.GDALDatasetTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff"
#        return (params, "kvp")

#class WCS20GetCoverageReferenceableDatasetImageCRSSubsetTestCase(eoxstest.GDALDatasetTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&subset=x(0,99)&subset=y(0,99)"
#        return (params, "kvp")

#class WCS20GetCoverageReferenceableDatasetGeogCRSSubsetTestCase(eoxstest.GDALDatasetTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,22)&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(-36,-32)"
#        return (params, "kvp")

#===============================================================================
# WCS 2.0 - POST
#===============================================================================

class WCS20PostGetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP GetCapabilities response
       via POST.
    """
    def getRequest(self):
        params = """<ns:GetCapabilities updateSequence="u2001" service="WCS"
          xmlns:ns="http://www.opengis.net/wcs/2.0"
          xmlns:ns1="http://www.opengis.net/ows/2.0">
            <ns1:AcceptVersions><ns1:Version>2.0.0</ns1:Version></ns1:AcceptVersions>
          </ns:GetCapabilities>
        """        
        return (params, "xml")

class WCS20PostDescribeCoverageDatasetTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response 
       for a wcseo:RectifiedDataset via POST.
    """
    def getRequest(self):
        params = """<ns:DescribeCoverage 
           xmlns:ns="http://www.opengis.net/wcs/2.0" service="WCS" version="2.0.0">
         <ns:CoverageId>MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed</ns:CoverageId>
        </ns:DescribeCoverage>"""
        return (params, "xml")

class WCS20PostDescribeEOCoverageSetDatasetSeriesTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response
    for a wcseo:RectifiedDatasetSeries via POST.
    """
    def getRequest(self):
        params = """<wcseo:DescribeEOCoverageSet service="WCS" version="2.0.0" count="100"
           xmlns:wcseo="http://www.opengis.net/wcseo/1.0"
           xmlns:wcs="http://www.opengis.net/wcs/2.0">     
          <wcseo:eoId>MER_FRS_1P_reduced</wcseo:eoId>
          <wcseo:containment>OVERLAPS</wcseo:containment>
          <wcseo:Sections>
            <wcseo:Section>All</wcseo:Section>
          </wcseo:Sections>
          <wcs:DimensionTrim>
            <wcs:Dimension>Long</wcs:Dimension>
            <wcs:TrimLow>16</wcs:TrimLow>
            <wcs:TrimHigh>18</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>Lat</wcs:Dimension>
            <wcs:TrimLow>46</wcs:TrimLow>
            <wcs:TrimHigh>48</wcs:TrimHigh>
          </wcs:DimensionTrim>
        </wcseo:DescribeEOCoverageSet>"""
        return (params, "xml")

class WCS20PostGetCoverageMultipartDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.0"
           xmlns:wcs="http://www.opengis.net/wcs/2.0">
          <wcs:mediatype>multipart/mixed</wcs:mediatype>
          <wcs:Format>image/tiff</wcs:Format>
          <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>Long</wcs:Dimension>
            <wcs:TrimLow>16</wcs:TrimLow>
            <wcs:TrimHigh>18</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>Lat</wcs:Dimension>
            <wcs:TrimLow>46</wcs:TrimLow>
            <wcs:TrimHigh>48</wcs:TrimHigh>
          </wcs:DimensionTrim>
        </wcs:GetCoverage>"""
        return (params, "xml")

#===============================================================================
# WCS 1.1 - POST
#===============================================================================

class WCS11PostGetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 1.1 GetCapabilities response via POST.
    """
    def getRequest(self):
        params = """<ns:GetCapabilities xmlns:ns="http://www.opengis.net/wcs/1.1" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCapabilities.xsd" 
          service="WCS" version="1.1.2"/>"""
        return (params, "xml")
        
class WCS11PostDescribeCoverageDatasetTestCase(eoxstest.XMLTestCase):
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

class WCS11PostDescribeCoverageMosaicTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WCS 1.1 DescribeCoverage response for a 
       wcseo:RectifiedStitchedMosaic via POST.
    """
    def getRequest(self):
        params = """<DescribeCoverage xmlns="http://www.opengis.net/wcs/1.1" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsDescribeCoverage.xsd" 
          service="WCS" version="1.1.2">
            <Identifier>mosaic_MER_FRS_1P_RGB_reduced</Identifier>
          </DescribeCoverage>"""
        return (params, "xml")

class WCS11PostGetCoverageDatasetTestCase(eoxstest.MultipartTestCase):
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
            <Output format="image/tiff"/>
          </GetCoverage>"""
        return (params, "xml")

class WCS11PostGetCoverageMosaicTestCase(eoxstest.MultipartTestCase):
    def getRequest(self):
        params = """<GetCoverage xmlns="http://www.opengis.net/wcs/1.1" 
          xmlns:ows="http://www.opengis.net/ows/1.1" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCoverage.xsd" 
          service="WCS" version="1.1.2">
            <ows:Identifier>mosaic_MER_FRS_1P_RGB_reduced</ows:Identifier>
            <DomainSubset>
              <ows:BoundingBox crs="urn:ogc:def:crs:EPSG::4326">
                <ows:LowerCorner>32 -4</ows:LowerCorner>
                <ows:UpperCorner>46.5 28</ows:UpperCorner>
              </ows:BoundingBox>
            </DomainSubset>
            <Output format="image/tiff"/>
          </GetCoverage>"""
        return (params, "xml")

# TODO: Not working because of a bug in MapServer
#class WCS11PostGetCoverageDatasetSubsetTestCase(eoxstest.MultipartTestCase):
    #def getRequest(self):
        #params = """<GetCoverage xmlns="http://www.opengis.net/wcs/1.1" 
          #xmlns:ows="http://www.opengis.net/ows/1.1" 
          #xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          #xsi:schemaLocation="http://www.opengis.net/wcs/1.1 http://schemas.opengis.net/wcs/1.1/wcsGetCoverage.xsd" 
          #service="WCS" version="1.1.2">
            #<ows:Identifier>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</ows:Identifier>
            #<DomainSubset>
              #<ows:BoundingBox crs="urn:ogc:def:crs:OGC::imageCRS">
                #<ows:LowerCorner>0 0</ows:LowerCorner>
                #<ows:UpperCorner>550 440</ows:UpperCorner>
              #</ows:BoundingBox>
            #</DomainSubset>
            #<Output format="image/tiff">
              #<GridCRS>
                #<GridBaseCRS>urn:ogc:def:crs:EPSG::4326</GridBaseCRS>
                #<GridType>urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs</GridType>
                #<GridOrigin>0 0</GridOrigin>
                #<GridOffsets>2 2</GridOffsets>
                #<GridCS>urn:ogc:def:crs:OGC::imageCRS</GridCS>
              #</GridCRS>
            #</Output>
          #</GetCoverage>"""
        #return (params, "xml")

#class WCS11PostGetCoverageDatasetSubsetEPSG4326TestCase(eoxstest.MultipartTestCase):
    #def getRequest(self):
        #params = """"""
##boundingbox=32,12,46.5,28,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=46.5,12&GridOffsets=0.06,0.06"
        #return (params, "xml")

#class WCS11PostGetCoverageMosaicSubsetTestCase(eoxstest.MultipartTestCase):
    #def getRequest(self):
        #params = """"""
##boundingbox=300,200,700,350,urn:ogc:def:crs:OGC::imageCRS&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=0,0&GridOffsets=2,2"
        #return (params, "xml")

#class WCS11PostGetCoverageMosaicSubsetEPSG4326TestCase(eoxstest.MultipartTestCase):
    #def getRequest(self):
        #params = """"""
##boundingbox=35,10,42,20,urn:ogc:def:crs:EPSG::4326&GridCS=urn:ogc:def:crs:OGC::imageCRS&GridType=urn:ogc:def:method:WCS:1.1:2dGridIn2dCrs&GridOrigin=40,10&GridOffsets=-0.06,0.06"
        #return (params, "xml")

#===============================================================================
# WMS
#===============================================================================

class WMS13GetCapabilitiesValidTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid WMS 1.3 GetCapabilities response"""
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetCapabilities"
        return (params, "kvp")

class WMS13GetCapabilitiesEmptyTestCase(eoxstest.XMLTestCase):
    """This test shall retrieve a valid but empty WMS 1.3 GetCapabilities response (see #41)"""
    fixtures = BASE_FIXTURES
    
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetCapabilities"
        return (params, "kvp")

class WMS13GetMapDatasetTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a simple dataset. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)

class WMS13GetMapMultipleDatasetsTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with two datasets. """
    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
              "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
              )
    width = 200
    bbox = (-3.75, 32.19025, 28.29481, 46.268645)
    
class WMS13GetMapDatasetMultispectralTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset containing 15 bands. """
    layers = ("MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",)
    bbox = (8.487755775451660, 32.195316643454134, 25.407486727461219, 46.249103546142578)

class WMS13GetMapMosaicTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a stitched mosaic. """
    layers = ("mosaic_MER_FRS_1P_RGB_reduced",)
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    
#class WMS13GetMapDatasetSeriesTestCase(eoxstest.WMS13GetMapTestCase):
#    """ Test a GetMap request with a dataset series. """
#    layers = ("MER_FRS_1P_reduced",)
#    width = 200
#    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    
# TODO: Add test cases with time parameter (point, interval, etc.)
    
class WMS13GetMapPNGDatasetTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/png"

class WMS13GetMapGIFDatasetTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/gif"

class WMS13GetMapTIFFDatasetTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",)
    bbox = (8.5, 32.2, 25.4, 46.3)
    frmt = "image/tiff"

class WMS13GetMapLayerNotDefinedFaultTestCase(eoxstest.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=INVALIDLAYER&bbox=0,0,1,1&crs=EPSG:4326&width=10&height=10&exceptions=XML"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "LayerNotDefined"

class WMS13GetMapFormatUnknownFaultTestCase(eoxstest.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=-32,-4,46,28&crs=EPSG:4326&width=100&height=100&format=image/INVALID&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidFormat"
    
class WMS13GetMapInvalidBoundingBoxTestCase(eoxstest.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=1,2,3&crs=EPSG:4326&width=100&height=100&format=image/jpeg&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

class WMS13GetMapInvalidCRSTestCase(eoxstest.WMS13ExceptionTestCase):
    def getRequest(self):
        params = "service=WMS&version=1.3.0&request=GetMap&layers=MER_FRS_1P_reduced&bbox=0,0,1,1&crs=INVALIDCRS&width=100&height=100&format=image/jpeg&exceptions=application/vnd.ogc.se_xml"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidCRS"

class WMS13GetMapReferenceableGridTestCase(eoxstest.WMS13GetMapTestCase):
    layers = ("ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775", )
    bbox = (17.0, -36.0, 22.0, -32.0)
    width = 500
    height = 400

class WMS13GetMapReferenceableGridReprojectionTestCase(eoxstest.WMS13GetMapTestCase):
    layers = ("ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775", )
    crs = "epsg:32734"
    bbox = (122043.08622624225, 6008645.867004246, 594457.4634022854, 6459127.468615601)
    width = 472
    height = 451
    swap_axes = False

#===============================================================================
# Test suite
#===============================================================================

def get_tests_by_prefix(prefix, loader=None):
    if loader is None:
        loader = unittest.TestLoader()
    result = []
    for key, value in globals().iteritems():
        if key.startswith(prefix):
            result.extend(loader.loadTestsFromTestCase(value))
            
    return result

def suite():
    wcs_version_tests = unittest.TestSuite(get_tests_by_prefix("WCSVersionNegotiation"))
    
    wcs10_tests = unittest.TestSuite()
    wcs10_tests.addTests(get_tests_by_prefix("WCS10GetCapabilities"))
    wcs10_tests.addTests(get_tests_by_prefix("WCS10DescribeCoverage"))
    wcs10_tests.addTests(get_tests_by_prefix("WCS10GetCoverage"))

    wcs11_tests = unittest.TestSuite()
    wcs11_tests.addTests(get_tests_by_prefix("WCS11GetCapabilities"))
    wcs11_tests.addTests(get_tests_by_prefix("WCS11DescribeCoverage"))
    wcs11_tests.addTests(get_tests_by_prefix("WCS11GetCoverage"))
    
    wcs20_tests = unittest.TestSuite()
    wcs20_tests.addTests(get_tests_by_prefix("WCS20GetCapabilities"))
    wcs20_tests.addTests(get_tests_by_prefix("WCS20DescribeCoverage"))
    wcs20_tests.addTests(get_tests_by_prefix("WCS20DescribeEOCoverageSet"))
    wcs20_tests.addTests(get_tests_by_prefix("WCS20GetCoverage"))
    
    wcs20_post_tests = unittest.TestSuite()
    wcs20_post_tests.addTests(get_tests_by_prefix("WCS20PostGetCapabilities"))
    wcs20_post_tests.addTests(get_tests_by_prefix("WCS20PostDescribeCoverage"))
    wcs20_post_tests.addTests(get_tests_by_prefix("WCS20PostDescribeEOCoverageSet"))
    wcs20_post_tests.addTests(get_tests_by_prefix("WCS20PostGetCoverage"))

    wcs11_post_tests = unittest.TestSuite()
    wcs11_post_tests.addTests(get_tests_by_prefix("WCS11Post"))

    wms13_tests = unittest.TestSuite(get_tests_by_prefix("WMS13"))
    
    all_tests = unittest.TestSuite()
    all_tests.addTests(wcs_version_tests)
    all_tests.addTests(wcs10_tests)
    all_tests.addTests(wcs11_tests)
    all_tests.addTests(wcs20_tests)
    all_tests.addTests(wms13_tests)
    all_tests.addTests(wcs20_post_tests)
    all_tests.addTests(wcs11_post_tests)
    
    return all_tests
