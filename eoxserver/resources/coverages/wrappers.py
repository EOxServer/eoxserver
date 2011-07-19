#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
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

"""
This module provides implementations of coverage interfaces as 
defined in :mod:`eoxserver.resources.coverages.interfaces`. These
classes wrap the resources stored in the database and augment them
with additional application logic.
"""

import os.path

import logging

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.system import System
from eoxserver.core.resources import (
    ResourceFactoryInterface, ResourceWrapper, ResourceFactory
)
from eoxserver.core.exceptions import (
    InternalError, InvalidParameterException, UnknownCRSException
)
from eoxserver.core.util.filetools import findFiles
from eoxserver.core.util.timetools import getDateTime
from eoxserver.resources.coverages.models import (
    SingleFileCoverageRecord, RectifiedDatasetRecord,
    ReferenceableDatasetRecord, RectifiedStitchedMosaicRecord,
    DatasetSeriesRecord, FileRecord, EOMetadataRecord, 
    ExtentRecord, LineageRecord, RangeTypeRecord
)
from eoxserver.resources.coverages.interfaces import (
    CoverageInterface, RectifiedDatasetInterface,
    ReferenceableDatasetInterface, RectifiedStitchedMosaicInterface, 
    DatasetSeriesInterface
)
from eoxserver.resources.coverages.rangetype import (
    Band, NilValue, RangeType
)
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory

#-----------------------------------------------------------------------
# Wrapper implementations
#-----------------------------------------------------------------------

class CoverageWrapper(ResourceWrapper):
    """
    This is the base class for all coverage wrappers. It is a partial
    implementation of :class:`~.CoverageInterface`. It inherits from
    :class:`~.ResourceWrapper`.
    """
    
    #-------------------------------------------------------------------
    # CoverageInterface methods
    #-------------------------------------------------------------------
    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    def getCoverageId(self):
        """
        Returns the Coverage ID.
        """
        
        return self.__model.coverage_id
    
    def getCoverageSubtype(self):
        """
        This method shall return the coverage subtype as defined in
        the WCS 2.0 EO-AP. It must be overridden by concrete
        coverage wrappers. By default this method raises
        :exc:`~.InternalError`.
        
        See the definition of
        :meth:`~.CoverageInterface.getCoverageSubtype` in
        :class:`~.CoverageInterface` for possible return values.
        """
        
        raise InternalError("Not implemented.")

    def getType(self):
        """
        This method shall return the internal coverage type code. It
        must be overridden by concrete coverage wrappers. By default
        this method raises :exc:`~.InternalError`.
        
        See the definition of :meth:`~.CoverageInterface.getType` in
        :class:`~.CoverageInterface` for possible return values.
        """
        
        raise InternalError("Not implemented.")
        
    def getSize(self):
        """
        This method shall return a tuple ``(xsize, ysize)`` for the
        coverage wrapped by the implementation. It has to be overridden
        by concrete coverage wrappers. By default this method raises
        :exc:`~.InternalError`.
        """
        
        raise InternalError("Not implemented.")
    
    def getRangeType(self):
        """
        This method returns the range type of the coverage as 
        :class:`~.RangeType` object.
        """
        
        range_type = RangeType(
            name=self.__model.range_type.name,
            data_type=self.__model.range_type.data_type
        )
        
        for band_record in self.__model.range_type.bands.order_by("rangetype2band__no"):
            nil_values = [
                NilValue(value=nv.value, reason=nv.reason)\
                for nv in band_record.nil_values.all()
            ]
            
            range_type.addBand(Band(
                name=band_record.name,
                identifier=band_record.identifier,
                definition=band_record.definition,
                description=band_record.description,
                uom=band_record.uom,
                nil_values=nil_values,
                gdal_interpretation=band_record.gdal_interpretation
            ))
        
        return range_type
    
    def getLayerMetadata(self):
        """
        Returns a list of ``(metadata_key, metadata_value)`` pairs
        that represent MapServer metadata tags to be attached to
        MapServer layers.
        """
        
        return self.__model.layer_metadata.values_list("key", "value")

class RectifiedGridWrapper(object):
    """
    This wrapper is intended as a mix-in for coverages that rely on a
    rectified grid. It implements :class:`~.RectifiedGridInterface`.
    """    
    @property
    def __model(self):
        return self._ResourceWrapper__model
        
    def _createExtentRecord(self, file_info):
        return ExtentRecord.objects.create(
            srid = file_info.srid,
            size_x = file_info.size_x,
            size_y = file_info.size_y,
            minx = file_info.extent[0],
            miny = file_info.extent[1],
            maxx = file_info.extent[2],
            maxy = file_info.extent[3]
        )
    
    def _updateExtentRecord(self, file_info):
        self.__model.extent.srid = file_info.srid
        self.__model.extent.size_x = file_info.size_x
        self.__model.extent.size_y = file_info.size_y
        self.__model.extent.minx = file_info.extent[0]
        self.__model.extent.miny = file_info.extent[1]
        self.__model.extent.maxx = file_info.extent[2]
        self.__model.extent.maxy = file_info.extent[3]
    
    def getSRID(self):
        """
        Returns the SRID of the coverage CRS.
        """
        
        return self.__model.extent.srid
    
    def getExtent(self):
        """
        Returns the coverage extent as a 4-tuple of floating point
        coordinates ``(minx, miny, maxx, maxy)`` expressed in the
        coverage CRS as defined by the SRID returned by :meth:`getSRID`.
        """
        
        return (
            self.__model.extent.minx,
            self.__model.extent.miny,
            self.__model.extent.maxx,
            self.__model.extent.maxy
        )

class ReferenceableGridWrapper(object):
    """
    This wrapper is intended as a mix-in for coverages that rely on
    referenceable grids. It has yet to be implemented.
    
    .. note:: The design for referenceable grids is yet TBD.
    """
    
    pass

class DatasetWrapper(object):
    """
    This wrapper is intended as a mix-in for coverages that are stored
    as single files (to be correct: GDAL datasets) together with
    quicklooks and metadata files.
    """    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    def _createFileRecord(self, file_info):
        return FileRecord.objects.create(
            path = file_info.filename,
            metadata_path = file_info.md_filename,
            metadata_format = file_info.md_format
        )
    
    def _updateFileRecord(self, file_info):
        self.__model.file.path = file_info.filename
        self.__model.file.metadata_path = file_info.md_filename
        self.__model.file.metadata_format = file_info.md_format
    
    def getFilename(self):
        """
        Returns the file name that relates to the dataset.
        
        .. note:: A GDAL dataset can consist of more than one file. This
                  path points to the "main" data file.
        """
        return self.__model.file.path
        
    def getQuicklookPath(self):
        """
        Returns the path to a quicklook of the data, if defined.
        """
        return self.__model.file.quicklook_path
    
    def getMetadataPath(self):
        """
        Returns the path to the metadata file.
        """
        return self.__model.file.metadata_path
    
    def getMetadataFormat(self):
        """
        Returns the metadata format code as defined by the ...
        """
        # TODO: finish documentation
        
        return self.__model.file.metadata_format
        
class EOMetadataWrapper(object):
    """
    This wrapper class is intended as a mix-in for EO coverages and 
    dataset series as defined in the WCS 2.0 EO-AP.
    """    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    def _createEOMetadataRecord(self, file_info):
        return EOMetadataRecord.objects.create(
            timestamp_begin = file_info.timestamp_begin,
            timestamp_end = file_info.timestamp_end,
            footprint = GEOSGeometry(file_info.footprint_wkt),
            eo_gml = file_info.md_xml_text
        )
    
    def _updateEOMetadataRecord(self, file_info):
        self.__model.eo_metadata.timestamp_begin = \
            file_info.timestamp_begin
        self.__model.eo_metadata.timestamp_end = \
            file_info.timestamp_end
        self.__model.eo_metadata.footprint = \
            GEOSGeometry(file_info.footprint_wkt)
        self.__model.eo_metadata.eo_gml = file_info.md_xml_text
    
    def getEOID(self):
        """
        Returns the EO ID of the object.
        """
        
        return self.__model.eo_id

    def getBeginTime(self):
        """
        Returns the acquisition begin time as :class:`datetime.datetime`
        object.
        """
        
        return self.__model.eo_metadata.timestamp_begin
    
    def getEndTime(self):
        """
        Returns the acquisition end time as :class:`datetime.datetime`
        object.
        """
        
        return self.__model.eo_metadata.timestamp_end
    
    def getFootprint(self):
        """
        Returns the acquisition footprint as
        :class:`django.contrib.gis.geos.GEOSGeometry` object in
        the EPSG:4326 CRS.
        """
        
        return self.__model.eo_metadata.footprint
        
    def getWGS84Extent(self):
        """
        Returns the WGS 84 extent as 4-tuple of floating point
        coordinates ``(minlon, minlat, maxlon, maxlat)``.
        """
        
        return self.__model.eo_metadata.footprint.extent
    
    def getEOGML(self):
        """
        Returns the EO O&M XML text stored in the metadata.
        """
        
        return self.__model.eo_metadata.eo_gml

class EOCoverageWrapper(CoverageWrapper, EOMetadataWrapper):
    """
    This is a partial implementation of :class:`~.EOCoverageInterface`.
    It inherits from :class:`CoverageWrapper` and
    :class:`EOMetadataWrapper`.
    """
    
    def _createLineageRecord(self, file_info):
        return LineageRecord.objects.create()
    
    def _updateLineageRecord(self, file_info):
        pass
    
    def getEOCoverageSubtype(self):
        """
        This method shall return the EO Coverage subtype according to
        the WCS 2.0 EO-AP. It must be overridden by child
        implementations. By default :exc:`~.InternalError` is raised.
        """
        
        raise InternalError("Not implemented.")
    
    def getDatasets(self, filter_exprs=None):
        """
        This method shall return the datasets associated with this
        coverage, possibly filtered by the optional filter expressions.
        It must be overridden by child implementations. By default
        :exc:`~.InternalError` is raised.
        """
        
        raise InternalError("Not implemented.")
    
    def getLineage(self):
        """
        Returns ``None``.
        
        .. note:: The lineage element has yet to be specified in
                  detail in the WCS 2.0 EO-AP.
        """
        
        return None

class EODatasetWrapper(EOCoverageWrapper, DatasetWrapper):
    """
    This is the base class for EO Dataset wrapper implementations. It
    inherits from :class:`EOCoverageWrapper` and
    :class:`DatasetWrapper`.
    """
    
    def getDatasets(self, filter_exprs=None):
        """
        This method applies the given filter expressions to the
        model and returns a list containing the wrapper in case the
        filters are matched or an empty list otherwise.
        """
        
        if filter_exprs is not None:
            for filter_expr in filter_exprs:
                filter = System.getRegistry().findAndBind(
                    intf_id = "core.filters.Filter",
                    params = {
                        "core.filters.res_class_id": self.__class__.__get_impl_id__(),
                        "core.filters.expr_class_id": filter_expr.__class__.__get_impl_id__(),
                    }
                )
                
                if not filter.resourceMatches(filter_expr, self):
                    return []
        
        return [self]

class RectifiedDatasetWrapper(EODatasetWrapper, RectifiedGridWrapper):
    """
    This is the wrapper for Rectified Datasets. It inherits from
    :class:`EODatasetWrapper` and :class:`RectifiedGridWrapper`. It
    implements :class:`~.RectifiedDatasetInterface`.
    
    The following attributes are recognized:
    
    * ``eo_id``: the EO ID of the dataset; value must be a string
    * ``filename``: the path to the dataset; value must be a string
    * ``metadata_filename``: the path to the accompanying metadata
      file; value must be a string
    * ``srid``: the SRID of the dataset's CRS; value must be an integer
    * ``size_x``: the width of the coverage in pixels; value must be
      an integer
    * ``size_y``: the height of the coverage in pixels; value must be
      an integer
    * ``minx``: the left hand bound of the dataset's extent; value must
      be numeric
    * ``miny``: the lower bound of the dataset's extent; value must be
      numeric
    * ``maxx``: the right hand bound of the dataset's extent; value must
      be numeric
    * ``maxy``: the upper bound of the dataset's extent; value must be
      numeric
    * ``visible``: the ``visible`` attribute of the dataset; value must
      be boolean
    * ``automatic``: the ``automatic`` attribute of the dataset; value
      must be boolean
    """
    
    REGISTRY_CONF = {
        "name": "Rectified Dataset Wrapper",
        "impl_id": "resources.coverages.wrappers.RectifiedDatasetWrapper",
        "model_class": RectifiedDatasetRecord,
        "id_field": "coverage_id",
        "factory_ids": ("resources.coverages.wrappers.EOCoverageFactory",)
    }
    
    FIELDS = {
        "eo_id": "eo_id",
        "filename": "file__path",
        "metadata_filename": "file__metadata_path",
        "metadata_format": "file__metadata_format",
        "srid": "extent__srid",
        "size_x": "extent__size_x",
        "size_y": "extent__size_y",
        "minx": "extent__minx",
        "miny": "extent__miny",
        "maxx": "extent__maxx",
        "maxy": "extent__maxy",
        "visible": "visible",
        "automatic": "automatic"
    }
    
    #-------------------------------------------------------------------
    # ResourceInterface implementations
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented in ResourceWrapper
    
    def __get_model(self):
        return self._ResourceWrapper__model
    
    def __set_model(self, model):
        self._ResourceWrapper__model = model
        
    __model = property(__get_model, __set_model)
    
    def _createModel(self, params):
        if "file_info" in params:
            file_info = params["file_info"]
        else:
            raise InternalError(
                "Missing mandatory 'file_info' parameter."
            )
        
        container = params.get("container")
        
        if container is None:
            automatic = params.get("automatic", False)
            visible = params.get("visible", True)
        else:
            automatic = params.get("automatic", True)
            visible = params.get("visible", False)
            
        file_record = self._createFileRecord(file_info)

        eo_metadata_record = self._createEOMetadataRecord(file_info)
            
        extent_record = self._createExtentRecord(file_info)
        
        lineage_record = self._createLineageRecord(file_info)
        
        range_type_record = RangeTypeRecord.objects.get(
            name = file_info.range_type
        )
        
        dataset = RectifiedDatasetRecord.objects.create(
            file = file_record,
            coverage_id = file_info.eo_id,
            eo_id = file_info.eo_id,
            extent = extent_record,
            range_type = range_type_record,
            eo_metadata = eo_metadata_record,
            lineage = lineage_record,
            automatic = automatic,
            visible = visible
        )
        
        if container is not None:
            container.add(self.__model)
        
        self.__model = dataset
        
    def _updateModel(self, params):
        file_info = params.get("file_info")
        automatic = params.get("automatic")
        visible = params.get("visible")
        add_container = params.get("add_container")
        rm_container = params.get("rm_container")

        if file_info is not None:
            self._updateFileRecord(file_info)

            self._updateEOMetadataRecord(file_info)
                
            self._updateExtentRecord(file_info)
            
            self._updateLineageRecord(file_info)
            
            range_type_record = RangeTypeRecord.objects.get(
                name = file_info.range_type
            )
            
            dataset.coverage_id = file_info.eo_id,
            dataset.eo_id = file_info.eo_id,
            dataset.range_type = range_type_record,
        
        if automatic is not None:
            dataset.automatic = automatic
        
        if visible is not None:
            dataset.visible = visible
        
        if add_container is not None:
            add_container.addCoverage(self.__model.pk)
        
        if rm_container is not None:
            rm_container.removeCoverage(self.__model.pk)
    
    def _getAttrValue(self, attr_name):
        if attr_name == "eo_id":
            return self.__model.eo_id
        elif attr_name == "filename":
            return self.__model.file.path
        elif attr_name == "metadata_filename":
            return self.__model.file.metadata_path
        elif attr_name == "metadata_format":
            return self.__model.file.metadata_format
        elif attr_name == "srid":
            return self.__model.extent.srid
        elif attr_name == "size_x":
            return self.__model.extent.size_x
        elif attr_name == "size_y":
            return self.__model.extent.size_y
        elif attr_name == "minx":
            return self.__model.extent.minx
        elif attr_name == "miny":
            return self.__model.extent.miny
        elif attr_name == "maxx":
            return self.__model.extent.maxx
        elif attr_name == "maxy":
            return self.__model.extent.maxy
        elif attr_name == "visible":
            return self.__model.visible
        elif attr_name == "automatic":
            return self.__model.automatic
    
    def _setAttrValue(self, attr_name, value):
        if attr_name == "eo_id":
            self.__model.eo_id = value
        elif attr_name == "filename":
            self.__model.file.path = value
        elif attr_name == "metadata_filename":
            self.__model.file.metadata_path = value
        elif attr_name == "metadata_format":
            self.__model.file.metadata_format = value
        elif attr_name == "srid":
            self.__model.extent.srid = value
        elif attr_name == "size_x":
            self.__model.extent.size_x = value
        elif attr_name == "size_y":
            self.__model.extent.size_y = value
        elif attr_name == "minx":
            self.__model.extent.minx = value
        elif attr_name == "miny":
            self.__model.extent.miny = value
        elif attr_name == "maxx":
            self.__model.extent.maxx = value
        elif attr_name == "maxy":
            self.__model.extent.maxy = value
        elif attr_name == "visible":
            self.__model.visible = value
        elif attr_name == "automatic":
            self.__model.automatic = value
    
    #-------------------------------------------------------------------
    # CoverageInterface implementations
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented in CoverageWrapper
    
    def getCoverageSubtype(self):
        """
        Returns ``RectifiedGridCoverage``.
        """
        
        return "RectifiedGridCoverage"
    
    def getType(self):
        """
        Returns ``eo.rect_dataset``
        """
        
        return "eo.rect_dataset"
    
    def getSize(self):
        """
        Returns the pixel size of the dataset as 2-tuple of integers
        ``(size_x, size_y)``.
        """
        
        return (self.__model.extent.size_x, self.__model.extent.size_y)

    #-------------------------------------------------------------------
    #  EOCoverageInterface implementations
    #-------------------------------------------------------------------
    
    def getEOCoverageSubtype(self):
        """
        Returns ``RectifiedDataset``.
        """
        
        return "RectifiedDataset"
    
    def getContainers(self):
        """
        This method returns a list of :class:`DatasetSeriesWrapper` and
        :class:`RectifiedStitchedMosaicWrapper` objects containing this
        Rectified Dataset, or an empty list.
        """
        cov_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        
        dss_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contains", "operands": (self.__model.pk,)}
        )
        
        wrappers = []
        wrappers.extend(cov_factory.find(
            impl_ids=["resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"],
            filter_exprs=[self_expr]
        ))
        wrappers.extend(dss_factory.find(filter_exprs=[self_expr]))
        
        return wrappers
    
    def getContainerCount(self):
        """
        This method returns the number of Dataset Series and 
        Rectified Stitched Mosaics containing this Rectified Dataset.
        """
        return self.__model.dataset_series_set.count() + \
               self.__model.rect_stitched_mosaics.count()
        
    def contains(self, res_id):
        """
        Always returns ``False``. A Dataset does not contain other
        Datasets.
        """
        return False
    
    def containedIn(self, res_id):
        """
        Returns ``True`` if this Rectified Dataset is contained in the
        Rectified Stitched Mosaic or Dataset Series with the resource
        primary key ``res_id``, ``False`` otherwise.
        """
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0 or \
               self.__model.rect_stitched_mosaics.filter(pk=res_id).count() > 0
    
RectifiedDatasetWrapperImplementation = \
RectifiedDatasetInterface.implement(RectifiedDatasetWrapper)

class ReferenceableDatasetWrapper(EODatasetWrapper, ReferenceableGridWrapper):
    """
    This is the wrapper for Referenceable Datasets. It inherits from
    :class:`EODatasetWrapper` and :class:`ReferenceableGridWrapper`.
    
    The following attributes are recognized:
    
    * ``eo_id``: the EO ID of the dataset; value must be a string
    * ``filename``: the path to the dataset; value must be a string
    * ``metadata_filename``: the path to the accompanying metadata
      file; value must be a string
    * ``size_x``: the width of the coverage in pixels; value must be
      an integer
    * ``size_y``: the height of the coverage in pixels; value must be
      an integer
    * ``visible``: the ``visible`` attribute of the dataset; value must
      be boolean
    * ``automatic``: the ``automatic`` attribute of the dataset; value
      must be boolean
    
    .. note:: The design of Referenceable Datasets is still TBD.
    """
    
    REGISTRY_CONF = {
        "name": "Referenceable Dataset Wrapper",
        "impl_id": "resources.coverages.wrappers.ReferenceableDatasetWrapper",
        "model_class": ReferenceableDatasetRecord,
        "id_field": "coverage_id",
        "factory_ids": ("resources.coverages.wrappers.EOCoverageFactory",)
    }
    
    FIELDS = {
        "eo_id": "eo_id",
        "filename": "file__path",
        "metadata_filename": "file__metadata_path",
        "metadata_format": "file__metadata_format",
        "size_x": "size_x",
        "size_y": "size_y",
        "visible": "visible",
        "automatic": "automatic"
    }
    
    #-------------------------------------------------------------------
    # ResourceInterface implementations
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented in ResourceWrapper
    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    def _createModel(self, params):
        pass # TODO
    
    def _updateModel(self, params):
        pass # TODO
    
    def _getAttrValue(self, attr_name):
        if attr_name == "eo_id":
            return self.__model.eo_id
        elif attr_name == "filename":
            return self.__model.file.path
        elif attr_name == "metadata_filename":
            return self.__model.file.metadata_path
        elif attr_name == "metadata_format":
            return self.__model.file.metadata_format
        elif attr_name == "size_x":
            return self.__model.size_x
        elif attr_name == "size_y":
            return self.__model.size_y
        elif attr_name == "visible":
            return self.__model.visible
        elif attr_name == "automatic":
            return self.__model.automatic
    
    def _setAttrValue(self, attr_name, value):
        if attr_name == "eo_id":
            self.__model.eo_id = value
        elif attr_name == "filename":
            self.__model.file.path = value
        elif attr_name == "metadata_filename":
            self.__model.file.metadata_path = value
        elif attr_name == "metadata_format":
            self.__model.file.metadata_format = value
        elif attr_name == "size_x":
            self.__model.size_x = value
        elif attr_name == "size_y":
            self.__model.size_y = value
        elif attr_name == "visible":
            self.__model.visible = value
        elif attr_name == "automatic":
            self.__model.automatic = value
    
    #-------------------------------------------------------------------
    # CoverageInterface implementations
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented in CoverageWrapper
    
    def getCoverageSubtype(self):
        """
        Returns ``ReferenceableGridCoverage``.
        """
        
        return "ReferenceableGridCoverage"
    
    def getType(self):
        """
        Returns ``eo.ref_dataset``
        """
        
        return "eo.ref_dataset"
    
    def getSize(self):
        """
        Returns the pixel size of the dataset as 2-tuple of integers
        ``(size_x, size_y)``.
        """
        
        return (self.__model.size_x, self.__model.size_y)

    #-------------------------------------------------------------------
    #  EOCoverageInterface implementations
    #-------------------------------------------------------------------
    
    def getEOCoverageSubtype(self):
        """
        Returns ``ReferenceableDataset``.
        """
        
        return "ReferenceableDataset"

    def getContainers(self):
        """
        This method returns a list of :class:`DatasetSeriesWrapper`
        objects containing this Referenceable Dataset, or an empty list.
        """
        dss_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contains", "operands": (self.__model.pk,)}
        )
        
        return dss_factory.find(filter_exprs=[self_expr])
    
    def getContainerCount(self):
        """
        This method returns the number of Dataset Series containing 
        this Referenceable Dataset.
        """
        return self.__model.dataset_series_set.count()
        
    def contains(self, res_id):
        """
        Always returns ``False``. A Dataset cannot contain other
        Datasets.
        """
        return False
    
    def containedIn(self, res_id):
        """
        This method returns ``True`` if this Referenceable Dataset is
        contained in the Dataset Series with the given resource
        primary key ``res_id``, ``False`` otherwise.
        """
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0

ReferenceableDatasetWrapperImplementation = \
ReferenceableDatasetInterface.implement(ReferenceableDatasetWrapper)

class RectifiedStitchedMosaicWrapper(EOCoverageWrapper, RectifiedGridWrapper):
    """
    This is the wrapper for Rectified Stitched Mosaics. It inherits
    from :class:`EOCoverageWrapper` and :class:`RectifiedGridWrapper`.
    It implements :class:`~.RectifiedStitchedMosaicInterface`.
    
    The following attributes are recognized:
    
    * ``eo_id``: the EO ID of the mosaic; value must be a string
    * ``srid``: the SRID of the mosaic's CRS; value must be an integer
    * ``size_x``: the width of the coverage in pixels; value must be
      an integer
    * ``size_y``: the height of the coverage in pixels; value must be
      an integer
    * ``minx``: the left hand bound of the mosaic's extent; value must
      be numeric
    * ``miny``: the lower bound of the mosaic's extent; value must be
      numeric
    * ``maxx``: the right hand bound of the mosaic's extent; value must
      be numeric
    * ``maxy``: the upper bound of the mosaic's extent; value must be
      numeric
    """

    REGISTRY_CONF = {
        "name": "Rectified Stitched Mosaic Wrapper",
        "impl_id": "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
        "model_class": RectifiedStitchedMosaicRecord,
        "id_field": "coverage_id",
        "factory_ids": ("resources.coverages.wrappers.EOCoverageFactory",)
    }
    
    FIELDS = {
        "eo_id": "eo_id",
        "srid": "extent__srid",
        "size_x": "extent__size_x",
        "size_y": "extent__size_y",
        "minx": "extent__minx",
        "miny": "extent__miny",
        "maxx": "extent__maxx",
        "maxy": "extent__maxy",
    }

    #-------------------------------------------------------------------
    # ResourceInterface implementations
    #-------------------------------------------------------------------
    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    # NOTE: partially implemented in ResourceWrapper
    
    def _createModel(self, params):
        pass # TODO
    
    def _updateModel(self, params):
        pass # TODO
    
    def _getAttrValue(self, attr_name):
        if attr_name == "eo_id":
            return self.__model.eo_id
        elif attr_name == "srid":
            return self.__model.extent.srid
        elif attr_name == "size_x":
            return self.__model.extent.size_x
        elif attr_name == "size_y":
            return self.__model.extent.size_y
        elif attr_name == "minx":
            return self.__model.extent.minx
        elif attr_name == "miny":
            return self.__model.extent.miny
        elif attr_name == "maxx":
            return self.__model.extent.maxx
        elif attr_name == "maxy":
            return self.__model.extent.maxy
    
    def _setAttrValue(self, attr_name, value):
        if attr_name == "eo_id":
            self.__model.eo_id = value
        elif attr_name == "srid":
            self.__model.extent.srid = value
        elif attr_name == "size_x":
            self.__model.extent.size_x = value
        elif attr_name == "size_y":
            self.__model.extent.size_y = value
        elif attr_name == "minx":
            self.__model.extent.minx = value
        elif attr_name == "miny":
            self.__model.extent.miny = value
        elif attr_name == "maxx":
            self.__model.extent.maxx = value
        elif attr_name == "maxy":
            self.__model.extent.maxy = value
    
    #-------------------------------------------------------------------
    # CoverageInterface implementations
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented in CoverageWrapper
    
    def getCoverageSubtype(self):
        """
        Returns ``RectifiedGridCoverage``.
        """
        
        return "RectifiedGridCoverage"
    
    def getType(self):
        """
        Returns ``eo.rect_stitched_mosaic``
        """
        
        return "eo.rect_stitched_mosaic"
    
    def getSize(self):
        """
        Returns the pixel size of the mosaic as 2-tuple of integers
        ``(size_x, size_y)``.
        """
        
        return (self.__model.extent.size_x, self.__model.extent.size_y)

    #-------------------------------------------------------------------
    #  EOCoverageInterface implementations
    #-------------------------------------------------------------------
    
    def getEOCoverageSubtype(self):
        """
        Returns ``RectifiedStitchedMosaic``.
        """
        
        return "RectifiedStitchedMosaic"
    
    def getDatasets(self, filter_exprs=None):
        """
        Returns a list of :class:`RectifiedDatasetWrapper` objects
        contained in the stitched mosaic wrapped by the implementation.
        It accepts an optional ``filter_exprs`` parameter which is
        expected to be a list of filter expressions
        (see module :mod:`eoxserver.resources.coverages.filters`) or
        ``None``. Only the datasets matching the filters will be
        returned; in case no matching coverages are found an empty list
        will be returned.
        """
        
        if filter_exprs is None:
            _filter_exprs = []
        else:
            _filter_exprs = filter_exprs
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contained_in", "operands": (self.__model.pk,)}
        )
        _filter_exprs.append(self_expr)
                
        factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        
        return factory.find(
            impl_ids=["resources.coverages.wrappers.RectifiedDatasetWrapper"],
            filter_exprs=_filter_exprs
        )
        
    def getContainers(self):
        """
        This method returns a list of :class:`DatasetSeriesWrapper`
        objects containing this Stitched Mosaic or an empty list.
        """
        
        dss_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contains", "operands": (self.__model.pk,)}
        )
        
        return dss_factory.find(filter_exprs=[self_expr])
    
    def getContainerCount(self):
        """
        This method returns the number of Dataset Series containing
        this Stitched Mosaic.
        """
        return self.__model.dataset_series_set.count()
        
    def contains(self, res_id):
        """
        This method returns ``True`` if the a Rectified Dataset with
        resource primary key ``res_id`` is contained within this
        Stitched Mosaic, ``False`` otherwise.
        """
        return self.__model.rect_datasets.filter(pk=res_id).count() > 0
    
    def containedIn(self, res_id):
        """
        This method returns ``True`` if this Stitched Mosaic is 
        contained in the Dataset Series with resource primary key
        ``res_id``, ``False`` otherwise.
        """
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0
    
    #-------------------------------------------------------------------
    # RectifiedStitchedMosaicInterface methods
    #-------------------------------------------------------------------
    
    def getShapeFilePath(self):
        """
        Returns the path to the shape file.
        """
        return os.path.join(self.__model.storage_dir, "tindex.shp")
    
    def getDataDirs(self):
        """
        This method returns a list of directories which hold the 
        stitched mosaic data.
        """
        
        return list(
            self.__model.data_dirs.values_list('dir', flat=True)
        )
    
    def getImagePattern(self):
        """
        Returns the filename pattern for image files to be included 
        into the stitched mosaic. The pattern is expressed in the format
        accepted by :func:`fnmatch.fnmatch`.
        """
        
        return self.__model.image_pattern
        
RectifiedStitchedMosaicWrapperImplementation = \
RectifiedStitchedMosaicInterface.implement(RectifiedStitchedMosaicWrapper)

class DatasetSeriesWrapper(ResourceWrapper, EOMetadataWrapper):
    """
    This is the wrapper for Dataset Series. It inherits from
    :class:`EOMetadataWrapper`. It implements
    :class:`DatasetSeriesInterface`.
    """
    
    REGISTRY_CONF = {
        "name": "Dataset Series Wrapper",
        "impl_id": "resources.coverages.wrappers.DatasetSeriesWrapper",
        "model_class": DatasetSeriesRecord,
        "id_field": "eo_id",
        "factory_ids": ("resources.coverages.wrappers.DatasetSeriesFactory", )
    }
    
    FIELDS = {}
    
    #-------------------------------------------------------------------
    # ResourceInterface methods
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented by ResourceWrapper
    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    def _createModel(self, params):
        pass # TODO
        
    def _updateModel(self, params):
        pass # TODO
        
    def _getAttrValue(self, attr_name):
        pass # TODO
        
    def _setAttrValue(self, attr_name, value):
        pass # TODO
    
    #-------------------------------------------------------------------
    # DatasetSeriesInterface methods
    #-------------------------------------------------------------------
    
    def getEOCoverages(self, filter_exprs=None):
        """
        This method returns a list of EOCoverage wrappers (for datasets
        and stitched mosaics) associated with the dataset series wrapped
        by the implementation. It accepts an optional ``filter_exprs``
        parameter which is expected to be a list of filter expressions
        (see module :mod:`eoxserver.resources.coverages.filters`) or
        ``None``. Only the EOCoverages matching the filters will be
        returned; in case no matching coverages are found an empty list
        will be returned.
        """
        
        if filter_exprs is None:
            _filter_exprs = []
        else:
            _filter_exprs = filter_exprs
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contained_in", "operands": (self.__model.pk,)}
        )
        _filter_exprs.append(self_expr)
        
        factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        
        return factory.find(filter_exprs=_filter_exprs)
        
    def contains(self, res_id):
        """
        This method returns ``True`` if the Dataset Series contains
        the EO Coverage with resource primary key ``res_id``, ``False``
        otherwise.
        """
        return self.__model.rect_datasets.filter(pk=res_id).count() > 0 or \
               self.__model.ref_datasets.filter(pk=res_id).count() > 0 or \
               self.__model.rect_stitched_mosaics.filter(pk=res_id).count() > 0
    
    def getDataDirs(self):
        """
        This method returns a list of directories which hold the 
        dataset series data.
        """
        
        return list(
            self.__model.data_dirs.values_list('dir', flat=True)
        )
    
    def getImagePattern(self):
        """
        Returns the filename pattern for image files to be included 
        into the stitched mosaic. The pattern is expressed in the format
        accepted by :func:`fnmatch.fnmatch`.
        """
        
        return self.__model.image_pattern

DatasetSeriesWrapperImplementation = \
DatasetSeriesInterface.implement(DatasetSeriesWrapper)

#-----------------------------------------------------------------------
# Factories
#-----------------------------------------------------------------------

class EOCoverageFactory(ResourceFactory):
    REGISTRY_CONF = {
        "name": "EO Coverage Factory",
        "impl_id": "resources.coverages.wrappers.EOCoverageFactory"
    }

EOCoverageFactoryImplementation = \
ResourceFactoryInterface.implement(EOCoverageFactory)

class DatasetSeriesFactory(ResourceFactory):
    REGISTRY_CONF = {
        "name": "Dataset Series Factory",
        "impl_id": "resources.coverages.wrappers.DatasetSeriesFactory"
    }

DatasetSeriesFactoryImplementation = \
ResourceFactoryInterface.implement(DatasetSeriesFactory)
