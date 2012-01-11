#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""
This module supports reading of geospatial metadata from GDAL datasets.
"""

from osgeo import osr


class GeospatialMetadata(object):
    """
    This class wraps geospatial metadata retrieved from a GDAL dataset. It has
    four optional attributes which default to ``None``:
    
    * ``srid``: the SRID of the CRS of the dataset
    * ``size_x``, ``size_y``: the dimension of the dataset
    * ``extent``: the geospatial extent of the dataset in the CRS given by the
      SRID
    * ``is_referenceable``: boolean value if the dataset is a referenceable
      grid coverage.
    """
    
    def __init__(self, srid=None, size_x=None, size_y=None, extent=None, is_referenceable=False):
        self.srid = srid
        self.size_x = size_x
        self.size_y = size_y
        self.extent = extent
        self.is_referenceable = is_referenceable
        
    @classmethod
    def readFromDataset(cls, ds, default_srid=None):
        """
        This class method returns a :class:`GeospatialMetadata` object
        initialized with the metadata read from the GDAL dataset ``ds``. It
        expects an open :class:`osgeo.gdal.Dataset` object as input. Furthermore
        it accepts an optional integer ``default_srid`` parameter that will be
        used to set the SRID if it cannot be retrieved from the dataset.
        """
        gt = ds.GetGeoTransform()
        
        srid = None
        projection = ds.GetProjection()
        if projection is not None and len(projection) != 0:
            srs = osr.SpatialReference()
            srs.ImportFromWkt(projection)
            
            srs.AutoIdentifyEPSG()
            if srs.IsProjected():
                srid = srs.GetAuthorityCode("PROJCS")
            elif srs.IsGeographic():
                srid = srs.GetAuthorityCode("GEOGCS")
            
        if srid is None and default_srid is not None:
            srid = int(default_srid)
        elif srid is None:
            pass
        else:
            srid = int(srid)
    
        size_x = ds.RasterXSize
        size_y = ds.RasterYSize
        
        if gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            xl = gt[0]
            yl = gt[3]
            xh = gt[0] + size_x * gt[1]
            yh = gt[3] + size_y * gt[5]
            
            extent = (
                min(xl, xh), min(yl, yh), max(xl, xh), max(yl, yh)
            )
            return cls(srid, size_x, size_y, extent)
        
        elif ds.GetGCPCount() > 0:
            return cls(size_x=size_x, size_y=size_y, is_referenceable=True)
        
        else:
            return None
        
