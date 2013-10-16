from autotest_services import testbase
import base as wmsbase


#===============================================================================
# WMS
#===============================================================================

class WMS11GetCapabilitiesValidTestCase(testbase.OWSTestCase):
    """This test shall retrieve a valid WMS 1.1 GetCapabilities response"""
    def getRequest(self):
        params = "service=WMS&version=1.1.1&request=GetCapabilities"
        return (params, "kvp")

class WMS11GetMapMultipleDatasetsTestCase(wmsbase.WMS11GetMapTestCase):
    """ Test a GetMap request with two datasets. """
    layers = ("mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
              "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced",
              )
    width = 200
    bbox = (-3.75, 32.19025, 28.29481, 46.268645)

