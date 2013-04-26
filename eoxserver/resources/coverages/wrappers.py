#-----------------------------------------------------------------------
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
#-----------------------------------------------------------------------

"""
This module provides implementations of coverage interfaces as 
defined in :mod:`eoxserver.resources.coverages.interfaces`. These
classes wrap the resources stored in the database and augment them
with additional application logic.
"""

import os.path
import operator
import logging

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.geometry import MultiPolygon, Polygon
from django.contrib.gis.db.models import Union

from eoxserver.core.system import System
from eoxserver.core.resources import (
    ResourceFactoryInterface, ResourceWrapper, ResourceFactory
)
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.models import (
    PlainCoverageRecord, RectifiedDatasetRecord,
    ReferenceableDatasetRecord, RectifiedStitchedMosaicRecord,
    DatasetSeriesRecord, EOMetadataRecord, 
    ExtentRecord, LineageRecord, RangeTypeRecord,
    LayerMetadataRecord
)
from eoxserver.resources.coverages.interfaces import (
    CoverageInterface, RectifiedDatasetInterface,
    ReferenceableDatasetInterface, RectifiedStitchedMosaicInterface, 
    DatasetSeriesInterface
)
from eoxserver.resources.coverages.rangetype import (
    Band, NilValue, RangeType
)


logger = logging.getLogger(__name__)

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


    def isAutomatic(self): 
        """
        Returns ``True`` if the coverage is automatic or ``False`` otherwise. 
        """
        
        return self.__model.automatic

    
    def getCoverageId(self):
        """
        Returns the Coverage ID.
        """
        
        return self.__model.coverage_id
    
    def getCoverageSubtype(self):
        """
        This method shall return the coverage subtype as defined in
        the WCS 2.0 EO-AP (EO-WCS). It must be overridden by concrete
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
    
    def getDataStructureType(self):
        """
        Returns the data structure type of the coverage. To be implemented
        by subclasses, raises :exc:`~.InternalError` by default.
        """
        raise InternalError("Not implemented.")
        
    def getData(self):
        """
        Returns the a :class:`~.CoverageDataWrapper` object that wraps the
        coverage data, raises :exc:`~.InternalError` by default.
        """
        raise InternalError("Not implemented.")
    
    def getLayerMetadata(self):
        """
        Returns a list of ``(metadata_key, metadata_value)`` pairs
        that represent MapServer metadata tags to be attached to
        MapServer layers.
        """
        
        return self.__model.layer_metadata.values_list("key", "value")
    
    def matches(self, filter_exprs):
        """
        Returns True if the Coverage matches the given filter
        expressions and False otherwise.
        """
        
        for filter_expr in filter_exprs:
            filter = System.getRegistry().findAndBind(
                intf_id = "core.filters.Filter",
                params = {
                    "core.filters.res_class_id": self.__class__.__get_impl_id__(),
                    "core.filters.expr_class_id": filter_expr.__class__.__get_impl_id__(),
                }
            )
            
            if not filter.resourceMatches(filter_expr, self):
                return False
    
        return True
    
    def _get_create_dict(self, params):
        create_dict = super(CoverageWrapper, self)._get_create_dict(params)
        
        if "coverage_id" not in params:
            raise InternalError(
                "Missing mandatory 'coverage_id' parameter for RectifiedDataset creation."
            )
        
        if "range_type_name" not in params:
            raise InternalError(
                "Missing mandatory 'range_type_name' parameter for RectifiedDataset creation."
            )
        
        create_dict["coverage_id"] = params["coverage_id"]
        
        try:
            create_dict["range_type"] = RangeTypeRecord.objects.get(
                name=params["range_type_name"]
            )
        except RangeTypeRecord.DoesNotExist:
            raise InternalError(
                "Unknown range type name '%s'" % params["range_type_name"]
            )
            
        if "data_source" in params and params["data_source"] is not None:
            create_dict["automatic"] = params.get("automatic", True)
            create_dict["data_source"] = params["data_source"].getRecord()
        else:
            create_dict["automatic"] = False
            create_dict["data_source"] = None
        
        layer_metadata = params.get("layer_metadata")

        if layer_metadata:
            create_dict["layer_metadata"] = []
            
            for key, value in layer_metadata.items():
                create_dict["layer_metadata"].append(
                    LayerMetadataRecord.objects.get_or_create(
                        key=key, value=value
                    )[0]
                )
                
        return create_dict
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(CoverageWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
        
        coverage_id = set_kwargs.get("coverage_id")
        range_type_name = set_kwargs.get("range_type_name")
        layer_metadata = set_kwargs.get("layer_metadata", {})
        automatic = set_kwargs.get("automatic")
        data_source = set_kwargs.get("data_source")
        
        if coverage_id is not None:
            self.__model.coverage_id = coverage_id
        
        if range_type_name is not None:
            self.__model.range_type = RangeTypeRecord.objects.get(
                name=range_type_name
            )
            
        for key, value in layer_metadata:
            pass # TODO implement setting
        
        if automatic is not None:
            self.__model.automatic = automatic
        
        if data_source:
            pass # TODO
        
class CommonGridWrapper(object): 
    """
    Common base class shared by :class:`~.RectifiedGridWrapper`
    and :class:`~.ReferenceableGridWrapper`
   """

    @property
    def __model(self):
        return self._ResourceWrapper__model

    def _get_create_dict(self, params):
        create_dict = super(CommonGridWrapper, self)._get_create_dict(params)
        
        if "geo_metadata" not in params:
            raise InternalError(
                "Missing mandatory 'coverage_id' parameter for dataset creation."
            )
        
        geo_metadata = params["geo_metadata"]
        
        create_dict["extent"] = ExtentRecord.objects.create(
            srid = geo_metadata.srid,
            size_x = geo_metadata.size_x,
            size_y = geo_metadata.size_y,
            minx = geo_metadata.extent[0],
            miny = geo_metadata.extent[1],
            maxx = geo_metadata.extent[2],
            maxy = geo_metadata.extent[3]
        )
        
        return create_dict

    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(CommonGridWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
        
        geo_md = set_kwargs.get("geo_metadata")
        if geo_md:
            extent = self.__model.extent
            extent.srid = geo_md.srid
            extent.size_x = geo_md.size_x
            extent.size_y = geo_md.size_y
            extent.minx = geo_md.extent[0]
            extent.miny = geo_md.extent[1]
            extent.maxx = geo_md.extent[2]
            extent.maxy = geo_md.extent[3]
            
            extent.save()

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

class RectifiedGridWrapper(CommonGridWrapper):
    """
    This wrapper is intended as a mix-in for coverages that rely on a
    rectified grid. It implements :class:`~.RectifiedGridInterface`.
    """    

    def getResolution(self):
        """
        Returns the coverage resolution as a 2-tuple of float values for the 
        x and y axes ``(resx, resy)`` expressed in the unit of measure of the
        coverage CRS as defined by the SRID returned by :meth:`getSRID`.
        """
        extent = self.getExtent()
        size = self.getSize()
        return (
            (extent[2] - extent[0]) / float(size[0]),
            (extent[3] - extent[1]) / float(size[1])
        )

class ReferenceableGridWrapper(CommonGridWrapper):
    """
    This wrapper is intended as a mix-in for coverages that rely on
    referenceable grids. It implements :class:`~.ReferenceableGridInterface`.
    """
    pass 
    

class PackagedDataWrapper(object):
    """
    This wrapper is intended as a mix-in for coverages that are stored as
    data packages.
    """    
    @property
    def __model(self):
        return self._ResourceWrapper__model
    
    # TODO: replace by appropriate data package implementation
    
    #def _createFileRecord(self, file_info):
        #return FileRecord.objects.create(
            #path = file_info.filename,
            #metadata_path = file_info.md_filename,
            #metadata_format = file_info.md_format
        #)
    
    #def _updateFileRecord(self, file_info):
        #self.__model.file.path = file_info.filename
        #self.__model.file.metadata_path = file_info.md_filename
        #self.__model.file.metadata_format = file_info.md_format
    
    def getDataStructureType(self):
        """
        Returns the data structure type of the underlying data package
        """
        # TODO: this implementation is inefficient as the data package wrapper
        # is discarded and cannot be reused, thus forcing a second database hit
        # when accessing the actual data
        return self.getData().getDataStructureType()
    
    def getData(self):
        """
        Return the data package wrapper associated with the coverage, i.e. an
        instance of a subclass of :class:`~.DataPackageWrapper`.
        """
        return System.getRegistry().getFromFactory(
            factory_id = "resources.coverages.data.DataPackageFactory",
            params = {
                "record": self.__model.data_package
            }
        )

class TiledDataWrapper(object):
    """
    This wrapper is intended as a mix-in for coverages that are stored in tile
    indices.
    """
    @property
    def __model(self):
        return self._ResourceWrapper__model
        
    def getDataStructureType(self):
        """
        Returns ``"index"``.
        """
        # this is a shortcut; it has to be overridden if any time different
        # data structure types for tiled data should be implemented
        return "index"
    
    def getData(self):
        """
        Returns a :class:`TileIndexWrapper` instance.
        """
        return System.getRegistry().getFromFactory(
            factory_id = "resources.coverages.data.TileIndexFactory",
            params = {
                "record": self.__model.tile_index
            }
        )

class EOMetadataWrapper(object):
    """
    This wrapper class is intended as a mix-in for EO coverages and 
    dataset series as defined in the WCS 2.0 EO-AP (EO-WCS).
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
    
    def _get_create_dict(self, params):
        create_dict = super(EOMetadataWrapper, self)._get_create_dict(params)
        
        if "eo_metadata" not in params:
            raise InternalError(
                "Missing mandatory 'eo_metadata' parameter for RectifiedDataset creation."
            )
        
        eo_metadata = params["eo_metadata"]
        
        create_dict["eo_id"] = eo_metadata.getEOID()
        
        md_format = eo_metadata.getMetadataFormat()
        if md_format and md_format.getName() == "eogml":
            eo_gml = eo_metadata.getRawMetadata()
        else:
            eo_gml = ""
        
        footprint = eo_metadata.getFootprint()
        if type(footprint) != MultiPolygon:
            footprint = MultiPolygon(footprint)
        
        create_dict["eo_metadata"] = EOMetadataRecord.objects.create(
            timestamp_begin = eo_metadata.getBeginTime(),
            timestamp_end = eo_metadata.getEndTime(),
            footprint = footprint,
            eo_gml = eo_gml
        )
        
        return create_dict
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(EOMetadataWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
        
        eo_id = set_kwargs.get("eo_id")
        eo_md = set_kwargs.get("eo_metadata")
        if eo_md:
            footprint = eo_md.getFootprint()
            if type(footprint) != MultiPolygon:
                footprint = MultiPolygon(footprint)
            
            record = self.__model.eo_metadata
            record.timestamp_begin = eo_md.getBeginTime()
            record.timestamp_end = eo_md.getEndTime()
            record.footprint = footprint
            
            md_format = eo_md.getMetadataFormat()
            if md_format and md_format.getName() == "eogml":
                record.eo_gml = eo_md.getRawMetadata()
            else:
                record.eo_gml = ""
            
            self.__model.eo_id = eo_md.getEOID()
            
            self.__model.eo_metadata = record
            self.__model.eo_metadata.save()
        
        if eo_id is not None:
            self.__model.eo_id = eo_id
        
    
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

class EOCoverageWrapper(EOMetadataWrapper, CoverageWrapper):
    """
    This is a partial implementation of :class:`~.EOCoverageInterface`.
    It inherits from :class:`CoverageWrapper` and
    :class:`EOMetadataWrapper`.
    """
    
    def _get_create_dict(self, params):
        create_dict = super(EOCoverageWrapper, self)._get_create_dict(params)
        
        create_dict["lineage"] = LineageRecord.objects.create()
        
        return create_dict
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(EOCoverageWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
    
        containers = link_kwargs.get("containers", [])
        if "container" in link_kwargs:
            containers.append(link_kwargs["container"])
        
        for container in containers:
            container.addCoverage(self)
        
        containers = unlink_kwargs.get("containers", [])
        if "container" in unlink_kwargs:
            containers.append(unlink_kwargs["container"])
        
        for container in containers:
            container.removeCoverage(self)
        
        # TODO lineage update?
    
    
    def getEOCoverageSubtype(self):
        """
        This method shall return the EO Coverage subtype according to
        the WCS 2.0 EO-AP (EO-WCS). It must be overridden by child
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
                  detail in the WCS 2.0 EO-AP (EO-WCS).
        """
        
        return None

class EODatasetWrapper(PackagedDataWrapper, EOCoverageWrapper):
    """
    This is the base class for EO Dataset wrapper implementations. It
    inherits from :class:`EOCoverageWrapper` and
    :class:`PackagedDataWrapper`.
    """
    
    def _get_create_dict(self, params):
        create_dict = super(EODatasetWrapper, self)._get_create_dict(params)
        
        if "data_package" not in params:
            raise InternalError(
                "Missing mandatory 'data_package' parameter for RectifiedDataset creation."
            )
        
        create_dict["data_package"] = params["data_package"].getRecord()
        
        if "container" in params:
            create_dict["visible"] = params.get("visible", False)
        else:
            create_dict["visible"] = params.get("visible", True)
        
        return create_dict
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(EODatasetWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)
        
        visible = set_kwargs.get("visible")
        if visible is not None:
            self.__model.visible = visible
        
        data_package = set_kwargs.get("data_package")
        if data_package:
            # TODO implement
            pass
    
    def getDatasets(self, filter_exprs=None):
        """
        This method applies the given filter expressions to the
        model and returns a list containing the wrapper in case the
        filters are matched or an empty list otherwise.
        """
        
        if filter_exprs is not None:
            if not self.matches(filter_exprs):
                return []
        
        return [self]

class RectifiedDatasetWrapper(RectifiedGridWrapper, EODatasetWrapper):
    """
    This is the wrapper for Rectified Datasets. It inherits from
    :class:`EODatasetWrapper` and :class:`RectifiedGridWrapper`. It
    implements :class:`~.RectifiedDatasetInterface`.
    
    .. attribute:: FIELDS
      
        * ``eo_id``: the EO ID of the dataset; value must be a string
        * ``begin_time``: the begin time of the eo metadata entry
        * ``end_time``: the end time of the eo metadata entry
        * ``footprint``: the footprint of the dataset
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
        * ``visible``: the visibility of the coverage (for DescribeCoverage
          requests); boolean
        * ``automatic``: if the dataset was automatically created or by hand;
          boolean
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
        "data_package": "data_package",
        "srid": "extent__srid",
        "size_x": "extent__size_x",
        "size_y": "extent__size_y",
        "minx": "extent__minx",
        "miny": "extent__miny",
        "maxx": "extent__maxx",
        "maxy": "extent__maxy",
        "visible": "visible",
        "automatic": "automatic",
        "begin_time": "eo_metadata__timestamp_begin",
        "end_time": "eo_metadata__timestamp_end",
        "footprint": "eo_metadata__footprint"
    
        # TODO layer metadata?
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

    # _get_create_dict inherited from superclasses and mix-ins

    def _create_model(self, create_dict):
        self.__model = RectifiedDatasetRecord.objects.create(**create_dict)
        
    def _post_create(self, params):
        if "container" in params and params["container"]:
            params["container"].addCoverage(self)
        containers = params.get("containers", [])
        for container in containers:
            container.addCoverage(self)
    
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
        
    def contains(self, wrapper):
        """
        Always returns ``False``. A Dataset does not contain other
        Datasets.
        """
        return False
    
    def containedIn(self, wrapper):
        """
        Returns ``True`` if this Rectified Dataset is contained in the
        Rectified Stitched Mosaic or Dataset Series specified by its
        ``wrapper``, ``False`` otherwise.
        """
        res_id = wrapper.getModel().pk
        
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0 or \
               self.__model.rect_stitched_mosaics.filter(pk=res_id).count() > 0
    
RectifiedDatasetWrapperImplementation = \
RectifiedDatasetInterface.implement(RectifiedDatasetWrapper)

class ReferenceableDatasetWrapper(ReferenceableGridWrapper, EODatasetWrapper):
    """
    This is the wrapper for Referenceable Datasets. It inherits from
    :class:`EODatasetWrapper` and :class:`ReferenceableGridWrapper`.
    
    .. attribute:: FIELDS
    
        * ``eo_id``: the EO ID of the dataset; value must be a string
        * ``begin_time``: the begin time of the eo metadata entry
        * ``end_time``: the end time of the eo metadata entry
        * ``footprint``: the footprint of the dataset
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
        "data_package": "data_package",
        "srid": "extent__srid",
        "size_x": "extent__size_x",
        "size_y": "extent__size_y",
        "minx": "extent__minx",
        "miny": "extent__miny",
        "maxx": "extent__maxx",
        "maxy": "extent__maxy",
        "visible": "visible",
        "automatic": "automatic",
        "begin_time": "eo_metadata__timestamp_begin",
        "end_time": "eo_metadata__timestamp_end",
        "footprint": "eo_metadata__footprint"
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
    
    def _create_model(self, create_dict):
        self.__model = ReferenceableDatasetRecord.objects.create(**create_dict)
        
    def _post_create(self, params):
        if "container" in params and params["container"]:
            params["container"].addCoverage(self)
        containers = params.get("containers", [])
        for container in containers:
            container.addCoverage(self)
    
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
        
        return (self.__model.extent.size_x, self.__model.extent.size_y)

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
        
    def contains(self, wrapper):
        """
        Always returns ``False``. A Dataset cannot contain other
        Datasets.
        """
        return False
    
    def containedIn(self, wrapper):
        """
        This method returns ``True`` if this Referenceable Dataset is
        contained in the Dataset Series specified by its ``wrapper``,
        ``False`` otherwise.
        """
        res_id = wrapper.getModel().pk
        
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0

ReferenceableDatasetWrapperImplementation = \
ReferenceableDatasetInterface.implement(ReferenceableDatasetWrapper)

class RectifiedStitchedMosaicWrapper(TiledDataWrapper, RectifiedGridWrapper, EOCoverageWrapper):
    """
    This is the wrapper for Rectified Stitched Mosaics. It inherits
    from :class:`EOCoverageWrapper` and :class:`RectifiedGridWrapper`.
    It implements :class:`~.RectifiedStitchedMosaicInterface`.
    
    .. attribute:: FIELDS
      
        * ``eo_id``: the EO ID of the mosaic; value must be a string
        * ``begin_time``: the begin time of the eo metadata entry
        * ``end_time``: the end time of the eo metadata entry
        * ``footprint``: the footprint of the mosaic
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
        "begin_time": "eo_metadata__timestamp_begin",
        "end_time": "eo_metadata__timestamp_end",
        "footprint": "eo_metadata__footprint"
    }

    #-------------------------------------------------------------------
    # ResourceInterface implementations
    #-------------------------------------------------------------------
    
    def __get_model(self):
        return self._ResourceWrapper__model
    
    def __set_model(self, model):
        self._ResourceWrapper__model = model
        
    __model = property(__get_model, __set_model)
    
    def __init__(self):
        super(RectifiedStitchedMosaicWrapper, self).__init__()
        
        self.__block_md_update = False
    
    # NOTE: partially implemented in ResourceWrapper
    
    def _get_create_dict(self, params):
        create_dict = super(RectifiedStitchedMosaicWrapper, self)._get_create_dict(params)
        
        if "tile_index" not in params:
            raise InternalError(
                "Missing mandatory 'tile_index' parameter for RectifiedStitchedMosaic creation."
            )
        
        create_dict["tile_index"] = params["tile_index"].getRecord()
        
        return create_dict
    
    def _create_model(self, create_dict):
        self.__model = RectifiedStitchedMosaicRecord.objects.create(
            **create_dict
        )
        
    def _post_create(self, params):
        container = params.get("container")
        if container is not None:
            container.addCoverage(self)
        
        containers = params.get("containers", [])
        for container in containers:
            container.addCoverage(self)
        
        for coverage in params.get("coverages", []):
            self.addCoverage(coverage)
            
        if "data_sources" in params:
            for data_source in params["data_sources"]:
                self.__model.data_sources.add(data_source.getRecord())
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(RectifiedStitchedMosaicWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)

        try:
            self.__block_md_update = True
            
            data_sources = link_kwargs.get("data_sources", [])
            coverages = link_kwargs.get("coverages", [])
            for data_source in data_sources:
                self.__model.data_sources.add(data_source.getRecord())
            for coverage in coverages:
                self.addCoverage(coverage)
            
            data_sources = unlink_kwargs.get("data_sources", [])
            coverages = unlink_kwargs.get("coverages", [])
            for data_source in data_sources:
                self.__model.data_sources.remove(data_source.getRecord())
            for coverage in coverages:
                self.removeCoverage(coverage)
                
            self._updateMetadata()
        finally:
            self.__block_md_update = False

        # TODO: tile_index

    def _updateMetadata(self):
        qs = self.__model.rect_datasets.all()
        
        if len(qs):
            eo_metadata_set = EOMetadataRecord.objects.filter(
                rectifieddatasetrecord_set__in = qs
            )
            
            try:
                begin_time = min(eo_metadata_set.values_list('timestamp_begin', flat=True))
                end_time = max(eo_metadata_set.values_list('timestamp_end', flat=True))
            # Work around for issue in Django 1.5
            except TypeError:
                begin_time = min([t.timestamp_begin for t in eo_metadata_set])
                end_time = max([t.timestamp_end for t in eo_metadata_set])
            
            footprint = eo_metadata_set.aggregate(
                Union('footprint')
            )["footprint__union"]
            
            if footprint.geom_type.upper() != "MULTIPOLYGON":
                footprint = MultiPolygon(footprint)

            self.__model.eo_metadata.timestamp_begin = begin_time
            self.__model.eo_metadata.timestamp_end = end_time
            self.__model.eo_metadata.footprint = footprint
            
            self.__model.eo_metadata.save()
    
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

        _filter_exprs = []
        
        if filter_exprs is not None:
            _filter_exprs.extend(filter_exprs)
        
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
        
    def contains(self, wrapper):
        """
        This method returns ``True`` if the a Rectified Dataset specified
        by its ``wrapper`` is contained within this Stitched Mosaic, 
        ``False`` otherwise.
        """
        res_id = wrapper.getModel().pk
        
        return self.__model.rect_datasets.filter(pk=res_id).count() > 0
    
    def containedIn(self, wrapper):
        """
        This method returns ``True`` if this Stitched Mosaic is 
        contained in the Dataset Series specified by its ``wrapper``, 
        ``False`` otherwise.
        """
        res_id = wrapper.getModel().pk
        
        return self.__model.dataset_series_set.filter(pk=res_id).count() > 0
    
    #-------------------------------------------------------------------
    # RectifiedStitchedMosaicInterface methods
    #-------------------------------------------------------------------
    
    def getShapeFilePath(self):
        """
        Returns the path to the shape file.
        """
        return os.path.join(self.__model.storage_dir, "tindex.shp")
    
    def addCoverage(self, wrapper):
        """
        Adds a Rectified Dataset specified by its wrapper. An 
        :exc:`InternalError` is raised if the wrapper type is not equal to
        ``eo.rect_dataset`` or if the grids of the dataset is not compatible to
        the grid of the Rectified Stitched Mosaic.
        """
        res_type = wrapper.getType()
        res_id = wrapper.getModel().pk
        
        if res_type != "eo.rect_dataset":
            raise InternalError(
                "Cannot add coverages of type '%s' to Rectified Stitched Mosaics" %\
                res_type
            )
        
        # check if SRIDs are equal
        if self.getSRID() != wrapper.getSRID():
            raise InternalError(
                "Cannot add coverage: SRID mismatch (%d != %s)" % (
                    self.getSRID(), wrapper.getSRID()
                )
            )
        
        EPSILON = 1e-10
        
        cov_extent = wrapper.getExtent()
        this_extent = self.getExtent()
        
        cov_offsets = wrapper.getResolution()
        this_offsets = self.getResolution()
        
        # check if offset vectors are the same
        if (abs(this_offsets[0] - cov_offsets[0]) > EPSILON
            or abs(this_offsets[1] - cov_offsets[1]) > EPSILON):
            raise InternalError(
                "Cannot add coverage: offset vector mismatch (%s != %s)" % (
                    this_offsets, cov_offsets
                )
            )
        
        # check if grids are the same
        diff_origins = tuple(map(operator.sub, this_extent[:2], cov_extent[:2]))
        v = tuple(map(operator.div, diff_origins, cov_offsets))
        if (abs(v[0] - round(v[0])) > EPSILON
            or abs(v[1] - round(v[1])) > EPSILON):
            raise InternalError("Cannot add coverage: grid mismatch.")
        
        # check if range types are the same
        if self.getRangeType() != wrapper.getRangeType():
            raise InternalError(
                "Cannot add coverage: range type mismatch (%s, %s)." % (
                    self.getRangeType().name, wrapper.getRangeType().name
                )
            )
        
        self.__model.rect_datasets.add(res_id)
        
        if not self.__block_md_update:
            self._updateMetadata()
    
    def removeCoverage(self, wrapper):
        """
        Removes a Rectified Dataset specified by its wrapper. An 
        :exc:`InternalError` is raised if the wrapper type is not equal to
        ``eo.rect_dataset``.
        """
        res_type = wrapper.getType()
        res_id = wrapper.getModel().pk
        
        if res_type != "eo.rect_dataset":
            raise InternalError(
                "Cannot remove coverages of type '%s' from Rectified Stitched Mosaics" %\
                res_type
            )
        else:
            self.__model.rect_datasets.remove(res_id)
        
        if not self.__block_md_update:
            self._updateMetadata()
    
    def getDataDirs(self):
        """
        This method returns a list of directories which hold the 
        stitched mosaic data.
        """
        
        return list(
            self.__model.data_dirs.values_list('dir', flat=True)
        )

    def getDataSources(self):
        data_source_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
        return [data_source_factory.get(record=record) 
                for record in self.__model.data_sources.all()]
        
    
    def getImagePattern(self):
        """
        Returns the filename pattern for image files to be included 
        into the stitched mosaic. The pattern is expressed in the format
        accepted by :func:`fnmatch.fnmatch`.
        """
        
        return self.__model.image_pattern
        
RectifiedStitchedMosaicWrapperImplementation = \
RectifiedStitchedMosaicInterface.implement(RectifiedStitchedMosaicWrapper)

class DatasetSeriesWrapper(EOMetadataWrapper, ResourceWrapper):
    """
    This is the wrapper for Dataset Series. It inherits from 
    :class:`EOMetadataWrapper`. It implements :class:`DatasetSeriesInterface`.
    
    .. attribute:: FIELDS
    
        * ``eo_id``: the EO ID of the dataset series; value must be a string
        * ``begin_time``: the begin time of the eo metadata entry
        * ``end_time``: the end time of the eo metadata entry
        * ``footprint``: the footprint of the mosaic
    """
    
    REGISTRY_CONF = {
        "name": "Dataset Series Wrapper",
        "impl_id": "resources.coverages.wrappers.DatasetSeriesWrapper",
        "model_class": DatasetSeriesRecord,
        "id_field": "eo_id",
        "factory_ids": ("resources.coverages.wrappers.DatasetSeriesFactory", )
    }
    
    FIELDS = {
        "eo_id": "eo_id",
        "begin_time": "eo_metadata__timestamp_begin",
        "end_time": "eo_metadata__timestamp_end",
        "footprint": "eo_metadata__footprint"
    }
    
    #-------------------------------------------------------------------
    # ResourceInterface methods
    #-------------------------------------------------------------------
    
    # NOTE: partially implemented by ResourceWrapper
    
    def __init__(self):
        super(DatasetSeriesWrapper, self).__init__()
        
        self.__block_md_update = False
    
    def __get_model(self):
        return self._ResourceWrapper__model
    
    def __set_model(self, model):
        self._ResourceWrapper__model = model
        
    __model = property(__get_model, __set_model)
        
    def _get_create_dict(self, params):
        create_dict = super(DatasetSeriesWrapper, self)._get_create_dict(params)
        
        layer_metadata = params.get("layer_metadata")
        
        if layer_metadata:
            create_dict["layer_metadata"] = []
            
            for key, value in layer_metadata.items():
                create_dict["layer_metadata"].append(
                    LayerMetadataRecord.objects.get_or_create(
                        key=key, value=value
                    )[0]
                )
        
        return create_dict
    
    def _create_model(self, create_dict):
        self.__model = DatasetSeriesRecord.objects.create(**create_dict)
    
    def _post_create(self, params):
        for data_source in params.get("data_sources", []):
            self.__model.data_sources.add(data_source.getRecord())
        
        for coverage in params.get("coverages", []):
            self.addCoverage(coverage)
    
    def _updateModel(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(DatasetSeriesWrapper, self)._updateModel(link_kwargs, unlink_kwargs, set_kwargs)

        try:
            self.__block_md_update = True
            
            # link
            data_sources = link_kwargs.get("data_sources", [])
            coverages = link_kwargs.get("coverages", [])
            for data_source in data_sources:
                self.__model.data_sources.add(data_source.getRecord())
            for coverage in coverages:
                self.addCoverage(coverage)
            
            # unlink
            data_sources = unlink_kwargs.get("data_sources", [])
            coverages = unlink_kwargs.get("coverages", [])
            for data_source in data_sources:
                self.__model.data_sources.remove(data_source.getRecord())
            for coverage in coverages:
                self.removeCoverage(coverage)
                
            self._updateMetadata()
        finally:
            self.__block_md_update = False
    
    def _aggregateMetadata(self, eo_metadata_set):
        try:
            begin_time = min(eo_metadata_set.values_list('timestamp_begin', flat=True))
            end_time = max(eo_metadata_set.values_list('timestamp_end', flat=True))
        # Work around for issue in Django 1.5
        except TypeError:
            begin_time = min([t.timestamp_begin for t in eo_metadata_set])
            end_time = max([t.timestamp_end for t in eo_metadata_set])
        
        try:
            # use the aggregate calculation if provided
            footprint = MultiPolygon(
                Polygon.from_bbox(eo_metadata_set.extent(field_name="footprint"))
            )
        except:
            # manual collection of footprints (required for backends other than 
            # SpatiaLite or PostGIS)
            logger.warn("Performing manual envelope calculation.")
            envelopes = MultiPolygon([
                md.footprint.envelope for md in eo_metadata_set
            ])
            footprint = envelopes.envelope
        
        return (begin_time, end_time, footprint)
    
    def _updateMetadata(self, added_coverage=None):
        begin_time = None
        footprint = None
        
        rect_qs = self.__model.rect_datasets.all()
        ref_qs = self.__model.ref_datasets.all()
        mosaic_qs = self.__model.rect_stitched_mosaics.all()
        
        # if a coverage was added, do not accumulate metadata, instead make a
        # simplified approach and only add the metadata of the new coverage
        if added_coverage:
            eo_metadata = self.__model.eo_metadata
            sum_count = rect_qs.count() + ref_qs.count() + mosaic_qs.count()
            
            # only perform shortcut when there is guranteed metadata of 
            # included coverages
            if sum_count > 1:
                logger.info("Performing shortcut metadata calculation.")
                eo_metadata.timestamp_begin = min(
                    eo_metadata.timestamp_begin, added_coverage.getBeginTime()
                )
                eo_metadata.timestamp_end = max(
                    eo_metadata.timestamp_end, added_coverage.getEndTime()
                )
                
                # calculate a new combined envelope if necessary 
                new_envelope = added_coverage.getFootprint().envelope
                series_envelopes = eo_metadata.footprint
                if not series_envelopes.contains(new_envelope):
                    series_envelopes.append(new_envelope)
                    eo_metadata.footprint = MultiPolygon(
                        series_envelopes.envelope
                    )
                
                eo_metadata.full_clean()
                eo_metadata.save()
                
                # exit now
                return
        
        # perform the normal metadata aggregation here
        if len(rect_qs):
            eo_metadata_set = EOMetadataRecord.objects.filter(
                rectifieddatasetrecord_set__in = rect_qs
            )

            begin_time, end_time, footprint = self._aggregateMetadata(
                eo_metadata_set
            )

        
        if len(ref_qs):
            eo_metadata_set = EOMetadataRecord.objects.filter(
                referenceabledatasetrecord_set__in = ref_qs
            )
            
            begin_time_ref, end_time_ref, footprint_ref = self._aggregateMetadata(
                eo_metadata_set
            )
            
            if begin_time:
                begin_time = min(begin_time, begin_time_ref)
                end_time = max(end_time, end_time_ref)
                footprint = footprint.union(footprint_ref)
            else:
                begin_time = begin_time_ref
                end_time = end_time_ref
                footprint = footprint_ref

        
        if len(mosaic_qs):
            eo_metadata_set = EOMetadataRecord.objects.filter(
                rectifiedstitchedmosaicrecord_set__in = mosaic_qs
            )
        
            begin_time_mosaics, end_time_mosaics, footprint_mosaics = self._aggregateMetadata(
                eo_metadata_set
            )
            
            if begin_time:
                begin_time = min(begin_time, begin_time_mosaics)
                end_time = max(end_time, end_time_mosaics)
                footprint = footprint.union(footprint_mosaics)
            else:
                begin_time = begin_time_mosaics
                end_time = end_time_mosaics
                footprint = footprint_mosaics

        if footprint and footprint.geom_type.upper() != "MULTIPOLYGON":
            footprint = MultiPolygon(footprint)
        elif footprint is None:
            pass

        # if there are no children do not update the metadata
        if begin_time:
            self.__model.eo_metadata.timestamp_begin = begin_time
            self.__model.eo_metadata.timestamp_end = end_time
            self.__model.eo_metadata.footprint = footprint
            
            self.__model.eo_metadata.full_clean()
            self.__model.eo_metadata.save()
            
    #-------------------------------------------------------------------
    # DatasetSeriesInterface methods
    #-------------------------------------------------------------------
    
    def getType(self):
        """
        Returns ``"eo.dataset_series"``.
        """
        
        return "eo.dataset_series"
    
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
        
        return self._get_contained_coverages(filter_exprs=filter_exprs)
        
    
    def getDatasets(self, filter_exprs=None):
        """
        This method returns a list of RectifiedDataset or ReferenceableDataset
        wrappers associated with the dataset series. It accepts an optional
        ``filter_exprs`` parameter which is expected to be a list of filter
        expressions (see module :mod:`eoxserver.resources.coverages.filters`) or
        ``None``. Only the Datasets matching the filters will be returned; in
        case no matching Datasets are found an empty list will be returned.
        """
        
        return self._get_contained_coverages(
            impl_ids = [
                "resources.coverages.wrappers.RectifiedDatasetWrapper",
                "resources.coverages.wrappers.ReferenceableDatasetWrapper"
            ],
            filter_exprs = filter_exprs
        )
        
    def getLayerMetadata(self):
        """
        Returns a list of ``(metadata_key, metadata_value)`` pairs
        that represent MapServer metadata tags to be attached to
        MapServer layers.
        """
        
        return self.__model.layer_metadata.values_list("key", "value")
        
    def contains(self, wrapper):
        """
        This method returns ``True`` if the Dataset Series contains
        the EO Coverage specifiec by its ``wrapper``, ``False``
        otherwise.
        """
        res_id = wrapper.getModel().pk
        
        return self.__model.rect_datasets.filter(pk=res_id).count() > 0 or \
               self.__model.ref_datasets.filter(pk=res_id).count() > 0 or \
               self.__model.rect_stitched_mosaics.filter(pk=res_id).count() > 0
    
    def addCoverage(self, wrapper):
        """
        Adds the EO coverage of type ``res_type`` with primary key
        ``res_id`` to the dataset series. An :exc:`InternalError` is
        raised if the type cannot be handled by Dataset Series.
        Supported wrapper types are:
        
        * ``eo.rect_dataset``
        * ``eo.ref_dataset``
        * ``eo.rect_stitched_mosaic``
        """
        res_type = wrapper.getType()
        res_id = wrapper.getModel().pk
        
        if res_type == "eo.rect_dataset":
            self.__model.rect_datasets.add(res_id)
        elif res_type == "eo.ref_dataset":
            self.__model.ref_datasets.add(res_id)
        elif res_type == "eo.rect_stitched_mosaic":
            self.__model.rect_stitched_mosaics.add(res_id)
        else:
            raise InternalError(
                "Cannot add coverages of type '%s' to Dataset Series" %\
                res_type
            )
        
        if not self.__block_md_update:
            self._updateMetadata(wrapper)

    def removeCoverage(self, wrapper):
        """
        Removes the EO coverage specified by its ``wrapper`` from the
        dataset series. An :exc:`InternalError` is
        raised if the type cannot be handled by Dataset Series.
        Supported wrapper types are:
        
        * ``eo.rect_dataset``
        * ``eo.ref_dataset``
        * ``eo.rect_stitched_mosaic``
        """
        res_type = wrapper.getType()
        res_id = wrapper.getModel().pk
        
        if res_type == "eo.rect_dataset":
            self.__model.rect_datasets.remove(res_id)
        elif res_type == "eo.ref_dataset":
            self.__model.ref_datasets.remove(res_id)
        elif res_type == "eo.rect_stitched_mosaic":
            self.__model.rect_stitched_mosaics.remove(res_id)
        else:
            raise InternalError(
                "Cannot add coverages of type '%s' to Dataset Series" %\
                res_type
            )
    
        if not self.__block_md_update:
            self._updateMetadata()
    
    def getDataDirs(self):
        """
        This method returns a list of directories which hold the 
        dataset series data.
        """
        
        return list(
            self.__model.data_dirs.values_list('dir', flat=True)
        )
    
    def getDataSources(self):
        data_source_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
        return [data_source_factory.get(record=record) 
                for record in self.__model.data_sources.all()]
    
    def getImagePattern(self):
        """
        Returns the filename pattern for image files to be included 
        into the stitched mosaic. The pattern is expressed in the format
        accepted by :func:`fnmatch.fnmatch`.
        """
        
        return self.__model.image_pattern
        
    def _get_contained_coverages(self, impl_ids=None, filter_exprs=None):
        _filter_exprs = []

        if filter_exprs is not None:
            _filter_exprs.extend(filter_exprs)
        
        self_expr = System.getRegistry().getFromFactory(
            "resources.coverages.filters.CoverageExpressionFactory",
            {"op_name": "contained_in", "operands": (self.__model.pk,)}
        )
        _filter_exprs.append(self_expr)
        
        factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        
        if impl_ids is None:
            return factory.find(filter_exprs=_filter_exprs)
        else:
            return factory.find(impl_ids=impl_ids, filter_exprs=_filter_exprs)


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
