from autotest_services import testbase


class WMS11GetMapTestCase(testbase.RasterTestCase):
    layers = []
    styles = []
    crs = "epsg:4326"
    bbox = (0, 0, 1, 1)
    width = 100
    height = 100
    frmt = "image/jpeg"
    time = None
    dim_band = None
    
    swap_axes = True
    
    httpHeaders = None
    
    def getFileExtension(self, part=None):
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
            
        if self.dim_band:
            params += "&dim_band=%s" % self.dim_band
        
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
    dim_band = None
    
    swap_axes = True
    
    httpHeaders = None
    
    def getFileExtension(self, part=None):
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
            
        if self.dim_band:
            params += "&dim_band=%s" % self.dim_band
        
        if self.httpHeaders is None:
            return (params, "kvp")
        else:
            return (params, "kvp", self.httpHeaders)

class WMS13ExceptionTestCase(testbase.ExceptionTestCase):
    def getExceptionCodeLocation(self):
        return "/{http://www.opengis.net/ogc}ServiceException/@code"
