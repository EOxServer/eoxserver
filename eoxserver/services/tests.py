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

import logging

from eoxserver.services.requests import OWSRequest
import eoxserver.testing.core as eoxstest

from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
import os, sys

class WCS20GetCapabilitiesValidTestCase(eoxstest.WCS20GetCapabilitiesTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP GetCapabilities response"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationOldStyleTestCase(eoxstest.WCS20GetCapabilitiesTestCase):
    """This test shall check old style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&version=3.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationNewStyleTestCase(eoxstest.WCS20GetCapabilitiesTestCase):
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
    
class WCS20DescribeCoverageDatasetTestCase(eoxstest.WCS20DescribeCoverageTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeCoverageMosaicTestCase(eoxstest.WCS20DescribeCoverageTestCase):
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

class WCS20DescribeEOCoverageSetDatasetTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDataset"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetMosaicTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetDatasetSeriesTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase):
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
    
    
# Paging testcases

class WCS20DescribeEOCoverageSetDatasetPagingCountTestCase(eoxstest.WCS20DescribeEOCoverageSetPagingTestCase):
    def getExpectedCoverageCount(self):
        return 2
    
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&count=2"
        return (params, "kvp")

# Section test cases

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


class WCS20DescribeEOCoverageSetDatasetUniqueTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase): 
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed,MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetDatasetOutOfSubsetTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed&ubset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(0,1)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(0,1)"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return []
    
class WCS20DescribeEOCoverageSetDatasetSeriesStitchedMosaicTestCase(eoxstest.WCS20DescribeEOCoverageSetTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced,mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
            "mosaic_MER_FRS_1P_RGB_reduced"
        ]

#class WCS20DescribeEOCoverageSetDatasetPagingConfigTestCase(eoxstest.WCS20DescribeEOCoverageSetPagingTestCase):
#    def getConfigCountOverride(self):
#        return 2
#    
#    def getExpectedCoverageCount(self):
#        return 2
#    
#    def getRequest(self):
#        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced"
#        return (params, "kvp")

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

# Simple requests

class WCS20GetCoverageMosaicTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff"
        return (params, "kvp")

class WCS20GetCoverageDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"
        return (params, "kvp")

# FORMAT

class WCS20GetCoverageJPEGTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/jpeg"
        return (params, "kvp")
    
    def getFileExtension(self):
        return "jpg"

# MEDIATYPE

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
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=image2009_mosaic&format=image/tiff&mediatype=multipart/something"
#        return (params, "kvp")
#
#    def getExpectedExceptionCode(self):
#        return "InvalidParameterValue"

# SUBSET

class WCS20GetCoverageSubsetDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageSubsetMosaicTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageMultipartSubsetDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326DatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326MosaicTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(0,30)"
        return (params, "kvp")

class WCS20GetCoverageSubsetInvalidEPSGFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/99999(38,40)&subset=y,http://www.opengis.net/def/crs/EPSG/0/99999(20,22)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

# OUTPUTCRS

class WCS20GetCoverageOutputCRSDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035"
        return (params, "kvp")

# SIZE

class WCS20GetCoverageSizeDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&size=x(200)&size=y(200)"
        return (params, "kvp")

class WCS20GetCoverageSizeMosaicTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(200)&size=y(400)"
        return (params, "kvp")

class WCS20GetCoverageSubsetSizeDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=x(20)&size=y(20)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326SizeDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&size=lat(20)&size=long(20)"
        return (params, "kvp")

class WCS20GetCoverageInvalidSizeFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(1.11)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

# RESOLUTION

class WCS20GetCoverageResolutionDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")
    
class WCS20GetCoverageResolutionMosaicTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageSubsetResolutionDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326ResolutionLatLonDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&resolution=lat(0.01)&resolution=long(0.01)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326ResolutionInvalidAxisDatasetFaultTestCase(eoxstest.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(38,40)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(20,22)&resolution=x(0.01)&resolution=y(0.01)"
        return (params, "kvp")
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

# RANGESUBSET

class WCS20GetCoverageRangeSubsetIndicesDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=1,2,3"
        return (params, "kvp")

class WCS20GetCoverageRangeSubsetNamesDatasetTestCase(eoxstest.WCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

class WCS20GetCoverageMultipartRangeSubsetNamesDatasetTestCase(eoxstest.WCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

# WMS

class WMS13GetCapabilitiesValidTestCase(eoxstest.WMS13GetCapabilitiesTestCase):
    """This test shall retrieve a valid WMS 1.3 GetCapabilities response"""
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
    
class WMS13GetMapDatasetSeriesTestCase(eoxstest.WMS13GetMapTestCase):
    """ Test a GetMap request with a dataset series. """
    layers = ("MER_FRS_1P_reduced",)
    width = 200
    bbox = (-3.75, 32.158895, 28.326165, 46.3)
    