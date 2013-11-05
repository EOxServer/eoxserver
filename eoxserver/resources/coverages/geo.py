#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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
import logging

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.contrib import osr
from eoxserver.processing.gdal import reftools as rt 
from eoxserver.resources.coverages import crss 


logger = logging.getLogger(__name__)

# extent calculation 
def getExtentFromRectifiedDS( ds , eps=1e-6 ):
    """ Calculates the extent tuple of the given gdal.Dataset. The dataset 
    must be rectified, i.e. projected to a recognized CRS, and the geocoding 
    must be encoded by the GDAL's Geo-Transformation matrix.
    
    The ``eps`` parameter is the relative threshold for non-zero values of
    non-diagonal terms of the GDAL's Geo-Transformation matrix.
    """

    size_x = ds.RasterXSize
    size_y = ds.RasterYSize

    x0 , dxx , dxy , y0 , dyx , dyy = ds.GetGeoTransform()

    if ( abs(eps*dxx) < abs(dxy) ) or ( abs(eps*dyy) < abs(dyx) ) :  
        RuntimeError( "Rectified datasets with non-orthogonal or"
            " rotated axes are not supported" ) 

    if ( dxx < 0 ) or ( dyy > 0 ) :  
        RuntimeError( "Rectified datasets with flipped axes directions"
            " are not supported" ) 

    x1 , y1 = ( x0 + size_x * dxx ) , ( y0 + size_y * dyy ) 

    return ( x0 , y1 , x1 , y0 ) 

def getExtentFromReferenceableDS( ds ):
    """ Calculates the extent tuple of the given gdal.Dataset. The dataset 
    must be encoded using the tie-points. 
    """

    filelist = ds.GetFileList()

    if 1 != len( filelist ) : 
        RuntimeError( "Cannot get a single dataset filename!" ) 
        
    rt_prm = rt.suggest_transformer(filelist[0]) 
    fp_wkt = rt.get_footprint_wkt(filelist[0],**rt_prm)

    return GEOSGeometry( fp_wkt ).extent 


class GeospatialMetadata(object):
    """
    This class wraps geospatial metadata retrieved from a GDAL dataset. It has
    four optional attributes which default to ``None`` and one defaulting to
    ``False``:
    
    * ``srid``: the SRID of the CRS of the dataset
    * ``size_x``, ``size_y``: the dimension of the dataset
    * ``extent``: the geospatial extent of the dataset in the CRS given by the
      SRID
    * ``is_referenceable``: boolean value if the dataset is a referenceable
      grid coverage.
    """
    
    def __init__(self, srid, size_x, size_y, extent, is_referenceable=False):

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

        size_x = ds.RasterXSize
        size_y = ds.RasterYSize
        
        is_ref = ds.GetGCPCount() > 0 

        proj   = ds.GetGCPProjection() if is_ref else ds.GetProjection() 

        if not isinstance(proj,basestring) or len(proj)<1 : 
            raise RuntimeError("Failed to extract CRS (projection) of the "
                    "dataset!" ) 
                
        # convert projection to EPSG code 

        srs = osr.SpatialReference()
    
        try:
            srs.ImportFromWkt( proj )
            srs.AutoIdentifyEPSG()
            ptype = "PROJCS" if srs.IsProjected() else "GEOGCS"
            srid = int(srs.GetAuthorityCode(ptype))

        except (RuntimeError, TypeError), e:
            logger.warn("Projection: %s" % proj) 
            logger.warn("Failed to identify projection's EPSG code."
                "%s: %s" % ( type(e).__name__ , str(e) ) ) 

            if default_srid is not None:
                logger.warn("Using the provided SRID '%s' instead."
                   % str(default_srid) )
            else:
                raise RuntimeError("Unknown SRS and no default supplied.")

            #validate the default SRID 
            if not crss.validateEPSGCode( default_srid ) : 
                raise RuntimeError("The default SRID '%s' is not a valid" 
                    " EPSG code." % str(default_srid) )

            srid = int(default_srid)
                 

        # get the extent 

        if is_ref: # Referenceable DS 

            extent = getExtentFromReferenceableDS( ds )

        else: # Rectified DS 
        
            extent = getExtentFromRectifiedDS( ds )

        # instantiate the class 
        return cls( srid, size_x, size_y, extent, is_ref )

