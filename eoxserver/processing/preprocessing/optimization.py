import numpy

from eoxserver.processing.preprocessing.util import ( 
    gdal, gdal_array, gdalconst, osr, get_limits, create_mem, copy_metadata, 
    copy_projection
)
from eoxserver.resources.coverages.crss import (
    parseEPSGCode, fromShortCode, fromURL, fromURN, fromProj4Str
)


#===============================================================================
# Dataset Optimization steps
#===============================================================================

class DatasetOptimization(object):
    """ Abstract base class for dataset optimization steps. Each optimization
        step shall be callable and return the dataset or a copy thereof if 
        necessary.
    """
    
    def __call__(self, ds):
        raise NotImplementedError


class ReprojectionOptimization(DatasetOptimization):
    """ Dataset optimization step to reproject the dataset into a predefined
        projection identified by an SRID.
    """

    def __init__(self, crs_or_srid):
        if isinstance(crs_or_srid, int):
            pass
        elif isinstance(crs_or_srid, basestring):
            crs_or_srid = parseEPSGCode(crs_or_srid, (fromShortCode, fromURL,
                                                      fromURN, fromProj4Str))
        else:
            raise ValueError("Unable to obtain CRS from '%s'." %
                             type(crs_or_srid).__name__)
        
        self.srid = crs_or_srid

        
    def __call__(self, src_ds):
        # setup
        src_sr = osr.SpatialReference()
        src_sr.ImportFromWkt(src_ds.GetProjection())
        
        dst_sr = osr.SpatialReference()
        dst_sr.ImportFromEPSG(self.srid)
        
        # create a temporary dataset to get information about the output size
        tmp_ds = gdal.AutoCreateWarpedVRT(src_ds, None, dst_sr.ExportToWkt(), 
                                          gdal.GRA_Bilinear, 0.125)
        
        # create the output dataset
        dst_ds = create_mem(tmp_ds.RasterXSize, tmp_ds.RasterYSize,
                            src_ds.RasterCount, 
                            src_ds.GetRasterBand(1).DataType)
        
        
        # reproject the image
        dst_ds.SetProjection(dst_sr.ExportToWkt())
        dst_ds.SetGeoTransform(tmp_ds.GetGeoTransform())
        
        gdal.ReprojectImage(src_ds, dst_ds,
                            src_sr.ExportToWkt(),
                            dst_sr.ExportToWkt(),
                            gdal.GRA_Bilinear)
        
        tmp_ds = None
        
        # copy the metadata
        copy_metadata(src_ds, dst_ds)
        
        return dst_ds


class BandSelectionOptimization(DatasetOptimization):
    """ Dataset optimization step which selects a number of bands and their 
    respective scale and copies them to the result dataset. 
    """
    
    def __init__(self, bands, datatype=gdalconst.GDT_Byte):
        # preprocess bands list
        # TODO: improve
        self.bands = map(lambda b: b  if len(b) == 3 else (b[0], None, None),
                         bands)
        self.datatype = datatype
        
    
    def __call__(self, src_ds):
        dst_ds = create_mem(src_ds.RasterXSize, src_ds.RasterYSize, 
                            len(self.bands), self.datatype)
        dst_range = get_limits(self.datatype)
        
        for dst_index, (src_index, dmin, dmax) in enumerate(self.bands, 1):
            src_band = src_ds.GetRasterBand(src_index)
            src_min, src_max = src_band.ComputeRasterMinMax()
            
            # get min/max values or calculate from band
            if dmin is None:
                dmin = get_limits(src_band.DataType)[0]
            elif dmin == "min":
                dmin = src_min
            if dmax is None:
                dmax = get_limits(src_band.DataType)[1]
            elif dmax == "max":
                dmax = src_max
            src_range = (dmin, dmax)
            
            data = src_band.ReadAsArray()
            
            # perform scaling
            data = numpy.clip(data, dmin, dmax)
            data = ((dst_range[1] - dst_range[0]) * 
                    ((data - src_range[0]) / (src_range[1] - src_range[0])))
            
            data = data.astype(gdal_array.codes[self.datatype])
            
            # write result
            dst_band = dst_ds.GetRasterBand(dst_index)
            dst_band.WriteArray(data)
        
        copy_projection(src_ds, dst_ds)
        copy_metadata(src_ds, dst_ds)
        
        return dst_ds


class ColorIndexOptimization(DatasetOptimization):
    """ Dataset optimization step to replace the pixel color values with a color
        index. If no color palette is given (e.g: a VRT or any other dataset 
        containing a color table), this step takes the first three bands and 
        computes a median color table.
    """
    
    def __init__(self, palette_file=None):
        self.palette_file = palette_file
    
    
    def __call__(self, src_ds):
        dst_ds = create_mem(src_ds.RasterXSize, src_ds.RasterYSize, 
                            1, gdalconst.GDT_Byte)
        
        if not self.palette_file:
            # create a color table as a median of the given dataset
            ct = gdal.ColorTable()
            gdal.ComputeMedianCutPCT(src_ds.GetRasterBand(1),
                                     src_ds.GetRasterBand(2),
                                     src_ds.GetRasterBand(3),
                                     256, ct)
        
        else:
            # copy the color table from the given palette file
            pct_ds = gdal.Open(self.palette_file)
            pct_ct = pct_ds.GetRasterBand(1).GetRasterColorTable()
            if not pct_ct:
                raise ValueError("The palette file '%s' does not have a Color "
                                 "Table." % self.palette_file)
            ct = pct_ct.Clone()
            pct_ds = None
        
        dst_ds.GetRasterBand(1).SetRasterColorTable(ct)
        gdal.DitherRGB2PCT(src_ds.GetRasterBand(1),
                           src_ds.GetRasterBand(2),
                           src_ds.GetRasterBand(3),
                           dst_ds.GetRasterBand(1), ct)
        
        copy_projection(src_ds, dst_ds)
        copy_metadata(src_ds, dst_ds)
        
        return dst_ds


class NoDataValueOptimization(DatasetOptimization):
    """ This optimization step assigns a no-data value to all raster bands in
        a dataset.
    """
    
    def __init__(self, nodata_values):
        self.nodata_values = nodata_values
        
        
    def __call__(self, ds):
        nodata_values = self.nodata_values
        if len(nodata_values) == 1:
            nodata_values = nodata_values * ds.RasterCount
        
        #TODO: bug, the same nodata value is set to all bands?
        
        for index, value in enumerate(nodata_values, start=1):
            try:
                ds.GetRasterBand(index).SetNoDataValue(value)
            except RuntimeError:
                pass # TODO
        
        return ds


#===============================================================================
# Post-create optimization steps
#===============================================================================

class DatasetPostOptimization(object):
    """ Abstract base class for dataset post-creation optimization steps. These
        opotimizations are performed on the actually produced dataset. This is
        required by some optimization techiques.
    """
    
    def __call__(self, ds):
        raise NotImplementedError


class OverviewOptimization(DatasetPostOptimization):
    """ Dataset optimization step to add overviews to the dataset. This step may
        have to be applied after the dataset has been reprojected.
    """
    
    def __init__(self, resampling=None):
        self.resampling = resampling
    
    
    def __call__(self, ds):
        ds.BuildOverviews(self.resampling, [2, 4, 8, 16])
        return ds

