from eoxserver.processing.gdal.reftools import get_footprint_wkt
from eoxserver.processing.preprocessing.util import (
    gdal, ogr, osr, create_mem, copy_metadata
) 


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
        # TODO: sanitize GCP list
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
        
        footprint_wkt = get_footprint_wkt(src_ds)
        if not gcp_sr.IsGeographic():
            out_sr = osr.SpatialReference()
            out_sr.ImportFromEPSG(4326)
            geom = ogr.CreateGeometryFromWkt(footprint_wkt, gcp_sr)
            geom.TransformTo(out_sr)
            footprint_wkt = geom.ExportToWkt()
        
        return dst_ds, footprint_wkt

