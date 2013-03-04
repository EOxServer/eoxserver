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
import logging

from eoxserver.resources.coverages import crss #import hasSwappedAxes, fromURL


logger = logging.getLogger(__name__)

def pairwise(iterable):
    "s -> (s0,s1), (s2,s3), (s4, s5), ..."
    a = iter(iterable)
    return izip(a, a)


class PolygonMask(object):
    def __init__(self, coords, crs=None):
        # check if the axes should be swapped
        
        self.srid = crss.fromURL(crs) if crs else None
        self.crs = crs

        if self.srid is not None and crss.hasSwappedAxes(self.srid):
            self.coords = [(x, y) for (y, x) in coords]
        else:
            self.coords = list(coords)
        
        # make sure the polygon is closed    
        if self.coords[:2] != self.coords[-2:]:
            self.coords.extend(self.coords[:2])
        
    
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
    
    
    @property
    def has_mask(self):
        return (len(self.polygons) + len(self.coverages)) > 0
    
    
    def _decode(self, req):
        if req.getParamType() == "kvp":
            self._decodeKVP(req)
        else:
            self._decodeXML(req)
        
    
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
                    raw_coords = map(float, mask_value.split(","))
                    if len(raw_coords) % 2 != 0:
                        raise Exception("Invalid number of coordinates given.")
                    
                    pairs = pairwise(raw_coords)
                    self.polygons.append(PolygonMask(pairs, crs))
                
                
                elif method.lower() in ("coverage", "coverages", "coverageid", "coverageids"):
                    self.coverages.extend(mask_value.split(","))

    def _decodeXML(self, req):
        # TODO: implement
        polygons = req.getParamValue("polygonmasks")
        for polygon in polygons:
            raw_coords = map(float, polygon.split(" "))
            if len(raw_coords) % 2 != 0:
                raise Exception("Invalid number of coordinates given.")
            
            pairs = pairwise(raw_coords)
            self.polygons.append(PolygonMask(pairs))
            # TODO: crs?
        
        