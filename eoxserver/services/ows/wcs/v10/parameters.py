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

from eoxserver.services.ows.wcs.parameters import (
    CoverageRenderParams, CoverageDescriptionRenderParams
)
from eoxserver.services.subset import Subsets, Trim


class WCS10CoverageDescriptionRenderParams(CoverageDescriptionRenderParams):
    coverage_ids_key_name = "coverage"

    def __init__(self, coverages):
        super(WCS10CoverageDescriptionRenderParams, self).__init__(
            coverages, "1.0.0"
        )


class WCS10CoverageRenderParams(CoverageRenderParams):
    def __init__(self, coverage, bbox, crs, format, response_crs=None, 
                 width=None, height=None, resx=None, resy=None, 
                 interpolation=None):

        super(WCS10CoverageRenderParams, self).__init__(coverage, "1.0.0")
        self._bbox = list(bbox)
        self._crs = crs
        self._format = format
        self._response_crs = response_crs
        self._width = width
        self._height = height
        self._resx = resx
        self._resy = resy
        self._interpolation = interpolation

    coverage_id_key_name = "coverage"

    bbox          = property(lambda self: self._bbox)
    crs           = property(lambda self: self._crs)
    format        = property(lambda self: self._format)
    response_crs  = property(lambda self: self._response_crs)
    width         = property(lambda self: self._width)
    height        = property(lambda self: self._height)
    resx          = property(lambda self: self._resx)
    resy          = property(lambda self: self._resy)
    interpolation = property(lambda self: self._interpolation)

    @property
    def subsets(self):
        return Subsets((
            Trim("x", self._bbox[0], self._bbox[2]),
            Trim("y", self._bbox[1], self._bbox[3]),
        ), crs=self._crs)


    def __iter__(self):
        for k, v in super(WCS10CoverageRenderParams, self).__iter__():
            yield k, v

        yield ("bbox", ",".join(map(str, self.bbox)))
        yield ("crs", self.crs)
        yield ("format", self.format)
        
        if self.response_crs:
            yield ("response_crs", self.response_crs)
        
        if self.width is not None:
            yield ("width", str(self.width))
        
        if self.height is not None:
            yield ("height", str(self.height))
        
        if self.resx is not None:
            yield ("resx", self.resx)

        if self.resy is not None:
            yield ("resy", self.resy)
        
        if self.interpolation:
            yield ("interpolation", self.interpolation)
