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


format_to_extension = {
    "image/jpeg": "jpeg",
    "image/png": "png",
    "image/gif": "gif"
}

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

class WMS13ExceptionTestCase(testbase.ExceptionTestCase):
    def getExceptionCodeLocation(self):
        return "ogc:ServiceException/@code"
