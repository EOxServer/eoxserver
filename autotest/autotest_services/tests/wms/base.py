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

from unittest import SkipTest, skipIf
import numpy as np
try:
    from scipy.stats import linregress
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False
from eoxserver.testing.utils import tag

from autotest_services import base as testbase


format_to_extension = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/tiff": "tif"
}

@tag('wms', 'wms11', 'getmap')
class WMS11GetMapTestCase(testbase.RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    time = None
    dim_bands = None

    swap_axes = True

    httpHeaders = None

    def getFileExtension(self, part=None):
        try:
            return format_to_extension[self.frmt]
        except KeyError:
            return testbase.mimetypes.guess_extension(self.frmt, False)[1:]

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

        if self.dim_bands:
            params += "&dim_bands=%s" % self.dim_bands

        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)

@tag('wms', 'wms13', 'getmap')
class WMS13GetMapTestCase(testbase.RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    time = None
    dim_bands = None

    swap_axes = True

    httpHeaders = None

    def getFileExtension(self, part=None):
        try:
            return format_to_extension[self.frmt]
        except KeyError:
            return testbase.mimetypes.guess_extension(self.frmt, False)[1:]

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

        if self.dim_bands:
            params += "&dim_bands=%s" % self.dim_bands

        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)


@tag('wms', 'wms13', 'exception')
class WMS13ExceptionTestCase(testbase.ExceptionTestCase):
    def getExceptionCodeLocation(self):
        return "ogc:ServiceException/@code"

@tag('wms', 'wms13')
class WMSTIFFComparison(WMS13GetMapTestCase, testbase.GDALDatasetTestCase):
    def testBinaryComparisonRaster(self):
        self.skipTest('compare the band size, count, and statistics')
    @tag('stastics')
    @skipIf(not HAVE_SCIPY, "scipy modoule is not installed")
    def testBandStatistics(self):
        for band in range( self.res_ds.RasterCount ):
            band += 1
            if band:
                exp_band = self.exp_ds.GetRasterBand(band)
                res_band = self.res_ds.GetRasterBand(band)
                array1 = np.array(exp_band.ReadAsArray()).flatten()
                array2 = np.array(res_band.ReadAsArray()).flatten()
                regress_result = linregress(array1,array2)
                self.assertGreaterEqual(regress_result.rvalue, 0.9)

@tag('wms')
class WMS11GetLegendTestCase(testbase.RasterTestCase):
    layers = []
    styles = []
    frmt = "image/png"

    def getFileExtension(self, part=None):
        try:
            return format_to_extension[self.frmt]
        except KeyError:
            return testbase.mimetypes.guess_extension(self.frmt, False)[1:]

    def getRequest(self):
        params = "service=WMS&request=GetMap&version=1.1.1&" \
                 "layers=%s&styles=%s&format=%s" % (
                     ",".join(self.layers), ",".join(self.styles), self.frmt
                 )
        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)