#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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

import logging

from eoxserver.processing.gdal.reftools import get_footprint_wkt
from eoxserver.processing.preprocessing.util import (
    gdal, ogr, osr, create_mem, copy_metadata
)


logger = logging.getLogger(__name__)


#===============================================================================
# Geographic references
#===============================================================================

class GeographicReference(object):
    pass


class Extent(GeographicReference):
    """ Sets the extent of the dataset expressed as a 4-tuple (minx, miny, maxx,
        maxy) with an optional SRID (defaults to EPSG: 4326). 
    """
    def __init__(self, minx, miny, maxx, maxy, srid=4326):
        self.minx, self.miny, self.maxx, self.maxy = minx, miny, maxx, maxy
        self.srid = srid
    
    
    def apply(self, ds):
        """ Set the geotransform and projection of the dataset according to 
            the defined extent and SRID.
        """
        sr = osr.SpatialReference(); sr.ImportFromEPSG(self.srid)
        ds.SetGeoTransform([ # TODO: correct?
            self.minx,
            (self.maxx - self.minx) / ds.RasterXSize,
            0,
            self.maxy,
            0,
            -(self.maxy - self.miny) / ds.RasterYSize
        ])
        ds.SetProjection(sr.ExportToWkt())
        
        return ds, None


class GCPList(GeographicReference):
    """ Sets a list of GCPs (Ground Control Points) to the dataset and then 
        performs a rectification to a projection specified by SRID.
    """
    
    def __init__(self, gcps, gcp_srid=4326, srid=None):
        """ Expects a list of GCPs as a list of tuples in the form 
            'x,y,[z,]pixel,line'.
        """
        
        self.gcps = map(lambda gcp: gdal.GCP(*gcp) if len(gcp) == 5 
                        else gdal.GCP(gcp[0], gcp[1], 0.0, gcp[2], gcp[3]), 
                        gcps)
        self.gcp_srid = gcp_srid
        self.srid = srid
    
        
    def apply(self, src_ds):
        # setup
        dst_sr = osr.SpatialReference()
        gcp_sr = osr.SpatialReference()
        
        dst_sr.ImportFromEPSG(self.srid if self.srid is not None 
                              else self.gcp_srid) 
        gcp_sr.ImportFromEPSG(self.gcp_srid)
        
        
        logger.debug("Using GCP Projection '%s'" % gcp_sr.ExportToWkt())
        logger.debug("Applying GCPs: \n%s"
                     % "\n".join(["%f %f -> %f %f" 
                                  % (gcp.GCPPixel, gcp.GCPLine, gcp.GCPX, gcp.GCPY)
                                  for gcp in self.gcps]))
        
        # set the GCPs
        src_ds.SetGCPs(self.gcps, gcp_sr.ExportToWkt())
        
        # create a temporary VRT, to find out the size of the output image
        tmp_ds = gdal.AutoCreateWarpedVRT(src_ds, None, dst_sr.ExportToWkt(), 
                                          gdal.GRA_Bilinear, 0.125)
        
        dst_ds = create_mem(tmp_ds.RasterXSize, tmp_ds.RasterYSize,
                            src_ds.RasterCount, 
                            src_ds.GetRasterBand(1).DataType)
        
        # reproject the image
        dst_ds.SetProjection(dst_sr.ExportToWkt())
        dst_ds.SetGeoTransform(tmp_ds.GetGeoTransform())
        
        gdal.ReprojectImage(src_ds, dst_ds, "", "", gdal.GRA_Bilinear)
        
        tmp_ds = None
        
        copy_metadata(src_ds, dst_ds)
        
        # TODO: maybe refine this
        method = "TPS" if len(self.gcps) > 10 else "GCP"
        
        footprint_wkt = get_footprint_wkt(src_ds, method)
        if not gcp_sr.IsGeographic():
            out_sr = osr.SpatialReference()
            out_sr.ImportFromEPSG(4326)
            geom = ogr.CreateGeometryFromWkt(footprint_wkt, gcp_sr)
            geom.TransformTo(out_sr)
            footprint_wkt = geom.ExportToWkt()
        
        logger.debug("Calculated footprint: '%s'." % footprint_wkt)
        
        return dst_ds, footprint_wkt

