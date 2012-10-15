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

from os.path import splitext
import numpy

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal.geometries import OGRGeometry
from django.contrib.gis.gdal.srs import SpatialReference, CoordTransform

from eoxserver.core.util.xmltools import DOMElementToXML, XMLEncoder
from eoxserver.processing.preprocessing.util import (
    create_mem, create_mem_copy, check_file_existence, gdal, ogr, osr, gdalconst
)
from eoxserver.processing.preprocessing.optimization import (
    BandSelectionOptimization, ColorIndexOptimization, NoDataValueOptimization,
    OverviewOptimization, ReprojectionOptimization
)


class NativeMetadataFormatEncoder(XMLEncoder):
    """
    Encodes EO Coverage metadata 
    """
    
    def encodeMetadata(self, eoid, begin_time, end_time, polygon):
        return self._makeElement("", "Metadata", [
            ("", "EOID", eoid),
            ("", "BeginTime", begin_time),
            ("", "EndTime", end_time),
            ("", "Footprint", [
                ("", "Polygon", [
                    ("", "Exterior", self._posListToString(polygon[0]))
                ] + [
                    tuple("", "Interior", self._posListToString(interior)) 
                    for interior in polygon[1:]
                ])
            ])
        ])
    
    
    def _posListToString(self, ring):
        return " ".join(map(str, ring))

# enum for bandmode
RGB, RGBA, ORIG_BANDS = range(3)

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
        ds = create_mem_copy(gdal.Open(input_filename))
        
        gt = ds.GetGeoTransform()
        footprint_wkt = None
        
        if not geo_reference:
            if gt == (0.0, 1.0, 0.0, 0.0, 0.0, 1.0): # TODO: maybe use a better check
                raise ValueError("No geospatial reference for unreferenced "
                                 "dataset given.")
        else:
            ds, footprint_wkt = geo_reference.apply(ds)
        
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
            check_file_existence(output_filename)
        
        # save the file to the disc
        driver = gdal.GetDriverByName(self.format_selection.driver_name)
        ds = driver.CreateCopy(output_filename, ds,
                               options=self.format_selection.creation_options)
        
        for optimization in self.post_optimizations:
            optimization(ds)
        
        # generate metadata if requested
        if generate_metadata:
            if not self.force:
                check_file_existence(output_md_filename)
            
            if not footprint_wkt:
                # generate the footprint from the dataset
                polygon = self._generate_footprint(ds)
            
            else:
                # use the provided footprint
                geom = OGRGeometry(footprint_wkt)
                exterior = []
                for x, y in geom.exterior_ring.tuple:
                    exterior.append(y); exterior.append(x)
                
                polygon = [exterior]
            
            
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
        tmp_ds = create_mem(ds.RasterXSize, ds.RasterYSize, 1, 
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
        
        # simplify the polygon. the tolerance value is *really* vague using
        # the GeoDjango geometry here, as it allows to preserve the topology
        polygon = OGRGeometry(GEOSGeometry(geometry.ExportToWkt()).simplify(1, True).wkt)
        
        # reproject each point from image coordinates to lat-lon
        gt = ds.GetGeoTransform()
        exterior = []
        
        # check if reprojection to latlon is necessary
        reproject = not sr.IsGeographic()
        if reproject: 
            ct = CoordTransform(SpatialReference(ds.GetProjectionRef()),
                                SpatialReference(4326))
        
        for x, y in polygon.exterior_ring:
            point = OGRGeometry("POINT (%f %f)"%
                                (gt[0] + abs(x) * gt[1] + abs(y) * gt[2],
                                 gt[3] + abs(x) * gt[4] + abs(y) * gt[5]))
            
            if reproject:
                point.transform(ct)
            
            exterior.append(point.y)
            exterior.append(point.x)
        
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
