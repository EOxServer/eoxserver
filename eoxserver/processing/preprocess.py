#!/usr/bin/env python
#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from os.path import splitext, exists
import numpy

from osgeo import gdal, ogr, osr, gdalconst, gdal_array
from django.contrib.gis.geos import GEOSGeometry
from eoxserver.core.util.xmltools import DOMElementToXML
from eoxserver.resources.coverages.metadata import NativeMetadataFormatEncoder

gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()


SUPPORTED_COMPRESSIONS = ("JPEG", "LZW", "PACKBITS", "DEFLATE", "CCITTRLE",
                          "CCITTFAX3", "CCITTFAX4", "NONE")

NUMERIC_LIMITS = {
    gdalconst.GDT_Byte: (0, 255), # TODO: make others aswell?
}

# enum for bandmode
RGB, RGBA, ORIG_BANDS = range(3)


#===============================================================================
# helper functions
#===============================================================================

def _create_mem_copy(ds, *args, **kwargs):
    """ Create a new In-Memory Dataset as copy from an existing dataset. """
    mem_drv = gdal.GetDriverByName('MEM')
    return mem_drv.CreateCopy('', ds, *args, **kwargs)
    

def _create_mem(sizex, sizey, numbands, datatype=gdalconst.GDT_Byte,
                options=None):
    """ Create a new In-Memory Dataset. """
    if options is None:
        options = []
    
    mem_drv = gdal.GetDriverByName('MEM')
    return mem_drv.Create('', sizex, sizey, numbands, datatype, options)


def _copy_projection(src_ds, dst_ds):
    """ Copy the projection and geotransform from on dataset to another """
    dst_ds.SetProjection(src_ds.GetProjection())
    dst_ds.SetGeoTransform(src_ds.GetGeoTransform())

    
def _copy_metadata(src_ds, dst_ds):
    """ Copy the metadata from on dataset to another """
    dst_ds.SetMetadata(src_ds.GetMetadata_Dict())


def _check_file_existence(filename):
    " Check if file exists and raise an IOError if it does. "
    if exists(filename):
        raise IOError("The output file '%s' already exists." % filename)

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
        return ds
    

class Footprint(GeographicReference):
    """  """
    # TODO: implement
    pass


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
        
        dst_ds = _create_mem(tmp_ds.RasterXSize, tmp_ds.RasterYSize,
                             src_ds.RasterCount, 
                             src_ds.GetRasterBand(1).DataType)
        
        # reproject the image
        dst_ds.SetProjection(dst_sr.ExportToWkt())
        dst_ds.SetGeoTransform(tmp_ds.GetGeoTransform())
        
        gdal.ReprojectImage(src_ds, dst_ds, "", "", gdal.GRA_Bilinear)
        
        tmp_ds = None
        
        _copy_metadata(src_ds, dst_ds)
        
        return dst_ds
        

#===============================================================================
# Format selection
#===============================================================================


class FormatSelection(object):
    """ Format selection with format specific options. Currently supports GTiff
        only.
    """
    
    def __init__(self, driver_name="GTiff", tiling=True, compression=None, 
                 jpeg_quality=None, zlevel=None, creation_options=None):
        self._driver_name = driver_name
        self.final_options = {}
        if compression:
            compression = compression.upper()
            if compression not in SUPPORTED_COMPRESSIONS:
                raise Exception("Unsupported compression method. Supported "
                                "compressions are: %s" 
                                % ", ".join(SUPPORTED_COMPRESSIONS))
            self.final_options["COMPRESS"] = compression
            
            if jpeg_quality is not None and compression == "JPEG":
                self.final_options["JPEG_QUALITY"] = jpeg_quality
            elif jpeg_quality is not None:
                raise ValueError("'jpeg_quality' can only be used with JPEG "
                                 "compression")
            
            if zlevel is not None and compression == "DEFLATE":
                self.final_options["ZLEVEL"] = zlevel
            elif zlevel is not None:
                raise ValueError("'zlevel' can only be used with DEFLATE "
                                 "compression")
            
            # TODO: "predictor" ?
        
        if tiling:
            self.final_options["TILED"] = "YES"
        
        if creation_options:
            # TODO: parse arglist
            self.final_options.update(dict(creation_options))
        
            
    @property
    def driver_name(self):
        return self._driver_name
    
    
    @property
    def extension(self):
        return ".tif"
    
    
    @property
    def creation_options(self):
        return ["%s=%s" % (key, value) 
                for key, value in self.final_options.items()]


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

    def __init__(self, srid):
        self.srid = srid

        
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
        dst_ds = _create_mem(tmp_ds.RasterXSize, tmp_ds.RasterYSize,
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
        _copy_metadata(src_ds, dst_ds)
        
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
        dst_ds = _create_mem(src_ds.RasterXSize, src_ds.RasterYSize, 
                             len(self.bands), self.datatype)
        limits = NUMERIC_LIMITS[self.datatype]
        
        for dst_index, (src_index, dmin, dmax) in enumerate(self.bands, 1):
            src_band = src_ds.GetRasterBand(src_index)
            src_min, src_max = src_band.ComputeRasterMinMax()
            
            # get min/max values or calculate from band
            if dmin is None:
                dmin = NUMERIC_LIMITS[src_band.DataType][0]
            elif dmin == "min":
                dmin = src_min
            if dmax is None:
                dmax = NUMERIC_LIMITS[src_band.DataType][1]
            elif dmax == "max":
                dmax = src_max
            
            data = src_band.ReadAsArray()
            
            # perform scaling
            # TODO: buggy?
            data = ((limits[1] - limits[0]) * ((data - dmin) / (dmax - dmin)))
            data = data.astype(gdal_array.codes[self.datatype])
            
            # write resulst
            dst_band = dst_ds.GetRasterBand(dst_index)
            dst_band.WriteArray(data)
        
        _copy_projection(src_ds, dst_ds)
        
        return dst_ds


class ColorIndexOptimization(DatasetOptimization):
    """ Dataset optimization step to replace the pixel color values with a color
        index. If no color palette is given (e.g: a VRT or any other dataset 
        containing a color table), this step takes the first three bands and 
        computes a median color table.
    """
    
    def __init__(self, palette_file=None):
        # TODO: sanitize inputs
        self.palette_file = palette_file
    
    
    def __call__(self, src_ds):
        dst_ds = _create_mem(src_ds.RasterXSize, src_ds.RasterYSize, 
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
        
        _copy_projection(src_ds, dst_ds)
        _copy_metadata(src_ds, dst_ds)
        
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

#===============================================================================
# Pre-Processors
#===============================================================================

class PreProcessor(object):
    """
    """
    
    force = False
    
    def __init__(self, format_selection, 
                 begin_time=None, end_time=None, coverage_id=None, 
                 overviews=True, crs=None, bands=None, bandmode=RGB,
                 color_index=False, palette_file=None, no_data_value=None, 
                 force=False):
        
        self.format_selection = format_selection
        self.begin_time = begin_time
        self.end_time = end_time
        self.coverage_id = coverage_id
        self.overviews = overviews
        
        self.crs = crs
        
        self.bands = bands
        self.bandmode = bandmode
        self.color_index = color_index
        self.palette_file = palette_file
        self.no_data_value = no_data_value
        
        self.force = force
        
    
    def process(self, input_filename, output_basename=None, 
                geo_reference=None, generate_metadata=True, 
                coverage_id=None, begin_time=None, end_time=None):
        
        # open the dataset and create an In-Memory Dataset as copy
        # to perform optimizations
        ds = _create_mem_copy(gdal.Open(input_filename))
        
        gt = ds.GetGeoTransform()
        
        if not geo_reference:
            if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0): # TODO: maybe use a better check
                raise ValueError("No geo reference supplied and the dataset "
                                 "has no internal geo transform.") # TODO: improve exception
        else:
            ds = geo_reference.apply(ds)
        
        # apply optimizations
        for optimization in self.optimizations:
            ds = optimization(ds)
        
        # TODO: make 'tif' dependant on format selection
        # check files exist
        if not output_basename:
            output_filename = splitext(input_filename)[0] + "_proc.tif"
            output_md_filename = splitext(input_filename)[0] + "_proc.xml"
        
        else:
            output_filename = output_basename + ".tif"
            output_md_filename = output_basename + ".xml"
        
        if not self.force:
            _check_file_existence(output_filename)
        
        # save the file to the disc
        driver = gdal.GetDriverByName(self.format_selection.driver_name)
        ds = driver.CreateCopy(output_filename, ds,
                               options=self.format_selection.creation_options)
        
        for optimization in self.post_optimizations:
            optimization(ds)
        
        # generate metadata if requested
        if generate_metadata:
            if not self.force:
                _check_file_existence(output_md_filename)
            
            # generate the footprint from the dataset
            polygon = self._generate_footprint(ds)
            
            # TODO: implement other options, e.g: generate footprint from
            # extent and reproject it.
            
            encoder = NativeMetadataFormatEncoder()
            xml = DOMElementToXML(encoder.encodeMetadata(coverage_id,
                                                         begin_time,
                                                         end_time, polygon))
            
            with open(output_md_filename, "w+") as f:
                f.write(xml)
        
        # close the dataset and write it to the disc
        ds = None
    
    
    def _generate_footprint(self, ds):
        """ Generate a fooptrint from a raster, using black/no-data as exclusion
        """
        
        # create an empty boolean array initialized as 'False' to store where
        # values exist as a mask array.
        nodata_map = numpy.zeros((ds.RasterYSize, ds.RasterXSize),
                               dtype=numpy.bool)
        
        for idx in range(1, ds.RasterCount + 1):
            band = ds.GetRasterBand(idx)
            raster_data = band.ReadAsArray()
            nodata = band.GetNoDataValue()
            
            if nodata is None:
                nodata = 0
            
            # apply the output to the map  
            nodata_map |= (raster_data != nodata)
        
        
        # create a temporary in-memory dataset and write the nodata mask 
        # into its single band
        tmp_ds = _create_mem(ds.RasterXSize, ds.RasterYSize, 1, 
                             gdalconst.GDT_Byte)
        tmp_band = tmp_ds.GetRasterBand(1)
        tmp_band.WriteArray(nodata_map.astype(numpy.uint8))
        
        
        # create an OGR in memory layer to hold the created polygon
        sr = osr.SpatialReference(); sr.ImportFromWkt(ds.GetProjectionRef())
        ogr_ds = ogr.GetDriverByName('Memory').CreateDataSource('out')
        layer = ogr_ds.CreateLayer('poly', sr, ogr.wkbPolygon)
        fd = ogr.FieldDefn('DN', ogr.OFTInteger)
        layer.CreateField(fd)
        
        # polygonize the mask band and store the result in the OGR layer
        gdal.Polygonize(tmp_band, tmp_band, layer, 0)
        
        if layer.GetFeatureCount() != 1:
            raise RuntimeError("Error during poligonization. Wrong number of "
                               "polygons.")
        
        # obtain geometry from the layer
        feature = layer.GetNextFeature()
        geometry = feature.GetGeometryRef()
        
        if geometry.GetGeometryType() != ogr.wkbPolygon:
            raise RuntimeError("Error during poligonization. Wrong geometry "
                               "type.")
        
        # simplify the polygon. the tolerance value is *really* vague
        polygon = GEOSGeometry(geometry.ExportToWkt()).simplify(1, True)
        
        # reproject each point from image coordinates to lat-lon
        # TODO: what if image is not in latlon? Need to reproject the coords to 4326
        gt = ds.GetGeoTransform()
        exterior = []
        for pixel_x, pixel_y in polygon.exterior_ring.tuple:
            exterior.append(gt[3] + abs(pixel_x) * gt[4] + abs(pixel_y) * gt[5])
            exterior.append(gt[0] + abs(pixel_x) * gt[1] + abs(pixel_y) * gt[2])
        
        return [exterior]


class WMSPreProcessor(PreProcessor):
    """
            
        >>> prep = WMSPreProcessor(...)
        >>> prep.process(input_filename, output_filename, generate_metadata)
    """

    @property
    def optimizations(self):
        if self.crs:
            yield ReprojectionOptimization(self.crs)
        
        
        if self.bandmode not in (RGB, RGBA, ORIG_BANDS):
            raise ValueError
        
        # if RGB is requested, use the given bands or the first 3 bands as RGB
        if self.bandmode == RGB:
            if self.bands and len(self.bands) != 3:
                raise ValueError("Wrong number of bands given. Expected 3, got "
                                 "%d." % len(self.bands))
            yield BandSelectionOptimization(self.bands or [(1, "min", "max"), 
                                                           (2, "min", "max"),
                                                           (3, "min", "max")])
        
        # if RGBA is requested, use the given bands or the first 4 bands as RGBA
        elif self.bandmode == RGBA:
            if self.bands and len(self.bands) != 4:
                raise ValueError("Wrong number of bands given. Expected 4, got "
                                 "%d." % len(self.bands))
            yield BandSelectionOptimization(self.bands or [(1, "min", "max"), 
                                                           (2, "min", "max"),
                                                           (3, "min", "max"),
                                                           (4, "min", "max")])
        
        # when band mode is set to original bands, don't use this optimization
        elif self.bandmode == ORIG_BANDS:
            if self.bands:
                raise ValueError("Bandmode is set to 'original', but bands are "
                                 "given.")
        
        else: raise ValueError("Illegal bandmode given.")
            
        if self.color_index:
            yield ColorIndexOptimization(self.palette_file)
            
        if self.no_data_value:
            yield NoDataValueOptimization(self.no_data_value)


    @property    
    def post_optimizations(self):
        if self.overviews:
            yield OverviewOptimization()
