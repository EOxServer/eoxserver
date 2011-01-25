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

import logging

from eoxserver.lib.requests import EOxSOWSRequest
import eoxserver.testing.core as eoxstest

from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
import os, sys

logging.basicConfig(
    filename=os.path.join('logs', 'test.log'),
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)

class EOxSWCS20GetCapabilitiesValidTestCase(eoxstest.EOxSWCS20GetCapabilitiesTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP GetCapabilities response"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=GetCapabilities"
        return EOxSOWSRequest(params=params, param_type="kvp")

########################################################################
#TODO: Commented because of Segfault in libxml2:
#class EOxSWCSVersionNegotiationOldStyleTestCase(eoxstest.EOxSWCS20GetCapabilitiesTestCase):
    #"""This test shall check old style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&version=3.0.0&request=GetCapabilities"
        #return EOxSOWSRequest(params=params, param_type="kvp")

#class EOxSWCSVersionNegotiationNewStyleTestCase(eoxstest.EOxSWCS20GetCapabilitiesTestCase):
    #"""This test shall check new style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&acceptversions=2.0.0,1.1.0&request=GetCapabilities"
        #return EOxSOWSRequest(params=params, param_type="kvp")
########################################################################

#class EOxSWCSVersionNegotiationFaultTestCase(eoxstest.EOxSExceptionTestCase):
    #"""This test shall check new style version negotiation. A valid ows:ExceptionReport shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&acceptversions=3.0.0&request=GetCapabilities"
        #return EOxSOWSRequest(params=params, param_type="kvp")

    #def getExpectedHTTPStatus(self):
        #return 400
    
    #def getExpectedExceptionCode(self):
        #return "VersionNegotiationFailed"
    
class EOxSWCS20DescribeCoverageDatasetTestCase(eoxstest.EOxSWCS20DescribeCoverageTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=collection_080313P600320035L0040S4_rgb"
        return EOxSOWSRequest(params=params, param_type="kvp")

class EOxSWCS20DescribeCoverageMosaicTestCase(eoxstest.EOxSWCS20DescribeCoverageTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedStitchedMosaic."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=image2009_mosaic"
        return EOxSOWSRequest(params=params, param_type="kvp")

class EOxSWCS20DescribeCoverageDatasetSeriesTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a non-coverage. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=image2009_collection"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"
        
class EOxSWCS20DescribeCoverageFaultTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a coverage that does not exist. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=some_coverage"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class EOxSWCS20DescribeCoverageMissingParameterTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall yield a valid ows:ExceptionReport for a missing parameter"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
        
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class EOxSWCS20DescribeEOCoverageSetDatasetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDataset"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=collection_080313P600320035L0040S4_rgb"
        return EOxSOWSRequest(params=params, param_type="kvp")

class EOxSWCS20DescribeEOCoverageSetMosaicTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=image2009_mosaic"
        return EOxSOWSRequest(params=params, param_type="kvp")

class EOxSWCS20DescribeEOCoverageSetDatasetSeriesTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDatasetSeries."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=image2009_collection"
        return EOxSOWSRequest(params=params, param_type="kvp")

class EOxSWCS20DescribeEOCoverageSetFaultTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription set for an wcseo-Object that does not exist. It shall yield a valid ows:ExceptionReport."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=some_eo_object"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class EOxSWCS20DescribeEOCoverageSetMissingParameterTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)"
        return EOxSOWSRequest(params=params, param_type="kvp")

    def getExpectedCoverageIds(self):
        return [
            "collection_080701P600300034L0000S4_rgb",
            "collection_090415P600300034L0000S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)&containment=overlaps"
        return EOxSOWSRequest(params=params, param_type="kvp")

    def getExpectedCoverageIds(self):
        return [
            "collection_080701P600300034L0000S4_rgb",
            "collection_090415P600300034L0000S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)&containment=contains"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedCoverageIds(self):
        return []

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-01-01\",\"2008-03-31\")"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "collection_080313P600320035L0040S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-01-01\",\"2008-03-13T10:00:15Z\")&containment=overlaps"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "collection_080313P600320035L0040S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-01-01\",\"2008-03-13T10:00:15Z\")&containment=contains"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedCoverageIds(self):
        return []

class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=overlaps"
        return EOxSOWSRequest(params=params, param_type="kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081010P600310035L0000S4_rgb",
            "collection_081024P600290035L0020S4_rgb"
        ]


class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=overlaps"
        return EOxSOWSRequest(params=params, param_type="kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081010P600310035L0000S4_rgb",
            "collection_081024P600290035L0020S4_rgb"
        ]


class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=contains"
        return EOxSOWSRequest(params=params, param_type="kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081024P600290035L0020S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetIncorrectTemporalSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(2008-01-01,2008-12-31)"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"
    
class EOxSWCS20DescribeEOCoverageSetInvalidTemporalSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=time(\"2008-01-01\",\"2008-31-31\")"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class EOxSWCS20DescribeEOCoverageSetIncorrectSpatialSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=x,http://www.opengis.net/def/crs/EPSG/0/3035(some_x,some_other_x)"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class EOxSWCS20DescribeEOCoverageSetInvalidSpatialSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=x,http://www.opengis.net/def/crs/EPSG/0/3035(4650000,4630000)"
        return EOxSOWSRequest(params=params, param_type="kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

# Test case result has to be clarified by WCS 2.0 EO Extension

#class EOxSWCS20DescribeEOCoverageSetInvalidAxisLabelTestCase(eoxstest.EOxSExceptionTestCase):
    #def getRequest(self):
        #params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=image2009_collection&subset=x_axis,http://www.opengis.net/def/crs/EPSG/0/3035(4500000,4700000)"
        #return EOxSOWSRequest(params=params, param_type="kvp")
    
    #def getExpectedHTTPStatus(self):
        #return 404
    
    #def getExpectedExceptionCode(self):
        #return "InvalidAxisLabel"

#curl -s -o 25.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1'
#curl -s -o 26.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test'
#curl -s -o 27.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2002_Test_Scene_1'
#curl -s -o 28.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff'
#curl -s -o 29.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff'
#curl -s -o 30.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/bmp'
#curl -s -o 31.dat 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&mediatype=multipart/mixed'
#curl -s -o 32.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff&mediatype=multipart/mixed'
#curl -s -o 33.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&mediatype=multipart/something'
#curl -s -o 34.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x(2100,2300)&SUBSET=y(3870,4070)'
#curl -s -o 35.dat 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&mediatype=multipart/mixed&subset=x(2100,2300)&subset=y(3870,4070)'
#curl -s -o 36.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff&subset=x(2100,2300)&subset=y(3870,4070)'
#curl -s -o 37.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&subset=x(2100,2300)&subset=y(3870,4070)'
#curl -s -o 38.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)'
#curl -s -o 39.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)'
#curl -s -o 40.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&OutputCRS=http://www.opengis.net/def/crs/EPSG/0/4326'
#curl -s -o 41.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/99999(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)'
#curl -s -o 42.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/99999(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/99999(48,48.3)'
#curl -s -o 43.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&size=x(200)&size=y(200)'
#curl -s -o 44.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff&size=x(200)&size=y(400)'
#curl -s -o 45.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x(2100,2700)&SUBSET=y(3870,4470)&size=x(200)&size=y(400)'
#curl -s -o 46.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)&SIZE=x(200)&SIZE=y(200)'
#curl -s -o 47.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)&SIZE=x(17.3)&SIZE=y(20)'
#curl -s -o 48.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&RESOLUTION=x(100)&RESOLUTION=y(100)'
#curl -s -o 49.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Stitched_Mosaic_Test&FORMAT=image/tiff&resolution=x(10)&resolution=y(20)'
#curl -s -o 50.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x(2100,2700)&SUBSET=y(3870,4470)&resolution=x(30)&resolution=y(30)'
#curl -s -o 51.tif 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)&RESOLUTION=x(0.00027)&RESOLUTION=y(0.00027)'
#curl -s -o 52.xml 'http://hma.eox.at/wcs-test?service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&FORMAT=image/tiff&SUBSET=x,http://www.opengis.net/def/crs/EPSG/0/4326(17,17.4)&SUBSET=y,http://www.opengis.net/def/crs/EPSG/0/4326(48,48.3)&RESOLUTION=lat(0.00027)&RESOLUTION=lon(0.00027)'
