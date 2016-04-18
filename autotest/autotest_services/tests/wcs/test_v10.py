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
        params = "service=WCS&version=1.0.0&request=DescribeCoverage&coverage=mosaic_MER_FRS_1P_reduced_RGB"
        return (params, "kvp")

class WCS10GetCoverageDatasetTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=GeoTIFF"
        return (params, "kvp")

class WCS10GetCoverageMosaicTestCase(testbase.RectifiedGridCoverageTestCase):
    def getRequest(self):
        params = "service=WCS&version=1.0.0&request=GetCoverage&coverage=mosaic_MER_FRS_1P_reduced_RGB&crs=epsg:4326&bbox=-4,32,28,46.5&width=640&height=290&format=image/tiff"
        return (params, "kvp")
