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


class WCS11CoverageDescrptionRenderParams(CoverageDescriptionRenderParams):
    coverage_ids_key_name = "identifier"

    def __init__(self, coverages):
        super(WCS11CoverageDescrptionRenderParams, self).__init__(
            coverages, "1.1.2"
        )


class WCS11CoverageRenderParams(CoverageRenderParams):
    def __init__(self, coverage, bbox, format, gridcs=None, gridbasecrs=None, 
                 gridtype=None, gridorigin=None, gridoffsets=None):

        super(WCS11CoverageRenderParams, self).__init__(coverage, "1.1.2")
        self._bbox = list(bbox)
        self._format = format
        self._gridcs = gridcs
        self._gridbasecrs = gridbasecrs
        self._gridtype = gridtype
        self._gridorigin = gridorigin
        self._gridoffsets = gridoffsets

    coverage_id_key_name = "identifier"

    bbox        = property(lambda self: self._bbox)
    format      = property(lambda self: self._format)
    gridcs      = property(lambda self: self._gridcs)
    gridbasecrs = property(lambda self: self._gridbasecrs)
    gridtype    = property(lambda self: self._gridtype)
    gridorigin  = property(lambda self: self._gridorigin)
    gridoffsets = property(lambda self: self._gridoffsets)

    @property
    def subsets(self):
        return Subsets((
            Trim("x", self._bbox[0], self._bbox[2]),
            Trim("y", self._bbox[1], self._bbox[3]),
        ), crs=self._bbox[4])


    def __iter__(self):
        for k, v in super(WCS11CoverageRenderParams, self).__iter__():
            yield k, v

        yield ("boundingbox", ",".join(map(str, self.bbox)))
        yield ("format", self.format)
        
        if self.gridcs:
            yield ("gridcs", self.gridcs)
        
        if self.gridbasecrs:
            yield ("gridbasecrs", self.gridbasecrs)
        
        if self.gridoffsets:
            yield ("gridoffsets", ",".join(map(str, self.gridoffsets)))
        
        if self.gridtype is not None:
            yield ("gridtype", self.gridtype)
        
        if self.gridorigin is not None:
            yield ("gridorigin", ",".join(map(str, self.gridorigin)))
