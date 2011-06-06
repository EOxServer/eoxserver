#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

import os.path
from fnmatch import fnmatch
from datetime import datetime
from osgeo import ogr, osr

import logging
from traceback import format_exc

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.contrib.gis.geos import Point, Polygon, GEOSGeometry

from eoxserver.core.exceptions import InternalError, XMLDecoderException
from eoxserver.core.util.filetools import findFiles
from eoxserver.resources.coverages.models import (
    RectifiedDatasetSeriesRecord, RectifiedDatasetRecord,
    RectifiedStitchedMosaicRecord, FileRecord, RectifiedGridRecord, 
    AxisRecord, RangeType, LineageRecord, EOMetadataRecord, 
    DataDirRecord, MosaicDataDirRecord
)
from eoxserver.resources.coverages.domainset import getGridFromFile
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory
from eoxserver.resources.coverages.interfaces import RectifiedStitchedMosaicRecordInterface
from eoxserver.resources.coverages.exceptions import SynchronizationErrors
from eoxserver.processing.mosaic import RectifiedMosaicStitcher

class FileInfo(object):
    @classmethod
    def fromFile(cls, filename, range_type, default_srid=None):
        info = cls(filename, range_type, default_srid)
        info.read()
        return info
    
    def __init__(self, filename, range_type, default_srid=None):
        super(FileInfo, self).__init__()
        
        self.filename = filename
        self.range_type = range_type
        self.default_srid = default_srid
        
        self.grid = None
        self.md_filename = None
        self.md_format = None
        self.eo_id = None
        self.timestamp_begin = None
        self.timestamp_end = None
        self.footprint_wkt = None
    
    def _getMetadataFileName(self):
        dir_name = os.path.dirname(self.filename)
        base_name = os.path.splitext(os.path.basename(self.filename))[0]

        md_filename = os.path.join(dir_name, "%s.xml" % base_name) # TODO: assume XML file in the same directory as image file with extension .xml
        
        return md_filename
    
    def _transformToWGS84(self, geom):
        geom.transform("+init=EPSG:4326")
        return geom
        
    def read(self):
        self.grid = getGridFromFile(str(self.filename))
        if self.grid.srid is None:
            self.grid.srid = self.default_srid
        
        self.md_filename = self._getMetadataFileName()
        #self.md_format = #"native" # TODO: assume metadata is always in native format
        
        try:
            md_int = MetadataInterfaceFactory.getMetadataInterfaceForFile(self.md_filename)
        except Exception, e:
            raise SynchronizationErrors(str(e))
        
        try:
            self.eo_id = md_int.getEOID()
            self.timestamp_begin = md_int.getBeginTime()
            self.timestamp_end = md_int.getEndTime()
            self.footprint_wkt = md_int.getFootprint()
            self.md_format = md_int.getMetadataFormat()
            self.md_xml_text = ""
            if self.md_format == "eogml":
                self.md_xml_text = md_int.getXMLText()
                
        except XMLDecoderException, e:
            raise SynchronizationErrors("Metadata XML Error: %s" % str(e))

        # TODO: provisional begin
        #minx, miny, maxx, maxy = self.grid.getExtent2D()
        #ll = self._transformToWGS84(Point(minx, miny, srid=self.grid.srid))
        #lr = self._transformToWGS84(Point(maxx, miny, srid=self.grid.srid))
        #ur = self._transformToWGS84(Point(maxx, maxy, srid=self.grid.srid))
        #ul = self._transformToWGS84(Point(minx, maxy, srid=self.grid.srid))
        #self.footprint_wkt = "POLYGON((%f %f, %f %f, %f %f, %f %f, %f %f))" % (
            #ll.x, ll.y,
            #lr.x, lr.y,
            #ur.x, ur.y,
            #ul.x, ul.y,
            #ll.x, ll.y
        #)
        # TODO: provisional end
    
    def astuple(self):
        return (
            self.grid, 
            self.range_type, 
            self.md_filename, 
            self.md_format,
            self.md_xml_text,
            self.eo_id, 
            self.timestamp_begin, 
            self.timestamp_end, 
            self.footprint_wkt
        )

class RectifiedCompositeObjectSynchronizer(object):
    def __init__(self, wcseo_object):
        super(RectifiedCompositeObjectSynchronizer, self).__init__()
        self.wcseo_object = wcseo_object
        self.errors = []
        self.infos = []
        
    def _getRangeTypeName(self, filename):
        return "RGB" # TODO
    
    def _getRangeType(self, filename):
        return RangeType.objects.get(name=self._getRangeTypeName(filename))
    
    def _getDefaultSRID(self, filename):
        return 3035 # TODO

    def _findFiles(self, data_dir):
        try:
            filenames = findFiles(data_dir, self.wcseo_object.image_pattern)
        except OSError: # TODO
            return []

        return filenames
        
    def _findAllFiles(self):
        filenames = []
        
        for data_dir in self.wcseo_object.data_dirs.all():
            filenames.extend(self._findFiles(data_dir.dir))
        
        return filenames

    def _getFileInfo(self, filename):
        return FileInfo.fromFile(filename, self._getRangeType(filename), self._getDefaultSRID(filename))
        
    def _createRecord(self, filename, file_info):
        logging.info("Creating Dataset for file '%s' ..." % filename)

        grid, range_type, md_filename, md_format, md_xml_text, eo_id, timestamp_begin, timestamp_end, footprint_wkt = file_info.astuple()
        
        file_record = FileRecord.objects.create(
            path = filename,
            metadata_path = md_filename,
            metadata_format = md_format
        )
        eo_metadata = EOMetadataRecord.objects.create(
            timestamp_begin = timestamp_begin,
            timestamp_end = timestamp_end,
            footprint = GEOSGeometry(footprint_wkt),
            eo_gml = md_xml_text
        )
        grid_record = RectifiedGridRecord.objects.create(
            srid = grid.srid
        )
        axis_1 = AxisRecord.objects.create(
            grid = grid_record,
            label = grid.axis_labels[0],
            dimension_idx = 1,
            low = grid.low[0],
            high = grid.high[0],
            origin_component = grid.origin[0],
            offset_vector_component = grid.offsets[0][0]
        )
        axis_2 = AxisRecord.objects.create(
            grid = grid_record,
            label = grid.axis_labels[1],
            dimension_idx = 2,
            low = grid.low[1],
            high = grid.high[1],
            origin_component = grid.origin[1],
            offset_vector_component = grid.offsets[1][1]
        )
        lineage = LineageRecord.objects.create()
        dataset = RectifiedDatasetRecord.objects.create(
            file = file_record,
            coverage_id = eo_id,
            eo_id = eo_id,
            grid = grid_record,
            range_type = range_type,
            eo_metadata = eo_metadata,
            lineage = lineage,
            automatic = True,
            visible = False
        )
        self.wcseo_object.rect_datasets.add(dataset)
        logging.info("Success.")
        self.infos.append("RectifiedDataset has been created for file %s"%filename)

    def _updateRecord(self, dataset, filename):
        # TODO
        logging.info("Updating Dataset for file '%s' ..." % filename)
        logging.info("Success.")

    def _deleteRecord(self, dataset):
        logging.info("Deleting Dataset for file '%s' ..." % dataset.file.path)

        file_record = dataset.file
        grid_record = dataset.grid
        
        dataset.delete()
        if file_record.rect_datasets.count() == 0 and file_record.single_file_coverages.count() == 0:
            file_record.delete()
        if grid_record.rect_datasets.count() == 0 and grid_record.rect_stitched_mosaics.count() == 0 and grid_record.single_file_coverages.count() == 0:
            grid_record.delete()

        logging.info("Success.")
        self.infos.append("RectifiedDataset with ID %s has been deleted."%dataset.eo_id)

    def _createDataset(self, filename):
        file_info = self._getFileInfo(filename)
        self._createRecord(filename, file_info)
    
    def _updateDataset(self, dataset, filename):
        self._updateRecord(dataset, filename)
        
    def _deleteDataset(self, dataset, filename):
        self._deleteRecord(dataset)

    def _updateOrCreateDatasets(self, fs_files, db_files):
        for filename in fs_files:
            if filename not in db_files:
                try:
                    dataset = RectifiedDatasetRecord.objects.get(file__path=filename)
                    self.wcseo_object.rect_datasets.add(dataset)
                    self.errors.append("RectifiedDataset with ID %s cannot be removed from the container."%dataset.eo_id)
                except RectifiedDatasetRecord.DoesNotExist:
                    self._createDataset(filename)
            else:
                self._updateDataset(self.wcseo_object.rect_datasets.get(file__path=filename), filename)
    
    def _deleteNotCompliant(self, all_files=None):
        if all_files is None:
            all_files = self._findAllFiles()
        
        datasets = self.wcseo_object.rect_datasets.filter(automatic=True).exclude(file__path__in=all_files)
        for dataset in datasets:
            self._deleteDataset(dataset, dataset.file.path)
    
    def _createDir(self, data_dir):
        fs_files = self._findFiles(data_dir)
        db_files = [dataset.file.path for dataset in self.wcseo_object.rect_datasets.all()]
        
        for filename in fs_files and filename not in db_files:
            self._createDataset(filename)
            
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)
    
    def _create(self):
        fs_files = self._findAllFiles()
        #db_files = [dataset.file.path for dataset in self.wcseo_object.rect_datasets.all()]
        db_files = self.wcseo_object.rect_datasets.all().values_list('file__path', flat=True)
        
        for filename in fs_files:
            if filename not in db_files:
                self._createDataset(filename)
                
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)
            
    def _updateDir(self, data_dir):
        fs_files = self._findFiles(data_dir)
        db_files = self.wcseo_object.rect_datasets.filter(file__path__startswith=data_dir).values_list('file__path', flat=True)
        
        self._updateOrCreateDatasets(fs_files, db_files)
        
        self._deleteNotCompliant()
        
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)
    
    def _update(self):
        fs_files = self._findAllFiles()
        db_files = self.wcseo_object.rect_datasets.all().values_list('file__path', flat=True)
        
        self._updateOrCreateDatasets(fs_files, db_files)
        
        self._deleteNotCompliant(fs_files)
        
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)
    
    def _logError(self, e):
        logging.error(str(e))
        logging.error(format_exc())

class RectifiedDatasetSeriesSynchronizer(RectifiedCompositeObjectSynchronizer):
    def __init__(self, wcseo_object):
        super(RectifiedDatasetSeriesSynchronizer, self).__init__(wcseo_object)
        
        self.range_type_names = {}
    
    def _getRangeTypeName(self, filename):
        dir_name = os.path.dirname(filename)
        
        if dir_name in self.range_type_names:
            return self.range_type_names[dir_name]
        else:
            rt_path = os.path.join(dir_name, "rangetype.txt")
            if os.path.exists(rt_path):
                rt_file = open(rt_path)
                range_type_name = rt_file.read().strip()
                rt_file.close()
            
                self.range_type_names[dir_name] = range_type_name
                return range_type_name
            else:
                self.range_type_names[dir_name] = "RGB" # TODO: make this configurable (default_range_type)
                return "RGB"
    
    def createDir(self, data_dir):
        try:
            self._createDir(data_dir)
        except Exception, e:
            self._logError(e)
            raise
    
    def create(self):
        try:
            self._create()
        except Exception, e:
            self._logError(e)
            raise
    
    def updateDir(self, data_dir):
        try:
            self._updateDir(data_dir)
        except Exception, e:
            self._logError(e)
            raise
    
    def update(self):
        try:
            self._update()
        except Exception, e:
            self._logError(e)
            raise
    
    def deleteDir(self, data_dir):
        try:
            self._deleteNotCompliant()
        except Exception, e:
            self._logError(e)
            raise

class RectifiedStitchedMosaicSynchronizer(RectifiedCompositeObjectSynchronizer):
    def __init__(self, wcseo_object):
        super(RectifiedStitchedMosaicSynchronizer, self).__init__(wcseo_object)
        
        mosaic_int = RectifiedStitchedMosaicRecordInterface(wcseo_object)
        self.grid = mosaic_int.getGrid()
        
        self.stitcher = RectifiedMosaicStitcher(mosaic_int)
        
    def _getRangeTypeName(self, filename):
        return self.wcseo_object.range_type.name
    
    def _getRangeType(self, filename):
        return self.wcseo_object.range_type
    
    def _getDefaultSRID(self, filename):
        return self.wcseo_object.grid.srid
        
    def _createDataset(self, filename):
        file_info = self._getFileInfo(filename)
        
        if file_info.grid.isSubGrid(self.grid):
            self._createRecord(filename, file_info)
        else:
            raise SynchronizationErrors("Dataset '%s': Grid does not match mosaic grid." % file_info.eo_id)
    
    def createDir(self, data_dir):
        try:
            self._createDir(data_dir)
            
            if not len(self.wcseo_object.rect_datasets.all()):
                raise SynchronizationErrors("The RectifiedStitchedMosaic must contain RectifiedDatasets")
            
            self.stitcher.generate()
        except Exception, e:
            self._logError(e)
            raise
    
    def create(self):
        try:
            self._create()
            
            if not len(self.wcseo_object.rect_datasets.all()):
                raise SynchronizationErrors("The RectifiedStitchedMosaic must contain RectifiedDatasets")
            
            self.stitcher.generate()
        except Exception, e:
            self._logError(e)
            raise
    
    def updateDir(self, data_dir):
        try:
            self._updateDir(data_dir)
            
            if not len(self.wcseo_object.rect_datasets.all()):
                raise SynchronizationErrors("The RectifiedStitchedMosaic must contain RectifiedDatasets")
            
            self.stitcher.generate()
        except Exception, e:
            self._logError(e)
            raise

    def update(self):
        try:
            self._update()
            
            if not len(self.wcseo_object.rect_datasets.all()):
                raise SynchronizationErrors("The RectifiedStitchedMosaic must contain RectifiedDatasets")
            
            self.stitcher.generate()
        except Exception, e:
            self._logError(e)
            raise
    
    def deleteDir(self, data_dir):
        try:
            self._deleteNotCompliant()
            
            if not len(self.wcseo_object.rect_datasets.all()):
                raise SynchronizationErrors("The RectifiedStitchedMosaic must contain RectifiedDatasets")

            self.stitcher.generate()
        except Exception, e:
            self._logError(e)
            raise
