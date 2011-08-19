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

from osgeo import gdal, ogr, osr
from calendar import timegm
from datetime import datetime
import math
import os, os.path
import numpy

import logging

from django.conf import settings
from django.contrib.gis.geos import Polygon

from eoxserver.resources.coverages.exceptions import SynchronizationErrors

class MosaicContribution(object):
    def __init__(self, dataset, contributing_footprint):
        self.dataset = dataset
        self.contributing_footprint = contributing_footprint
    
    def difference(self, other_footprint):
        self.contributing_footprint = self.contributing_footprint.difference(other_footprint)
    
    def isEmpty(self):
        return self.contributing_footprint.empty or self.contributing_footprint.num_geom == 0
    
    @classmethod
    def getContributions(cls, mosaic_int, poly=None):
        if poly is None:
            datasets = mosaic_int.getDatasets()
        else:
            poly.transform(4326)
            
            datasets = filter(
                lambda dataset: dataset.getFootprint().intersects(poly),
                mosaic_int.getDatasets()
            )
        
        datasets.sort(lambda a, b: timegm(a.getBeginTime().timetuple()) - timegm(b.getBeginTime().timetuple()))
        
        contributions = []
        
        for dataset in datasets:
            footprint = dataset.getFootprint()
            
            for contribution in contributions:
                contribution.difference(footprint)
            
            if poly is None:
                contributions.append(cls(dataset, footprint))
            else:
                contributions.append(cls(dataset, footprint.intersection(poly)))
        
        #logging.debug("Contributions")
        #for contribution in contributions:
            #logging.debug("Dataset: %s" % contribution.dataset.getCoverageId())
            #logging.debug("Contributing Footprint: %s" % contribution.contributing_footprint.wkt)
        
        return filter(
            lambda contribution: not contribution.isEmpty(),
            contributions
        )
        
class RectifiedMosaicStitcher(object):
    def __init__(self, mosaic_int):
        self.mosaic_int = mosaic_int
        
        self.srid = mosaic_int.getSRID()
        self.minx, self.miny, self.maxx, self.maxy = mosaic_int.getExtent()
        self.size_x, self.size_y = mosaic_int.getSize()
        self.xres = math.fabs((self.maxx - self.minx) / self.size_x)
        self.yres = math.fabs((self.maxy - self.miny) / self.size_y)
        
        self.band_count = 3 # TODO
        self.nodata = 0 # TODO
        
        self.target_dir = os.path.join(settings.PROJECT_DIR, "data", "mosaics", mosaic_int.getEOID())
        self.create_time = datetime.now()
    
    def _roundint(self, f):
        return int(numpy.int_(numpy.rint(f)))
    
    def _getTileExtent(self, x_index, y_index):
        minx = self.minx + float(x_index) * self.xres * 256.0
        maxx = min(minx + self.xres * 256.0, self.maxx)
        miny = self.miny + float(y_index) * self.yres * 256.0
        maxy = min(miny + self.yres * 256.0, self.maxy)
        
        return (minx, miny, maxx, maxy)
    
    def _getTileGeometry(self, x_index, y_index):
        return Polygon.from_bbox(self._getTileExtent(x_index, y_index))
    
    def _getContributingTiles(self, contributing_footprint):
        if contributing_footprint.empty:
            raise StopIteration
        else:
            #reproject footprint
            ref_area = contributing_footprint.transform(self.srid, True)
            
            minx, miny, maxx, maxy = ref_area.extent
            
            x_index_min = int(math.floor((minx - self.minx) / self.xres / 256.0))
            x_index_max = int(math.ceil((maxx - self.minx) / self.xres / 256.0))
            y_index_min = int(math.floor((miny - self.miny) / self.yres / 256.0))
            y_index_max = int(math.ceil((maxy - self.miny) / self.yres / 256.0))
            
            logging.debug("Mosaic Extent: %f, %f, %f, %f" % (self.minx, self.miny, self.maxx, self.maxy))
            logging.debug("Contr. Footprint Extent: %f, %f, %f, %f" % contributing_footprint.extent)
            logging.debug("Ref. Area Extent: %f, %f, %f, %f" % (minx, miny, maxx, maxy)) 
            logging.debug("Tile Index Extent: %d, %d, %d, %d" % (x_index_min, y_index_min, x_index_max, y_index_max))
            
            for x_index in range(x_index_min, x_index_max+1):
                for y_index in range(y_index_min, y_index_max+1):
                    if self._getTileGeometry(x_index, y_index).intersects(ref_area):
                        yield (x_index, y_index)

    def _getTilePath(self, id, x_index, y_index):
        dst_dir = os.path.join(
            self.target_dir,
            "tiles_%s" % self.create_time.strftime("%Y%m%dT%H%M%S"),
            "%03d" % (x_index // 1000),
            "%03d" % (y_index // 1000)
        )
        
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        
        dst_filename = "tile_%s_%06d_%06d.tiff" % (id, x_index, y_index)
        
        return os.path.join(dst_dir, dst_filename)

    def _makeTile(self, tile_coords, dataset):
        x_index, y_index = tile_coords
        
        tile_minx, tile_miny, tile_maxx, tile_maxy = self._getTileExtent(x_index, y_index)
        
        ds_minx, ds_miny, ds_maxx, ds_maxy = dataset.getExtent()
        
        minx = max(ds_minx, tile_minx)
        miny = max(ds_miny, tile_miny)
        maxx = min(ds_maxx, tile_maxx)
        maxy = min(ds_maxy, tile_maxy)
        
        x_offset = self._roundint((minx - ds_minx) / self.xres)
        y_offset = self._roundint((ds_maxy - maxy) / self.yres)
        x_size = self._roundint((maxx - minx) / self.xres)
        y_size = self._roundint((maxy - miny) / self.yres)
        
        logging.debug("_makeTile()")
        logging.debug("Tile Extent: %f, %f, %f, %f" % (tile_minx, tile_miny, tile_maxx, tile_maxy))
        logging.debug("Dataset Extent: %f, %f, %f, %f" % (ds_minx, ds_miny, ds_maxx, ds_maxy))
        logging.debug("Final Extent: %f, %f, %f, %f" % (minx, miny, maxx, maxy))
        logging.debug("Offsets: %d, %d; Size: %d, %d" % (x_offset, y_offset, x_size, y_size))
        
        src_path = str(dataset.getFilename())
        dst_path = str(self._getTilePath(dataset.getEOID(), x_index, y_index))

        src = gdal.Open(src_path)

        driver = gdal.GetDriverByName('GTiff')
        dst = driver.Create(dst_path, x_size, y_size, self.band_count)
        gt = [minx, self.xres, 0, maxy, 0, -self.yres]
        dst.SetGeoTransform(gt)
        dst.SetProjection(src.GetProjection())
        
        data = src.ReadRaster(x_offset, y_offset, x_size, y_size, x_size, y_size)
        dst.WriteRaster(0, 0, x_size, y_size, data, x_size, y_size)
        
        del src # close the datasets
        del dst
        
        return Tile(dst_path, x_index, y_index, minx, miny, maxx, maxy, x_size, y_size)

    def _mergeTiles(self, tiles):
        if len(tiles) == 1:
            return tiles[0]
        else:
            logging.debug("_mergeTiles")
            
            x_index = tiles[0].x_index
            y_index = tiles[0].y_index
            
            logging.debug("Index: (%d, %d)" % (x_index, y_index))
            
            minx = min([tile.minx for tile in tiles])
            miny = min([tile.miny for tile in tiles])
            maxx = max([tile.maxx for tile in tiles])
            maxy = max([tile.maxy for tile in tiles])
            
            x_size = self._roundint((maxx - minx) / self.xres)
            y_size = self._roundint((maxy - miny) / self.yres)
            
            dst_path = str(self._getTilePath("merged", x_index, y_index))
            
            driver = gdal.GetDriverByName('MEM')
            tmp = driver.Create(dst_path, x_size, y_size, self.band_count)

            
            # initialize arrays
            for band_no in range(1, self.band_count+1):
                band = tmp.GetRasterBand(band_no)
                band.SetNoDataValue(self.nodata)
            
            for tile in tiles:
                src = gdal.Open(tile.path)
                
                tile_x_offset = self._roundint((tile.minx - minx) / self.xres)
                tile_y_offset = self._roundint((maxy - tile.maxy) / self.yres)

                logging.debug("Offsets: %d, %d" % (tile_x_offset, tile_y_offset))
                logging.debug("Float Offsets: %f, %f" % ((tile.minx - minx) / self.xres, (maxy - tile.maxy) / self.yres))

                for band_no in range(1, self.band_count + 1):
                    src_band = src.GetRasterBand(band_no)
                    tmp_band = tmp.GetRasterBand(band_no)
                    
                    tile_data = src_band.ReadAsArray(0, 0, tile.x_size, tile.y_size)
                    merged_data = tmp_band.ReadAsArray(tile_x_offset, tile_y_offset, tile.x_size, tile.y_size)
                    
                    tile_nodata = numpy.equal(tile_data, self.nodata)
                    
                    to_write = numpy.choose(tile_nodata, (tile_data, merged_data))
                    
                    logging.debug("Shape: %s " % str(to_write.shape))
                    
                    tmp_band.WriteArray(to_write, tile_x_offset, tile_y_offset)
            
            driver = gdal.GetDriverByName('GTiff')
            dst = driver.CreateCopy(dst_path, tmp)
            gt = [minx, self.xres, 0, maxy, 0, -self.yres]
            dst.SetGeoTransform(gt)
            dst.SetProjection(src.GetProjection())

            return Tile(dst_path, x_index, y_index, minx, miny, maxx, maxy, x_size, y_size)
            
    def _createTileIndex(self, result_tiles):
        path = os.path.join(self.target_dir, "tindex_%s.shp" % self.create_time.strftime("%Y%m%dT%H%M%S"))
        
        tile_index = TileIndex(path, self.srid)
        
        tile_index.open()
        
        for tile_coords, tile in result_tiles.items():
            tile_index.addTile(tile)
        
        tile_index.close()
        
        return tile_index
        
    def _save(self, result_tiles, tile_index):
        self.mosaic_int.getModel().shape_file_path = tile_index.path
        self.mosaic_int.getModel().save()
    
    def _cleanup(self, tmp_tiles, result_tiles):
        driver = gdal.GetDriverByName('GTiff')
        
        for tile_coords, tiles in tmp_tiles.items():
            if len(tiles) > 1:
                for tile in tiles:
                    driver.Delete(tile.path)

    def generate(self):
        # determine contributing footprints
        contributions = MosaicContribution.getContributions(self.mosaic_int)
        
        # tile datasets
        dataset_tiles = {}
        
        for contribution in contributions:
            logging.debug("Processing Dataset '%s' ..." % contribution.dataset.getEOID())
            
            for tile_coords in self._getContributingTiles(contribution.contributing_footprint):
                if tile_coords in dataset_tiles:
                    dataset_tiles[tile_coords].append(self._makeTile(tile_coords, contribution.dataset))
                else:
                    dataset_tiles[tile_coords] = [self._makeTile(tile_coords, contribution.dataset)]
        
        # merge tiles
        result_tiles = {}
        
        for tile_coords, tiles in dataset_tiles.items():
            result_tiles[tile_coords] = self._mergeTiles(tiles)
        
        # create tileindex
        tile_index = self._createTileIndex(result_tiles)
        
        # save result tiles and tile index to their respective locations
        self._save(result_tiles, tile_index)
        
        # cleanup
        self._cleanup(dataset_tiles, result_tiles)
        
class Tile(object):
    def __init__(self, path, x_index, y_index, minx, miny, maxx, maxy, x_size, y_size):
        self.path = path
        self.x_index = x_index
        self.y_index = y_index
        
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        
        self.x_size = x_size
        self.y_size = y_size

class TileIndex(object):
    def __init__(self, path, srid):
        self.path = path
        
        self.srid = srid
        self.srs = osr.SpatialReference()
        self.srs.ImportFromEPSG(self.srid)
        
        self.shapefile = None
        self.layer = None
            
    def _createShapeFile(self):
        driver = ogr.GetDriverByName('ESRI Shapefile')
        if driver is None:
            raise SynchronizationError("Cannot start GDAL Shapefile driver")
        
        logging.info("Creating shapefile '%s' ...")
        
        self.shapefile = driver.CreateDataSource(str(self.path))
        if self.shapefile is None:
            raise SynchronizationError("Cannot create shapefile '%s'." % self.path)
        
        self.layer = self.shapefile.CreateLayer("file_locations", self.srs, ogr.wkbPolygon)
        if self.layer is None:
            raise SynchronizationError("Cannot create layer 'file_locations' in shapefile '%s' with SRS %s" %(self.path, str(self.srs)))
        
        location_defn = ogr.FieldDefn("location", ogr.OFTString)
        location_defn.SetWidth(256) # TODO: make this configurable
        if self.layer.CreateField(location_defn) != 0:
            raise SynchronizationError("Cannot create field 'location' on layer 'file_locations' in shapefile '%s'" % self.path)

        if self.layer.CreateField(ogr.FieldDefn("x_index", ogr.OFTInteger)) != 0:
            raise SynchronizationError("Cannot create field 'location' on layer 'file_locations' in shapefile '%s'" % self.path)

        if self.layer.CreateField(ogr.FieldDefn("y_index", ogr.OFTInteger)) != 0:
            raise SynchronizationError("Cannot create field 'location' on layer 'file_locations' in shapefile '%s'" % self.path)

        logging.info("Success.")
                
    def open(self):
        if not os.path.exists(self.path):
            self._createShapeFile()
        else:
            logging.info("Opening shapefile '%s' ...")
            
            self.shapefile = ogr.Open(self.path, True) # Open for updating
            if self.shapefile is None:
                raise SynchronizationError("Cannot open shapefile '%s'." % self.path)
                
            self.layer = self.shapefile.GetLayer(0)
            if self.layer is None:
                raise SynchronizationError("Shapefile '%s' has wrong format." % self.path)
            
            logging.info("Success")
    
    def close(self):
        self.layer.SyncToDisk()
        self.shapefile = None
    
    def addTile(self, tile):
        logging.info("Creating shapefile entry for tile (%06d, %06d) ..." % (tile.x_index, tile.y_index))
        
        feature = ogr.Feature(self.layer.GetLayerDefn())
        
        geom = ogr.CreateGeometryFromWkt("POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
            tile.minx, tile.miny,
            tile.maxx, tile.miny,
            tile.maxx, tile.maxy,
            tile.minx, tile.maxy,
            tile.minx, tile.miny
        ), self.srs)
        
        feature.SetGeometry(geom)
        feature.SetField("location", tile.path)
        feature.SetField("x_index", tile.x_index)
        feature.SetField("y_index", tile.y_index)
        if self.layer.CreateFeature(feature) != 0:
            raise SynchronizationError("Could not create shapefile entry for file '%s'" % self.path)
        
        feature = None
        
        logging.info("Success.")
    
