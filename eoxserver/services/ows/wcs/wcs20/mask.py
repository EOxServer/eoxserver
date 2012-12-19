#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

import re
from itertools import izip

from eoxserver.resources.coverages import crss #import hasSwappedAxes, fromURL

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


class PolygonMask(object):
    def __init__(self, coords, crs=None):
        srid = crss.fromURL(crs)
        if srid is not None and crss.hasSwappedAxes(srid):
            self.coords = [(y, x) for (x, y) in coords]
        else:
            self.coords = coords
        self.crs = crs
    
    
    def __iter__(self):
        return iter(self.coords)
    
    
    def __len__(self):
        return len(self.coords)
    
    
    def to_wkt(self):
        pass # TODO: implement



class WCS20MaskDecoder(object):
    """ Parser class for WCS 2.0 mask request parameters. Not yet OGC standardized. """
    
    def __init__(self, req):
        self.polygons = []
        self.coverages = []
        self._decode(req)
        
    
    def _decode(self, req):
        if req.getParamType() == "kvp":
            self._decodeKVP(req)
        else:
            self._decodeXML()
        
    
    def _decodeKVP(self, req):
        for key, values in req.getParams().items():
            if not key.startswith("mask"):
                continue
            
            for value in values:
                match = re.match(
                    r'(\w+)(,([^(]+))?()\(([^(^)]*)\)', value
                )
                
                if not match:
                    raise Exception("Invalid `mask` expression.")
                
                method = match.group(1)
                crs = match.group(3)
                mask_value = match.group(5)
                
                if method.lower() == "polygon":
                    coords = pairwise(map(float, mask_value.split(",")))
                    self.polygons.append(object)
                    
                    self.polygons.append(PolygonMask(coords, crs))
                
                elif method.lower() in ("coverageid", "coverageids"):
                    self.coverages.extend(mask_value.split(","))

    def _decodeXML(self):
        # TODO: implement
        pass
        
        