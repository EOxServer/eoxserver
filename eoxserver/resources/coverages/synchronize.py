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
This module contains classes and functions for synchronizing the
database content with data stored in the file system.
"""

import os.path
from fnmatch import fnmatch
from datetime import datetime
from osgeo import ogr, osr

import logging
from traceback import format_exc

from eoxserver.core.system import System

from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.contrib.gis.geos import Point, Polygon, GEOSGeometry

from eoxserver.core.exceptions import InternalError, XMLDecoderException
from eoxserver.core.util.filetools import findFiles
#from eoxserver.resources.coverages.models import (
    #DatasetSeriesRecord, RectifiedDatasetRecord,
    #RectifiedStitchedMosaicRecord, FileRecord, RangeType, LineageRecord, EOMetadataRecord, 
    #DataDirRecord, MosaicDataDirRecord
#)
from eoxserver.resources.coverages.domainset import getGridFromFile
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory
#from eoxserver.resources.coverages.interfaces import RectifiedStitchedMosaicRecordInterface
from eoxserver.resources.coverages.exceptions import SynchronizationErrors
from eoxserver.processing.mosaic import RectifiedMosaicStitcher

class FileInfo(object):
    """
    This class gathers information about a coverage given in a file
    (more precisely: a GDAL dataset) and an accompanying metadata file.
    :class:`FileInfo` objects are used by :class:`Synchronizer` and 
    its descendants in order to record information to be ingested into
    the database.
    
    The constructor expects two mandatory arguments ``filename`` and
    ``range_type_name`` and an optional ``default_srid``. The
    ``range_type_name`` should refer to a range type known to the
    system; otherwise subsequent processing steps may fail. The
    ``default_srid`` is used to set the SRID in case it cannot be
    retrieved from the file.
    """
    @classmethod
    def fromFile(cls, filename, range_type_name, default_srid=None):
        """
        This class method reads in the file information from
        ``filename`` and returns a :class:`FileInfo` object. The
        ``range_type_name`` and ``default_srid`` arguments have the
        same meaning as for the constructor.
        """
        info = cls(filename, range_type_name, default_srid)
        info.read()
        return info
    
    def __init__(self, filename, range_type_name, default_srid=None):
        self.filename = filename
        self.range_type = range_type_name
        self.default_srid = default_srid
        
        self.srid = None
        self.size_x = None
        self.size_y = None
        self.extent = None
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
        """
        Call this method to actually retrieve information from the
        file.
        """
        ds = gdal.Open(str(self.filename))

        gt = ds.GetGeoTransform()
        
        srs = SpatialReference()
        srs.ImportFromWkt(ds.GetProjection())

        srs.AutoIdentifyEPSG()
        if srs.IsProjected():
            srid = srs.GetAuthorityCode("PROJCS")
        elif srs.IsGeographic():
            srid = srs.GetAuthorityCode("GEOGCS")
        else:
            srid = None
        
        if srid is None:
            self.srid = self.default_srid
        else:
            self.srid = srid
    
        self.size_x = ds.RasterXSize
        self.size_y = ds.RasterYSize
        
        xl = gt[0]
        yl = gt[3]
        xh = gt[0] + (ds.RasterXSize - 1) * gt[1]
        yh = gt[3] + (ds.RasterYSize - 1) * gt[5]
        
        self.extent = (
            min(xl, xh), min(yl, yh), max(xl, xh), max(yl, yh)
        )
        
        self.md_filename = self._getMetadataFileName()
        
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
    
    def astuple(self):
        """
        Returns the file information as a tuple of:
        
        * ``filename``: the path to the file,
        * ``srid``: the SRID of the file or ``"imageCRS"``,
        * ``size_x``: the pixel size of the file in x direction,
        * ``size_y``: the pixel size of the file in y direction,
        * ``extent``: a 4-tuple ``(minx, miny, maxx, maxy)`` of floating
          point coordinates in the CRS given by ``srid``; ``None`` for
          imageCRS
        * ``range_type_name``: the range type name,
        * ``md_filename``: path to the metadata file,
        * ``md_format``: name of the metadata format,
        * ``md_xml_text``: XML text representation of the metadata,
        * ``eo_id``: EO ID of the file as read from the metadata,
        * ``timestamp_begin``: timestamp of the acquisition time
          interval begin as read from the metadata,
        * ``timestamp_end``: timestamp of the acquisition time interval
          end as read from the metadata,
        * ``footprint_wkt``: WKT representation of the acquisition
          footprint as read from the metadata.
          
        Each of these properties is also available as attribute of the
        :class:`FileInfo` object.
        """
        return (
            self.filename,
            self.srid,
            self.size_x,
            self.size_y,
            self.extent, 
            self.range_type_name, 
            self.md_filename, 
            self.md_format,
            self.md_xml_text,
            self.eo_id, 
            self.timestamp_begin, 
            self.timestamp_end, 
            self.footprint_wkt
        )

class Synchronizer(object):
    DEFAULT_RANGE_TYPE_NAME = "RGB"
    DEFAULT_SRID = 3035
    
    def __init__(self):
        self.default_range_type_name = self.DEFAULT_RANGE_TYPE_NAME
        self.default_srid = self.DEFAULT_SRID
        
        self.factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        
        self.errors = []
        self.infos = []
    
    def setDefaults(self, default_range_type_name, default_srid):
        self.default_range_type_name = default_range_type_name
        self.default_srid = default_srid
    
    def _getRangeTypeName(self, filename):
        return self.default_range_type_name
        
    def _getDefaultSRID(self, filename):
        return self.default_srid
    
    def _getFileInfo(self, filename):
        return FileInfo.fromFile(
            filename,
            self._getRangeTypeName(filename),
            self._getDefaultSRID(filename)
        )
    
    def _getFilenameExpression(self, filename):
        return System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory", {
                "op_name": "attr",
                "operands": ("filename", "=", filename)
            }
        )

    def _createRectifiedDataset(self, file_info, container=None):
        logging.info(
            "Creating Dataset for file '%s' ..." % file_info.filename
        )

        rect_dataset_wrapper = self.factory.create(
            impl_id = "resources.coverages.wrappers.RectifiedDatasetWrapper",
            params = {
                "file_info": file_info,
                "container": container
            }
        )
        
        logging.info("Success.")
        self.infos.append(
            "RectifiedDataset has been created for file '%s'." % \
            file_info.filename
        )
    
    def _updateRectifiedDataset(self, coverage_id=None, file_info=None, add_container=None, rm_container=None):
        if coverage_id is None and file_info is None:
            raise InternalError(
                "One of 'coverage_id' or 'file_info' is required."
            )

        params = {}
        if file_info is not None:
            params.update({"file_info": file_info})
        if add_container is not None:
            params.update({"add_container": add_container})
        if rm_container is not None:
            params.update({"rm_container": rm_container})

        if coverage_id is None:
            logging.info(
                "Updating Rectified Dataset for file '%s' ..." % \
                file_info.filename
            )
            
            filename_expr = self._getFilenameExpression(
                file_info.filename
            )

            rect_dataset_wrapper = self.factory.update(
                impl_ids=["resources.coverages.wrappers.RectifiedDatasetWrapper"],
                filter_exprs=[filename_expr],
                params=params
            )[0]
            
            _coverage_id = rect_dataset_wrapper.getCoverageId()
        else:
            logging.info(
                "Updating Rectified Dataset '%s' ..." % coverage_id
            )
            
            self.factory.update(
                obj_id=coverage_id,
                params=params
            )
            
            _coverage_id = coverage_id
        
        logging.info("Success.")
        self.infos.append(
            "Rectified Dataset '%s' has been updated." % _coverage_id
        )

    def _deleteRectifiedDataset(self, coverage_id):
        logging.info(
            "Deleting Rectified Dataset '%s' ..." % coverage_id
        )
        
        self.factory.delete(obj_id=coverage_id)
        
        logging.info("Success.")
        self.infos.append(
            "Rectified Dataset '%s' has been deleted." % coverage_id
        )
    
    def _rectifiedDatasetExists(self, filename):
        filename_expr = self._getFilenameExpression(filename)

        return self.factory.exists(
            impl_ids=["resources.coverages.wrappers.RectifiedDatasetWrapper"],
            filter_exprs=[filename_expr]
        )

    def _logError(self, e):
        logging.error(str(e))
        logging.error(format_exc())

class RectifiedDatasetSynchronizer(Synchronizer):
    def create(self, filename):
        try:
            file_info = self._getFileInfo(filename)
            
            if self._rectifiedDatasetExists(filename):
                self._updateRectifiedDataset(file_info=file_info)
            else:
                self._createRectifiedDataset(file_info)
        except Exception, e:
            self._logError(e)
            raise
    
    def update(self, filename):
        try:
            file_info = self._getFileInfo(filename)
            
            if self._rectifiedDatasetExists(filename):
                self._updateRectifiedDataset(file_info=file_info)
            else:
                self._createRectifiedDataset(file_info)
        except Exception, e:
            self._logError(e)
            raise
            
    def delete(self, coverage_id):
        try:
            self._deleteRectifiedDatasetRecord(coverage_id)
        except Exception, e:
            self._logError(e)
            raise

class ContainerSynchronizer(Synchronizer):
    def __init__(self, container):
        super(ContainerSynchronizer, self).__init__()
        
        self.container = container
    
    def _findAllFiles(self):
        filenames = []
        
        for data_dir in self.container.getDataDirs():
            filenames.extend(
                findFiles(data_dir, self.container.getImagePattern())
            )
        
        return filenames

    def _updateOrCreateDatasets(self, fs_files, db_files):
        for filename in fs_files:
            try:
                if filename not in db_files:

                    if self._rectifiedDatasetExists(filename):

                        self._updateRectifiedDataset(
                            file_info=self._getFileInfo(filename),
                            add_container=self.container
                        )

                    else:
                        
                        self._createRectifiedDataset(
                            file_info=self._getFileInfo(filename),
                            container=self.container
                        )
                        
                else:
                    self._updateRectifiedDataset(
                        file_info=self._getFileInfo(filename)
                    )
            except Exception, e:
                self._logError(e)
                self.errors.append(str(e))
    
    def _deleteNotCompliant(self, all_files=None):
        if all_files is None:
            all_files = self._findAllFiles()
        
        expr_factory = System.getRegistry().bind(
            "resources.coverages.filters.CoverageExpressionFactory"
        )
        auto_expr = expr_factory.get(
            op_name = "attr",
            operands = ("automatic", "=", True)
        )
        file_expr = expr_factory.get(
            op_name = "attr",
            operands = ("filename", "!in", all_files)
        )
        
        self.factory.update(
            impl_ids = ["resources.coverages.wrappers.RectifiedDatasetWrapper"],
            filter_exprs = [auto_expr, file_expr],
            rm_container = self.container
        )
        
        orphan_expr = expr_factory.get(
            op_name = "orphaned"
        )
        invisible_expr = expr_factory.get(
            op_name = "attr",
            operands = ("visible", "=", False)
        )
        
        self.factory.delete(
            impl_ids = ["resources.coverages.wrappers.RectifiedDatasetWrapper"],
            filter_exprs = [auto_expr, invisible_expr, orphan_expr]
        )
    
    def _getFiles(self):
        expr_factory = System.getRegistry().bind(
            "resources.coverages.filters.CoverageExpressionFactory"
        )
        
        contained_expr = expr_factory.get(
            op_name = "contained_in",
            operands = (self.container,)
        )
        
        return self.factory.getAttrValues(
            attr_name = "filename",
            impl_ids = ["resources.coverages.wrappers.RectifiedDatasetWrapper"],
            filter_exprs = [contained_expr]
        )
    
    def _create(self):
        fs_files = self._findAllFiles()
        db_files = self._getFiles()
        
        for filename in fs_files:
            if filename not in db_files:
                try:
                    self._createRectifiedDataset(
                        file_info = self._getFileInfo(filename),
                        container = self.container
                    )
                except Exception, e:
                    self._logError(e)
                    self.errors.append(str(e))
                
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)
    
    def _update(self):
        fs_files = self._findAllFiles()
        db_files = self._getFiles()
        
        self._updateOrCreateDatasets(fs_files, db_files)
        
        self._deleteNotCompliant(fs_files)
        
        if len(self.errors):
            raise SynchronizationErrors(*self.errors)

class DatasetSeriesSynchronizer(ContainerSynchronizer):
    def __init__(self, container):
        super(DatasetSeriesSynchronizer, self).__init__(container)
        
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
                self.range_type_names[dir_name] = \
                    self.default_range_type_name
                return self.default_range_type_name
    
    def create(self):
        try:
            self._create()
        except Exception, e:
            self._logError(e)
            raise
    
    def update(self):
        try:
            self._update()
        except Exception, e:
            self._logError(e)
            raise
    
    def delete(self):
        try:
            self._deleteNotCompliant()
        except Exception, e:
            self._logError(e)
            raise

class RectifiedStitchedMosaicSynchronizer(ContainerSynchronizer):
    def __init__(self, container):
        super(RectifiedStitchedMosaicSynchronizer, self).__init__(
            container
        )
        
        self.stitcher = RectifiedMosaicStitcher(container)
        
    def _getRangeTypeName(self, filename):
        return self.container.getRangeType().name
    
    def _getDefaultSRID(self, filename):
        return self.container.getSRID()
            
    def create(self):
        try:
            self._create()
            
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
            
    def delete(self):
        try:
            self._deleteNotCompliant()
        
        except Exception, e:
            self._logError(e)
            raise
