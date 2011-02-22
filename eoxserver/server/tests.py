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
        return (params, "kvp")

########################################################################
#TODO: Commented because of Segfault in libxml2:
#class EOxSWCSVersionNegotiationOldStyleTestCase(eoxstest.EOxSWCS20GetCapabilitiesTestCase):
    #"""This test shall check old style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&version=3.0.0&request=GetCapabilities"
        #return (params, "kvp")

#class EOxSWCSVersionNegotiationNewStyleTestCase(eoxstest.EOxSWCS20GetCapabilitiesTestCase):
    #"""This test shall check new style version negotiation. A valid WCS 2.0 EO-AP GetCapabilities response shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&acceptversions=2.0.0,1.1.0&request=GetCapabilities"
        #return (params, "kvp")
########################################################################

#class EOxSWCSVersionNegotiationFaultTestCase(eoxstest.EOxSExceptionTestCase):
    #"""This test shall check new style version negotiation. A valid ows:ExceptionReport shall be returned"""
    #def getRequest(self):
        #params = "service=wcs&acceptversions=3.0.0&request=GetCapabilities"
        #return (params, "kvp")

    #def getExpectedHTTPStatus(self):
        #return 400
    
    #def getExpectedExceptionCode(self):
        #return "VersionNegotiationFailed"
    
class EOxSWCS20DescribeCoverageDatasetTestCase(eoxstest.EOxSWCS20DescribeCoverageTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class EOxSWCS20DescribeCoverageMosaicTestCase(eoxstest.EOxSWCS20DescribeCoverageTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeCoverage response for a wcseo:RectifiedStitchedMosaic."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class EOxSWCS20DescribeCoverageDatasetSeriesTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a non-coverage. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1P_reduced"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"
        
class EOxSWCS20DescribeCoverageFaultTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a coverage that does not exist. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=some_coverage"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class EOxSWCS20DescribeCoverageMissingParameterTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall yield a valid ows:ExceptionReport for a missing parameter"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
        
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class EOxSWCS20DescribeEOCoverageSetDatasetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDataset"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class EOxSWCS20DescribeEOCoverageSetMosaicTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class EOxSWCS20DescribeEOCoverageSetDatasetSeriesTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP DescribeEOCoverageSet response for a wcseo:RectifiedDatasetSeries."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced"
        return (params, "kvp")

class EOxSWCS20DescribeEOCoverageSetFaultTestCase(eoxstest.EOxSExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription set for an wcseo-Object that does not exist. It shall yield a valid ows:ExceptionReport."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=some_eo_object"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class EOxSWCS20DescribeEOCoverageSetMissingParameterTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "collection_080701P600300034L0000S4_rgb",
            "collection_090415P600300034L0000S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)&containment=overlaps"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "collection_080701P600300034L0000S4_rgb",
            "collection_090415P600300034L0000S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTwoSpatialSubsetsContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48.7)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(14,14.1)&containment=contains"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return []

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-01-01\",\"2008-03-31\")"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "collection_080313P600320035L0040S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-01-01\",\"2008-03-13T10:00:15Z\")&containment=overlaps"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return [
            "collection_080313P600320035L0040S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetTemporalSubsetContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-01-01\",\"2008-03-13T10:00:15Z\")&containment=contains"
        return (params, "kvp")
    
    def getExpectedCoverageIds(self):
        return []

class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=overlaps"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081010P600310035L0000S4_rgb",
            "collection_081024P600290035L0020S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetOverlapsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=overlaps"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081010P600310035L0000S4_rgb",
            "collection_081024P600290035L0020S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetSpatioTemporalSubsetContainsTestCase(eoxstest.EOxSWCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-10-01\",\"2008-11-01\")&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(47,48)&subset=long,http://www.opengis.net/def/crs/EPSG/0/4326(12,14.8)&containment=contains"
        return (params, "kvp")
        
    def getExpectedCoverageIds(self):
        return [
            "collection_081024P600290035L0020S4_rgb"
        ]

class EOxSWCS20DescribeEOCoverageSetIncorrectTemporalSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(2008-01-01,2008-12-31)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"
    
class EOxSWCS20DescribeEOCoverageSetInvalidTemporalSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=time(\"2008-01-01\",\"2008-31-31\")"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class EOxSWCS20DescribeEOCoverageSetIncorrectSpatialSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=x,http://www.opengis.net/def/crs/EPSG/0/3035(some_x,some_other_x)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class EOxSWCS20DescribeEOCoverageSetInvalidSpatialSubsetTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=x,http://www.opengis.net/def/crs/EPSG/0/3035(4650000,4630000)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 404
    
    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

# Test case result has to be clarified by WCS 2.0 EO Extension

#class EOxSWCS20DescribeEOCoverageSetInvalidAxisLabelTestCase(eoxstest.EOxSExceptionTestCase):
    #def getRequest(self):
        #params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=x_axis,http://www.opengis.net/def/crs/EPSG/0/3035(4500000,4700000)"
        #return (params, "kvp")
    
    #def getExpectedHTTPStatus(self):
        #return 404
    
    #def getExpectedExceptionCode(self):
        #return "InvalidAxisLabel"


#TODO this is a XML test, isnt it?

class EOxSWCS20GetCoverageFormatMissingTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

#class EOxSWCS20GetCoverageSimpleTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=Image2009_Test_Scene_1&format=image/tiff"
#        return (params, "kvp")

# SIMPLE requests

class EOxSWCS20GetCoverageMosaicTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff"
        return (params, "kvp")

class EOxSWCS20GetCoverageCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"
        return (params, "kvp")

# FORMAT

# TODO: currently unrecognised format 'bmp'. either choose another, or add it to outputformats
#class EOxSWCS20GetCoverageBMPTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/bmp"
#        return (params, "kvp")
#    
#    def getFileExtension(self):
#        return "bmp"

    
# MEDIATYPE

class EOxSWCS20GetCoverageMultipartMosaicTestCase(eoxstest.EOxSWCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&mediatype=multipart/mixed"
        return (params, "kvp")

class EOxSWCS20GetCoverageMultipartCollectionTestCase(eoxstest.EOxSWCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed"
        return (params, "kvp")

# TODO: wrong multipart parameters only result in non-multipart images. Uncomment, when implemented
#class EOxSWCS20GetCoverageWrongMultipartParameterTestCase(eoxstest.EOxSExceptionTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=image2009_mosaic&format=image/tiff&mediatype=multipart/something"
#        return (params, "kvp")
#
#    def getExpectedHTTPStatus(self):
#        return 404
#    
#    def getExpectedExceptionCode(self):
#        return "InvalidParameterValue"

# SUBSET

class EOxSWCS20GetCoverageSubsetCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,500)&subset=y(200,500)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetMosaicTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x(100,500)&subset=y(200,500)"
        return (params, "kvp")

class EOxSWCS20GetCoverageMultipartSubsetCollectionTestCase(eoxstest.EOxSWCS20GetCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/mixed&subset=x(100,500)&subset=y(200,500)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetEPSG4326CollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(16,17.4)&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(43,44.3)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetEPSG4326MosaicTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(16,17.4)&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(43,44.3)"
        return (params, "kvp")
    
class EOxSWCS20GetCoverageOutputCRSCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&outputcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetInvalidEPSGTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/99999(16,17.4)&subset=y,http://www.opengis.net/def/crs/EPSG/0/99999(43,44.3)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

# SIZE

class EOxSWCS20GetCoverageSizeCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&size=x(200)&size=y(200)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSizeMosaicTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(200)&size=y(400)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetSizeCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,500)&subset=y(200,500)&size=x(200)&size=y(200)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetEPSG4326SizeCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(16,17.4)&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(43,44.3)&size=x(200)&size=y(200)"
        return (params, "kvp")

class EOxSWCS20GetCoverageInvalidSizeTestCase(eoxstest.EOxSExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&size=x(1.11)"
        return (params, "kvp")
    
    def getExpectedHTTPStatus(self):
        return 400
    
    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

# RESOLUTION

class EOxSWCS20GetCoverageResolutionCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")
    
class EOxSWCS20GetCoverageResolutionMosaicTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_RGB_reduced&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetResolutionCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,500)&subset=y(200,500)&resolution=x(0.1)&resolution=y(0.1)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetEPSG4326ResolutionCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326(16,17.4)&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326(43,44.3)&resolution=x(0.01)&resolution=y(0.01)"
        return (params, "kvp")

class EOxSWCS20GetCoverageSubsetEPSG4326ResolutionLatLonCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lon,http://www.opengis.net/def/crs/EPSG/0/4326(16,17.4)&subset=lat,http://www.opengis.net/def/crs/EPSG/0/4326(43,44.3)&resolution=lat(0.01)&resolution=lon(0.01)"
        return (params, "kvp")

# RANGESUBSET

class EOxSWCS20GetCoverageRangeSubsetIndicesCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=1,2,3"
        return (params, "kvp")

class EOxSWCS20GetCoverageRangeSubsetNamesCollectionTestCase(eoxstest.EOxSWCS20GetCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")
