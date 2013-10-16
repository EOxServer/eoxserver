from autotest_services import testbase
import base as wcsbase



#===============================================================================
# WCS 1.0
#===============================================================================

class WCS10GetCapabilitiesValidTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCS10GetCapabilitiesEmptyTestCase(testbase.XMLTestCase):
    """This test shall retrieve a valid but empty WCS 1.0 GetCapabilities response (see #41)"""
    fixtures = testbase.BASE_FIXTURES
    
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCapabilities"
        return (params, "kvp")

class WCS10DescribeCoverageDatasetTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=DescribeCoverage&coverage=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced"
        return (params, "kvp")

class WCS10DescribeCoverageMosaicTestCase(testbase.XMLTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=DescribeCoverage&coverage=mosaic_MER_FRS_1P_RGB_reduced"
        return (params, "kvp")

class WCS10GetCoverageDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=GeoTIFF"
        return (params, "kvp")

class WCS10GetCoverageMosaicTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1P_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=image/tiff"
        return (params, "kvp")
