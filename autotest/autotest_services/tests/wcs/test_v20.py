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

from urllib import quote

from autotest_services import base as testbase
import base as wcsbase


#===============================================================================
# WCS 2.0 Get Capabilities
#===============================================================================

class WCS20GetCapabilitiesValidTestCase(testbase.XMLTestCase, testbase.SchematronTestMixIn):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities response"""

    schematron_locations = ["http://schemas.opengis.net/wcs/crs/",
                            "http://schemas.opengis.net/wcs/crs/1.0/wcsCrs.sch"]

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities"
        return (params, "kvp")

class WCS20GetCapabilitiesEmptyTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 2.0 EO-AP (EO-WCS) GetCapabilities response (see #41)"""
    fixtures = testbase.BASE_FIXTURES

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationTestCase(testbase.XMLTestCase):
    """This test shall check version negotiation. A valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationOldStyleTestCase(testbase.XMLTestCase):
    """This test shall check old style version negotiation. A valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&version=3.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationNewStyleTestCase(testbase.XMLTestCase):
    """This test shall check new style version negotiation. A valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities response shall be returned"""
    def getRequest(self):
        params = "service=wcs&acceptversions=2.0.1,1.1.0&request=GetCapabilities"
        return (params, "kvp")

class WCSVersionNegotiationFaultTestCase(testbase.ExceptionTestCase):
    """This test shall check new style version negotiation. A valid ows:ExceptionReport shall be returned"""
    def getRequest(self):
        params = "service=wcs&acceptversions=3.0.0&request=GetCapabilities"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "VersionNegotiationFailed"

class WCS20GetCapabilitiesSectionsAllTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=All"
        return (params, "kvp")

class WCS20GetCapabilitiesSectionsAll2TestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=ServiceIdentification,ServiceProvider,OperationsMetadata,ServiceMetadata,Contents"
        return (params, "kvp")

class WCS20GetCapabilitiesSectionsAll3TestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=ServiceIdentification,ServiceProvider,OperationsMetadata,ServiceMetadata,CoverageSummary,DatasetSeriesSummary"
        return (params, "kvp")

class WCS20GetCapabilitiesSectionsServiceIdentificationTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=ServiceIdentification"
        return (params, "kvp")

class WCS20GetCapabilitiesSectionsContentsTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=Contents"
        return (params, "kvp")


class WCS20GetCapabilitiesSectionsCoverageSummaryTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=CoverageSummary"
        return (params, "kvp")

class WCS20GetCapabilitiesSectionsDatasetSeriesSummaryTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities
    response including all sections"""

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities&sections=DatasetSeriesSummary"
        return (params, "kvp")

#===============================================================================
# WCS 2.0 DescribeCoverage
#===============================================================================

class WCS20DescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeCoverage response for a wcseo:RectifiedDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeCoverageMosaicTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeCoverage response for a wcseo:RectifiedStitchedMosaic."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

class WCS20DescribeCoverageDatasetSeriesFaultTestCase(testbase.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a non-coverage. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1P_reduced"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS20DescribeCoverageFaultTestCase(testbase.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription for a coverage that does not exist. It shall yield a valid ows:ExceptionReport"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=some_coverage"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS20DescribeCoverageMissingParameterFaultTestCase(testbase.ExceptionTestCase):
    """This test shall yield a valid ows:ExceptionReport for a missing parameter"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

#===============================================================================
# WCS 2.0 DescribeEOCoverageSet
#===============================================================================

class WCS20DescribeEOCoverageSetDatasetTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeEOCoverageSet response for a wcseo:RectifiedDataset"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetMosaicTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic"""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetDatasetSeriesTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeEOCoverageSet response for a wcseo:RectifiedDatasetSeries."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetFaultTestCase(testbase.ExceptionTestCase):
    """This test shall try to retrieve a CoverageDescription set for an wcseo-Object that does not exist. It shall yield a valid ows:ExceptionReport."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=some_eo_object"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "NoSuchDatasetSeriesOrCoverage"

class WCS20DescribeEOCoverageSetMissingParameterFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "MissingParameterValue"

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat(32,47)&subset=long(11,33)"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsOverlapsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat(32,47)&subset=long(11,33)&containment=overlaps"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTwoSpatialSubsetsContainsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat(32,47)&subset=long(11,33)&containment=contains"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetOverlapsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&containment=overlaps'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetOverlapsIntervalBorderTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-16T09:09:29Z\")&containment=overlaps"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetContainsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&containment=contains'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetTemporalSubsetContainsIntervalBorderTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(\"2006-08-01\",\"2006-08-16T09:12:46Z\")&containment=contains"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&subset=lat(32,47)&subset=long(11,33)'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetOverlapsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&subset=lat(32,47)&subset=long(11,33)&containment=overlaps'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetSpatioTemporalSubsetContainsTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-08-22T09:22:00Z")&subset=lat(32,47)&subset=long(11,33)&containment=contains'
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetIncorrectTemporalSubsetFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime(2006-08-01,2006-08-22)"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class WCS20DescribeEOCoverageSetInvalidTemporalSubsetFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = 'service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=phenomenonTime("2006-08-01","2006-31-31")'
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class WCS20DescribeEOCoverageSetIncorrectSpatialSubsetFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat(some_lat,some_other_lat)"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

class WCS20DescribeEOCoverageSetInvalidSpatialSubsetFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=lat(47,32)"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidSubsetting"

# EOxServer allows and understands certain additional axis labels like "lat", or "long".
class WCS20DescribeEOCoverageSetInvalidAxisLabelFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&subset=x_axis(32,47)"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidAxisLabel"

#===============================================================================
# WCS 2.0: Paging testcases
#===============================================================================

class WCS20DescribeEOCoverageSetDatasetPagingCountTestCase(testbase.WCS20DescribeEOCoverageSetPagingTestCase):
    def getExpectedCoverageCount(self):
        return 1

    def getExpectedDatasetSeriesCount(self):
        return 1

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&count=2"
        return (params, "kvp")

#===============================================================================
# WCS 2.0: Section test cases
#===============================================================================

class WCS20DescribeEOCoverageSetSectionsAllTestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/2.0}CoverageDescriptions",
            "{http://www.opengis.net/wcs/wcseo/1.0}DatasetSeriesDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=All"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsAll2TestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/2.0}CoverageDescriptions",
            "{http://www.opengis.net/wcs/wcseo/1.0}DatasetSeriesDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions,DatasetSeriesDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsAll3TestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/2.0}CoverageDescriptions",
            "{http://www.opengis.net/wcs/wcseo/1.0}DatasetSeriesDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=All,DatasetSeriesDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsAll4TestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/2.0}CoverageDescriptions",
            "{http://www.opengis.net/wcs/wcseo/1.0}DatasetSeriesDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions,All"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsCoverageDescriptionsTestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/2.0}CoverageDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=CoverageDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsDatasetSeriesDescriptionsTestCase(testbase.WCS20DescribeEOCoverageSetSectionsTestCase):
    def getExpectedSections(self):
        return [
            "{http://www.opengis.net/wcs/wcseo/1.0}DatasetSeriesDescriptions"
        ]

    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeEOCoverageSet&eoId=MER_FRS_1P_reduced&sections=DatasetSeriesDescriptions"
        return (params, "kvp")

class WCS20DescribeEOCoverageSetSectionsFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced&sections=WrongSection"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 400

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"


class WCS20DescribeEOCoverageSetDatasetUniqueTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed,MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed"
        ]

class WCS20DescribeEOCoverageSetDatasetOutOfSubsetTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced,mosaic_MER_FRS_1P_reduced_RGB,MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed&subset=lat(0,1)&subset=long(0,1)"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return []

class WCS20DescribeEOCoverageSetDatasetSeriesStitchedMosaicTestCase(testbase.WCS20DescribeEOCoverageSetSubsettingTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=DescribeEOCoverageSet&EOID=MER_FRS_1P_reduced,mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

    def getExpectedCoverageIds(self):
        return [
            "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed",
            "MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_uint16_reduced_compressed",
            "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
            "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
            "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
            "mosaic_MER_FRS_1P_reduced_RGB"
        ]

#===============================================================================
# WCS 2.0: Exceptions
#===============================================================================

# after WCS 2.0.1 implementation does not lead to an error anymore
#class WCS20GetCoverageFormatMissingFaultTestCase(testbase.ExceptionTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB"
#        return (params, "kvp")
#
#    def getExpectedExceptionCode(self):
#        return "MissingParameterValue"

class WCS20GetCoverageNoSuchCoverageFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=INVALID"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "NoSuchCoverage"

class WCS20GetCoverageFormatUnsupportedFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/jpeg"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

class WCS20GetCoverageFormatUnknownFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=unknown"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Simple requests
#===============================================================================

class WCS20GetCoverageMosaicTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff"
        return (params, "kvp")

class WCS20GetCoverageDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff"
        return (params, "kvp")

#==============================================================================
# WCS 2.0: Formats
#==============================================================================

# WCS 2.0.1 introduced the native format, i.e., default format in case of missing format specification
class WCS20GetCoverageNativeTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "tif"

class WCS20GetCoverageJPEG2000TestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/jp2"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "jp2"

class WCS20GetCoverageNetCDFTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=application/x-netcdf"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "nc"

class WCS20GetCoverageHDFTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=application/x-hdf"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "hdf"

# TODO: Enable test once subdatasets are supported (see #123):
#class WCS20GetCoverageNetCDFInputTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_netCDF&format=image/tiff"
#        return (params, "kvp")

class WCS20GetCoverageJPEG2000InputTestCase(testbase.RectifiedGridCoverageTestCase):
    fixtures = testbase.RectifiedGridCoverageTestCase.fixtures + ["meris_coverages_jpeg2000.json"]
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced_JPEG2000&format=image/tiff"
        return (params, "kvp")

#===============================================================================
# WCS 2.0: Multipart requests
#===============================================================================

class WCS20GetCoverageMultipartMosaicTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&mediatype=multipart/related"
        return (params, "kvp")

class WCS20GetCoverageMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related"
        return (params, "kvp")

# TODO: wrong multipart parameters only result in non-multipart images. Uncomment, when implemented
#class WCS20GetCoverageWrongMultipartParameterFaultTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.ExceptionTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&mediatype=multipart/something"
#        return (params, "kvp")
#
#    def getExpectedExceptionCode(self):
#        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Subset requests
#===============================================================================

class WCS20GetCoverageSubsetDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageMultipartSubsetMosaicTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&mediatype=multipart/related&subset=x(100,1000)&subset=y(0,99)"
        return (params, "kvp")

class WCS20GetCoverageMultipartSubsetDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326DatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat(38,40)&subset=long(20,22)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326MosaicTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&subset=lat(38,40)&subset=long(0,30)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageSubsetInvalidEPSGFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&subset=x(38,40)&subset=y(20,22)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/99999"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "SubsettingCrs-NotSupported"

    def getExpectedHTTPStatus(self):
        return 404

#===============================================================================
# WCS 2.0: OutputCRS
#===============================================================================

class WCS20GetCoverageOutputCRSDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035"
        return (params, "kvp")

class WCS20GetCoverageOutputCRSotherUoMDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3857"
        return (params, "kvp")

class WCS20GetCoverageOutputCrsEPSGFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&outputcrs=http://www.opengis.net/def/crs/EPSG/0/99999"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "OutputCrs-NotSupported"

    def getExpectedHTTPStatus(self):
        return 404

#===============================================================================
# WCS 2.0: Size
#===============================================================================

class WCS20GetCoverageSizeDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&scalesize=x(200),y(200)"
        return (params, "kvp")

class WCS20GetCoverageSizeMosaicTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&scalesize=x(200),y(400)"
        return (params, "kvp")

class WCS20GetCoverageSubsetSizeDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&scalesize=x(20),y(20)"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326SizeDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&subset=lat(38,40)&subset=long(20,22)&scalesize=lat(20),long(20)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageSubsetEPSG4326SizeExceedsExtentDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat(10,50)&subset=long(0,50)&scalesize=lat(100),long(100)&mediatype=multipart/related&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageInvalidSizeFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&scalesize=x(1.11)"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 404

    def getExpectedExceptionCode(self):
        return "InvalidScaleFactor"

#===============================================================================
# WCS 2.0: Resolution
#===============================================================================

# TODO: not supported anymore (WCS 2.0 Scaling Extension)

#class WCS20GetCoverageResolutionDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
#        return (params, "kvp")
#
#class WCS20GetCoverageResolutionMosaicTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1P_reduced_RGB&format=image/tiff&resolution=x(0.1)&resolution=y(0.1)"
#        return (params, "kvp")
#
#class WCS20GetCoverageSubsetResolutionDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&resolution=x(0.1)&resolution=y(0.1)"
#        return (params, "kvp")
#
#class WCS20GetCoverageSubsetEPSG4326ResolutionLatLonDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat(38,40)&subset=long(20,22)&resolution=lat(0.01)&resolution=long(0.01)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
#        return (params, "kvp")
#
#class WCS20GetCoverageSubsetEPSG4326ResolutionInvalidAxisDatasetFaultTestCase(testbase.ExceptionTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=lat(38,40)&subset=long(20,22)&resolution=x(0.01)&resolution=y(0.01)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
#        return (params, "kvp")
#
#    def getExpectedExceptionCode(self):
#        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0: Rangesubset
#===============================================================================

class WCS20GetCoverageRangeSubsetIntervalDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=MERIS_radiance_01_uint16:MERIS_radiance_03_uint16"
        return (params, "kvp")

class WCS20GetCoverageRangeSubsetNamesDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

class WCS20GetCoverageRangeSubsetNamesPNGDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/png&rangesubset=MERIS_radiance_01_uint16"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "png"

class WCS20GetCoverageRangeSubsetItemIntervalDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/png&rangesubset=MERIS_radiance_01_uint16,MERIS_radiance_03_uint16:MERIS_radiance_04_uint16"
        return (params, "kvp")

    def getFileExtension(self, part=None):
        return "png"

class WCS20GetCoverageMultipartRangeSubsetNamesDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mediatype=multipart/related&rangesubset=MERIS_radiance_04_uint16,MERIS_radiance_05_uint16,MERIS_radiance_06_uint16"
        return (params, "kvp")

# TODO: not supported anymore (WCS 2.0 Scaling Extension)

#class WCS20GetCoverageSubsetSizeResolutionOutputCRSRangeSubsetIntervalDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=y(100)&resolution=x(0.1)&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&rangesubset=MERIS_radiance_01_uint16:MERIS_radiance_03_uint16&mediatype=multipart/related"
#        return (params, "kvp")

#===============================================================================
# WCS 2.0: Polygon Mask
#===============================================================================

# TODO: Enable these tests once the feature is implemented in MapServer

#class WCS20GetCoveragePolygonMaskTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mask=polygon(14.124422306243844,42.806626286621963,21.208516509273601,43.730638573973678,21.208516509273601,43.730638573973678,21.892970055460054,37.8443380767702,15.04843459359555,36.646544370943914,12.379065763468395,39.555471942236323,14.124422306243844,42.806626286621963)"
#        return (params, "kvp")


#class WCS20GetCoveragePolygonMaskProjectedTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self): # TODO: swap axes
#        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&mask=polygon,http://www.opengis.net/def/crs/EPSG/0/4326(42.806626286621963,14.124422306243844,43.730638573973678,21.208516509273601,43.730638573973678,21.208516509273601,37.8443380767702,21.892970055460054,36.646544370943914,15.04843459359555,39.555471942236323,12.379065763468395,42.806626286621963,14.124422306243844)"
#        return (params, "kvp")

#class WCS20PostGetCoveragePolygonMaskTestCase(testbase.RectifiedGridCoverageTestCase):
#    def getRequest(self):
#        params = """<wcs:GetCoverage service="WCS" version="2.0.0"
#           xmlns:wcs="http://www.opengis.net/wcs/2.0"
#           xmlns:wcsmask="http://www.opengis.net/wcs/mask/1.0">
#          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
#          <wcs:format>image/tiff</wcs:format>
#          <wcs:Extension>
#            <wcsmask:polygonMask>14.124422306243844 42.806626286621963 21.208516509273601 43.730638573973678 21.208516509273601 43.730638573973678 21.892970055460054 37.8443380767702 15.04843459359555 36.646544370943914 12.379065763468395 39.555471942236323 14.124422306243844 42.806626286621963</wcsmask:polygonMask>
#          </wcs:Extension>
#        </wcs:GetCoverage>"""
#        return (params, "xml")

#===============================================================================
# WCS 2.0: Interpolation
#===============================================================================

class WCS20GetCoverageDatasetInterpolationNearestTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced&format=image/tiff&subset=x(200,250)&subset=y(200,250)outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&interpolation=http://www.opengis.net/def/interpolation/OGC/1/nearest-neighbour"
        return (params, "kvp")

class WCS20GetCoverageDatasetInterpolationAverageTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced&format=image/tiff&subset=x(200,250)&subset=y(200,250)outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&interpolation=http://www.opengis.net/def/interpolation/OGC/1/average"
        return (params, "kvp")

class WCS20GetCoverageDatasetInterpolationBilinearTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced&format=image/tiff&subset=x(200,250)&subset=y(200,250)outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&interpolation=http://www.opengis.net/def/interpolation/OGC/1/bilinear"
        return (params, "kvp")

class WCS20GetCoverageInvalidInterpolationFaultTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced&format=image/tiff&subset=x(200,250)&subset=y(200,250)outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&interpolation=http://www.opengis.net/def/interpolation/OGC/1/invalid"
        return (params, "kvp")

    def getExpectedExceptionCode(self):
        return "InterpolationMethodNotSupported"

    def getExpectedHTTPStatus(self):
        return 404

#===============================================================================
# WCS 2.0 Rasdaman test cases
#===============================================================================

class WCS20GetCoverageRasdamanMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSubsetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSizeTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&scalesize=x(100),y(100)"
        return (params, "kvp")

# TODO: not supported anymore (WCS 2.0 Scaling Extension)
#class WCS20GetCoverageRasdamanMultipartDatasetResolutionTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&resolution=x(0.1)&resolution=y(0.1)"
#        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetOutputCRSTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035"
        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetSubsetSizeTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&subset=x(100,200)&subset=y(200,300)&scalesize=x(20),y(20)"
        return (params, "kvp")

# TODO: not supported anymore (WCS 2.0 Scaling Extension)
#class WCS20GetCoverageRasdamanMultipartDatasetSubsetResolutionTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
#    def getRequest(self):
#        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&subset=x(100,200)&subset=y(200,300)&resolution=x(0.1)&resolution=y(0.1)"
#        return (params, "kvp")

class WCS20GetCoverageRasdamanMultipartDatasetRangeSubsetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&mediatype=multipart/related&rangesubset=1"
        return (params, "kvp")

class WCS20GetCoverageRasdamanSubsetSizeResolutionOutputCRSRangeSubsetIndicesDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.RasdamanTestCaseMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced_rasdaman&format=image/tiff&subset=x(100,200)&subset=y(200,300)&size=y(100)&resolution=x(0.1)&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3035&rangesubset=1,2,3&mediatype=multipart/related"
        return (params, "kvp")


#===============================================================================
# WCS 2.0: GetCov with EPSG:3035 input images
#===============================================================================

class WCS20DescribeCoverageReprojectedDatasetTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected"
        return (params, "kvp")

class WCS20GetCoverageReprojectedDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected&format=image/tiff"
        return (params, "kvp")

class WCS20GetCoverageReprojectedSubsetDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected&format=image/tiff&subset=x(100,200)&subset=y(200,300)"
        return (params, "kvp")

class WCS20GetCoverageReprojectedSubsetEPSG4326DatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected&format=image/tiff&mediatype=multipart/related&subset=lat(38,40)&subset=long(20,22)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageReprojectedMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected&format=image/tiff&mediatype=multipart/related"
        return (params, "kvp")

class WCS20GetCoverageReprojectedEPSG3857DatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed_reprojected&format=image/tiff&mediatype=multipart/related&outputcrs=http://www.opengis.net/def/crs/EPSG/0/3857"
        return (params, "kvp")

#===============================================================================
# WCS 2.0 Referenceable Grid Coverages
#===============================================================================

class WCS20DescribeCoverageReferenceableDatasetTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeCoverage response for a wcseo:ReferenceableDataset."""
    def getRequest(self):
        params = "service=WCS&version=2.0.0&request=DescribeCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775"
        return (params, "kvp")

class WCS20GetCoverageReferenceableDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageReferenceableGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&mediatype=multipart/related"
        return (params, "kvp")

class WCS20GetCoverageReferenceableDatasetImageCRSSubsetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageReferenceableGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&mediatype=multipart/related&subset=x(0,99)&subset=y(0,99)"
        return (params, "kvp")

class WCS20GetCoverageReferenceableDatasetGeogCRSSubsetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageReferenceableGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&mediatype=multipart/mixed&subset=x(18.0,20.0)&subset=y(-34.5,-33.5)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageReferenceableDatasetGeogCRSSubsetExceedsExtentTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageReferenceableGridCoverageMultipartTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&mediatype=multipart/mixed&subset=x(18,23)&subset=y(-35,-33)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

class WCS20GetCoverageReferenceableDatasetGeogCRSSubsetOutsideExtentTestCase(testbase.ExceptionTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775&format=image/tiff&mediatype=multipart/mixed&subset=x(14.5,16.5)&subset=y(-34.5,-33.5)&subsettingcrs=http://www.opengis.net/def/crs/EPSG/0/4326"
        return (params, "kvp")

    def getExpectedHTTPStatus(self):
        return 400

    def getExpectedExceptionCode(self):
        return "InvalidParameterValue"

#===============================================================================
# WCS 2.0.1 Corrigendum test cases
#===============================================================================


class WCS20CorrigendumGetCapabilitiesEmptyTestCase(testbase.XMLTestCase):
    """ This test shall retrieve a valid but empty WCS 2.0.1 EO-AP (EO-WCS)
        GetCapabilities response (see #162)
    """
    fixtures = testbase.BASE_FIXTURES

    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=GetCapabilities"
        return (params, "kvp")


class WCS20CorrigendumDescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    """ This test shall retrieve a valid WCS 2.0.1 EO-AP (EO-WCS)
        DescribeCoverage response for a wcseo:RectifiedDataset (see #162).
    """
    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=DescribeCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")


class WCS20CorrigendumDescribeEOCoverageSetMosaicTestCase(testbase.XMLTestCase):
    """ This test shall retrieve a valid WCS 2.0.1 EO-AP (EO-WCS)
        DescribeEOCoverageSet response for a wcseo:RectifiedStitchedMosaic
        (see #162)
    """
    def getRequest(self):
        params = "service=WCS&version=2.0.1&request=DescribeEOCoverageSet&eoId=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")


class WCS20CorrigendumGetCoverageDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=wcs&version=2.0.1&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed"
        return (params, "kvp")


#===============================================================================
# WCS 2.0 - POST
#===============================================================================

class WCS20PostGetCapabilitiesValidTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) GetCapabilities response
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

class WCS20PostDescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeCoverage response
       for a wcseo:RectifiedDataset via POST.
    """
    def getRequest(self):
        params = """<ns:DescribeCoverage
           xmlns:ns="http://www.opengis.net/wcs/2.0" service="WCS" version="2.0.0">
         <ns:CoverageId>MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed</ns:CoverageId>
        </ns:DescribeCoverage>"""
        return (params, "xml")

class WCS20PostDescribeEOCoverageSetDatasetSeriesTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid WCS 2.0 EO-AP (EO-WCS) DescribeEOCoverageSet response
    for a wcseo:RectifiedDatasetSeries via POST.
    """
    def getRequest(self):
        params = """<wcseo:DescribeEOCoverageSet service="WCS" version="2.0.0" count="100"
           xmlns:wcseo="http://www.opengis.net/wcs/wcseo/1.0"
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

class WCS20PostGetCoverageMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0">
          <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")

class WCS20PostGetCoverageSubsetMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0">
          <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>x</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>99</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>y</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>99</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")

class WCS20PostGetCoverageSubsetEPSG4326MultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:crs="http://www.opengis.net/wcs/crs/1.0">
          <wcs:Extension>
            <crs:subsettingCrs>http://www.opengis.net/def/crs/EPSG/0/4326</crs:subsettingCrs>
          </wcs:Extension>
          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>Long</wcs:Dimension>
            <wcs:TrimLow>20</wcs:TrimLow>
            <wcs:TrimHigh>22</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>Lat</wcs:Dimension>
            <wcs:TrimLow>38</wcs:TrimLow>
            <wcs:TrimHigh>40</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")

class WCS20PostGetCoverageReferenceableMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageReferenceableGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0">
          <wcs:CoverageId>ASA_WSM_1PNDPA20050331_075939_000000552036_00035_16121_0775</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>x</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>100</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>y</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>100</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")


class WCS20PostGetCoverageRangeSubsetMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:rsub="http://www.opengis.net/wcs/range-subsetting/1.0">
          <wcs:Extension>
            <rsub:RangeSubset>
              <rsub:RangeItem>
                <rsub:RangeComponent>MERIS_radiance_04_uint16</rsub:RangeComponent>
              </rsub:RangeItem>
              <rsub:RangeItem>
                <rsub:RangeInterval>
                  <rsub:startComponent>MERIS_radiance_05_uint16</rsub:startComponent>
                  <rsub:endComponent>MERIS_radiance_07_uint16</rsub:endComponent>
                </rsub:RangeInterval>
              </rsub:RangeItem>
            </rsub:RangeSubset>
          </wcs:Extension>
          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>x</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>99</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>y</wcs:Dimension>
            <wcs:TrimLow>0</wcs:TrimLow>
            <wcs:TrimHigh>99</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")


class WCS20PostGetCoverageScaleSizeMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:scal="http://www.opengis.net/wcs/scaling/1.0">
          <wcs:Extension>
            <scal:ScaleToSize>
              <scal:TargetAxisSize>
                <scal:axis>x</scal:axis>
                <scal:targetSize>50</scal:targetSize>
              </scal:TargetAxisSize>
              <scal:TargetAxisSize>
                <scal:axis>y</scal:axis>
                <scal:targetSize>50</scal:targetSize>
              </scal:TargetAxisSize>
            </scal:ScaleToSize>
          </wcs:Extension>
          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")


class WCS20PostGetCoverageScaleExtentMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:scal="http://www.opengis.net/wcs/scaling/1.0">
          <wcs:Extension>
            <scal:ScaleToExtent>
              <scal:TargetAxisExtent>
                <scal:axis>x</scal:axis>
                <scal:low>50</scal:low>
                <scal:high>100</scal:high>
              </scal:TargetAxisExtent>
              <scal:TargetAxisExtent>
                <scal:axis>y</scal:axis>
                <scal:low>50</scal:low>
                <scal:high>100</scal:high>
              </scal:TargetAxisExtent>
            </scal:ScaleToExtent>
          </wcs:Extension>
          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")


class WCS20PostGetCoverageInterpolationMultipartDatasetTestCase(wcsbase.WCS20GetCoverageMixIn, testbase.WCS20GetCoverageRectifiedGridCoverageMultipartTestCase):
    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:int="http://www.opengis.net/wcs/interpolation/1.0"
           xmlns:crs="http://www.opengis.net/wcs/crs/1.0">
          <wcs:Extension>
            <int:Interpolation>
              <int:globalInterpolation>http://www.opengis.net/def/interpolation/OGC/1/bilinear</int:globalInterpolation>
            </int:Interpolation>
            <crs:subsettingCrs>http://www.opengis.net/def/crs/EPSG/0/4326</crs:subsettingCrs>
          </wcs:Extension>
          <wcs:CoverageId>MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed</wcs:CoverageId>
          <wcs:DimensionTrim>
            <wcs:Dimension>Long</wcs:Dimension>
            <wcs:TrimLow>20</wcs:TrimLow>
            <wcs:TrimHigh>22</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:DimensionTrim>
            <wcs:Dimension>Lat</wcs:Dimension>
            <wcs:TrimLow>36</wcs:TrimLow>
            <wcs:TrimHigh>38</wcs:TrimHigh>
          </wcs:DimensionTrim>
          <wcs:format>image/tiff</wcs:format>
          <wcs:mediaType>multipart/related</wcs:mediaType>
        </wcs:GetCoverage>"""
        return (params, "xml")


# WCS 2.0 GetCoverage GeoTIFF

class WCS20GetCoverageDatasetGeoTIFFPackBitsTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "PACKBITS"

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=PackBits"
        return (params, "kvp")

class WCS20GetCoverageDatasetGeoTIFFHuffmanTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "CCITTRLE"

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=Huffman"
        return (params, "kvp")

class WCS20GetCoverageDatasetGeoTIFFLZWTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "LZW"

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=LZW"
        return (params, "kvp")


class WCS20GetCoverageDatasetGeoTIFFJPEGLowTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "JPEG"
    expected_jpeg_quality = 50

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=JPEG&geotiff:jpeg_quality=50"
        return (params, "kvp")


class WCS20GetCoverageDatasetGeoTIFFJPEGHighTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "JPEG"
    expected_jpeg_quality = 90

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=JPEG&geotiff:jpeg_quality=90"
        return (params, "kvp")


class WCS20GetCoverageDatasetGeoTIFFDeflateTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_compression = "DEFLATE"

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:compression=Deflate&geotiff:predictor=Horizontal"
        return (params, "kvp")


class WCS20GetCoverageDatasetGeoTIFFInterleaveBandTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_interleave = "BAND"

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:interleave=Band"
        return (params, "kvp")


class WCS20GetCoverageDatasetGeoTIFFTiled16TestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_tiling = (16, 16)

    def getRequest(self):
        params = "service=wcs&version=2.0.0&request=GetCoverage&CoverageId=MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_uint16_reduced_compressed&format=image/tiff&geotiff:tiling=true&geotiff:tilewidth=16&geotiff:tileheight=16"
        return (params, "kvp")

class WCS20GetCoverageDatasetGeoTIFFPostTestCase(wcsbase.GeoTIFFMixIn, testbase.RectifiedGridCoverageTestCase):
    expected_tiling = (32, 64)
    expected_interleave = "BAND"
    expected_compression = "DEFLATE"

    def getRequest(self):
        params = """<wcs:GetCoverage service="WCS" version="2.0.1"
           xmlns:wcs="http://www.opengis.net/wcs/2.0"
           xmlns:geotiff="http://www.opengis.net/gmlcov/geotiff/1.0">
          <wcs:CoverageId>mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced</wcs:CoverageId>
          <wcs:format>image/tiff</wcs:format>
          <wcs:Extension>
            <geotiff:parameters>
              <geotiff:compression>Deflate</geotiff:compression>
              <geotiff:predictor>FloatingPoint</geotiff:predictor>
              <geotiff:interleave>Band</geotiff:interleave>
              <geotiff:tiling>true</geotiff:tiling>
              <geotiff:tilewidth>32</geotiff:tilewidth>
              <geotiff:tileheight>64</geotiff:tileheight>
            </geotiff:parameters>
          </wcs:Extension>
        </wcs:GetCoverage>"""
        return (params, "xml")
