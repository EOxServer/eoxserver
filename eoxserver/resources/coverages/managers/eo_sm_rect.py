#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import NoSuchCoverageException

from eoxserver.processing.mosaic import make_mosaic

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.base import BaseManagerContainerMixIn
from eoxserver.resources.coverages.managers.coverage import CoverageManager

#-------------------------------------------------------------------------------

class RectifiedStitchedMosaicManager(BaseManagerContainerMixIn, CoverageManager):
    """
    Coverage Manager for `RectifiedStitchedMosaics`
       
    To add data sources to the ``RectifiedStitchedMosaic`` at the time it is
    created the ``data_sources`` and ``data_dirs`` parameters can be used. 
    The ``data_sources`` parameter shall be a list of objects implementing 
    the :class:`~.DataSourceInterface`. Alternatively the ``data_dirs`` 
    parameter shall be a list of dictionaries consisting of the following
    arguments:
       
    * ``search_pattern``: a regular expression to specify what files in the
      directory are considered as data files.
   
    * ``path``: for local or FTP data sources, this parameter shall be a 
      path to a valid directory, containing the data files.
    
    * ``type``: defines the type of the location describing the data source.
      This can either be `local` or `remote`.
      
    These parameters can also be used in the context of an 
    :meth:`~BaseManager.update` within the `link` or `unlink` dict.
    
    To specify geospatial metadata use the ``geo_metadata`` parameter,
    which has to be an instance of :class:`~.GeospatialMetadata`. Optionally
    ``default_srid`` can be used to declare a default SRID. When updating,
    it has to be placed within the ``set`` dict.
    
    To specify earth observation related metadata use the ``eo_metadata``
    parameter which has to be of the type :class:`~.EOMetadata`. When updating,
    it has to be placed within the ``set`` dict.
    
    The mandatory parameter ``range_type_name`` states which range type
    this coverage is using.
    
    If the created dataset shall be inserted into a `DatasetSeries` or
    `RectifiedStitchedMosaic` a wrapper instance can be passed with the
    ``container`` parameter. Alternatively you can use the ``container_ids``
    parameter, passing a list of IDs referencing either `DatasetSeries`
    or `RectifiedStitchedMosaics`. These parameters can also be used in the 
    context of an :meth:`~BaseManager.update` within the `link` or `unlink`
    dict.
    
    Additional metadata can be added with the ``abstract``, ``title``,
    and ``keywords`` parameters.
    
    For additional ``set`` parameters for the :meth:`~BaseManager.update` method
    please refer to the :attr:`~.RectifiedStitchedMosaicWrapper.FIELDS` 
    attribute of the according wrapper.
    
    .. method:: synchronize(obj_id)
    
        This method synchronizes a :class:`~.RectifiedStitchedMosaicRecord`
        identified by the ``obj_id`` with the file system. It does three tasks:
        
        * It scans through all directories specified by its data sources and
          checks if data files exist which do not yet have an according record.
          For each, a :class:`~.RectifiedDatasetRecord` is created and linked
          with the :class:`~.RectifiedStitchedMosaicRecord`. Also all existing,
          but previously not contained datasets are linked to the `Rectified 
          Stitched Mosaic`.
        
        * All contained instances of :class:`~.RectifiedDatasetRecord` are
          checked if their data file still exists. If not, the according record
          is unlinked from the `Rectified Stitched Mosaic` and deleted.
        
        * All instances of :class:`~.RectifiedDatasetRecord` associated with the
          :class:`~.RectifiedStitchedMosaicRecord` which are not referenced by a
          data source anymore are unlinked from the `Rectified Stitched Mosaic`.
    
    .. method:: delete(obj_id)
        
        This deletes a `RectifiedDataset` record specified by its 
        ``obj_id``. If no coverage with this ID can be found, an 
        :exc:`~.NoSuchCoverage` exception will be raised.
        
    """

    _wrapper = "resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"
    _type0   = "rect_stitched_mosaic"
    _type    = "eo.%s"%_type0

    REGISTRY_CONF = {
        "name": "Rectified Stitched Mosaic Manager",
        "impl_id": "resources.coverages.managers.RectifiedStitchedMosaicManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": _type 
        }
    }
    
    def delete(self, obj_id):
        """
        Remove a referenceable dataset identified by the ``obj_id`` parameter.

        :param obj_id: the ID (CoverageID or EOID) of the object to be deleted 
        :rtype: no output returned
        """
        return self._get_wrapper( obj_id ).deleteModel()
    
    def synchronize(self, obj_id):
        """
        This method synchronizes a :class:`~.RectifiedStitchedMosaicRecord`
        identified by the ``obj_id`` with the file system. It does three tasks:
        
        * It scans through all directories specified by its data sources and
          checks if data files exist which do not yet have an according record.
          For each, a :class:`~.RectifiedDatasetRecord` is created and linked
          with the :class:`~.RectifiedStitchedMosaicRecord`. Also all existing,
          but previously not contained datasets are linked to the `Rectified 
          Stitched Mosaic`.
        
        * All contained instances of :class:`~.RectifiedDatasetRecord` are
          checked if their data file still exists. If not, the according record
          is unlinked from the `Rectified Stitched Mosaic` and deleted.
        
        * All instances of :class:`~.RectifiedDatasetRecord` associated with the
          :class:`~.RectifiedStitchedMosaicRecord` which are not referenced by a
          data source anymore are unlinked from the `Rectified Stitched Mosaic`.

        :param obj_id: the ID (CoverageID or EOID) of the object to be synchronised
        :rtype: no output returned
        """

        container = self._get_wrapper( obj_id )
        
        self._synchronize(container, container.getDataSources(), container.getDatasets())
        self._make_mosaic(container)
    
    def __init__(self):
        super(RectifiedStitchedMosaicManager, self).__init__()
        
        self.data_source_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
        
        self.tile_index_factory = System.getRegistry().bind(
            "resources.coverages.data.TileIndexFactory"
        )

    def _create(self, coverage_id, **kwargs):
        geo_metadata = self._get_geo_metadata(kwargs)
        
        range_type_name = self._get_range_type_name(kwargs)
        
        layer_metadata = self._get_layer_metadata(kwargs)
        
        eo_metadata = self._get_eo_metadata(kwargs)
        
        tile_index = self._get_tile_index(kwargs)
        
        data_sources = self._get_data_sources(kwargs)
        
        containers = self._get_containers(kwargs)
        
        coverages = self._get_coverages(kwargs)
        
        coverage = self._create_coverage(
            coverage_id,
            geo_metadata,
            range_type_name,
            layer_metadata,
            eo_metadata,
            tile_index,
            data_sources,
            kwargs.get("container"),
            containers,
            coverages
        )
        
        self._create_contained(coverage, data_sources)
        
        self._make_mosaic(coverage)
        
        return coverage
    
    def _create_coverage(self, coverage_id, geo_metadata, range_type_name, layer_metadata, eo_metadata, tile_index, data_sources, container=None, containers=None, coverages=None):
        return self.coverage_factory.create(
            impl_id=self._wrapper,
            params={
                "coverage_id": coverage_id,
                "geo_metadata": geo_metadata,
                "range_type_name": range_type_name,
                "layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "tile_index": tile_index,
                "data_sources": data_sources,
                "container": container,
                "containers": containers,
                "coverages": coverages
            }
        )
    
    def _get_geo_metadata(self, params):
        if "geo_metadata" in params:
            return params["geo_metadata"]
        else:
            raise InternalError(
                "Mandatory 'geo_metadata' keyword argument missing."
            )
    
    def _get_eo_metadata(self, params):
        if "eo_metadata" in params:
            return params["eo_metadata"]
        else:
            raise InternalError(
                "Mandatory 'eo_metadata' keyword argument missing."
            )
    
    def _get_tile_index(self, params):
        if "storage_dir" in params:
            return self.tile_index_factory.create(
                type="index", storage_dir = params["storage_dir"]
            )
        else:
            raise InternalError(
                "Mandatory 'storage_dir' keyword argument missing."
            )
            
    def _get_id_prefix(self):
        return self._type0 
    
    def _get_contained_range_type_name(self, container, location=None):
        return container.getRangeType().name
    
    def _get_containers(self, params):
        containers = params.get("container_ids", [])
        wrappers = []
        
        for obj_id in containers:
            wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.DatasetSeriesFactory",
                {"obj_id": obj_id}
            )
            
            if not wrapper:
                raise InternalError(
                    "Dataset Series or ID %s not found." % obj_id
                ) 
            
            wrappers.append(wrapper)
        
        return wrappers 
    
    def _make_mosaic(self, coverage):
        make_mosaic(coverage)

    def _prepare_update_dicts(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(RectifiedStitchedMosaicManager, self)._prepare_update_dicts(link_kwargs, unlink_kwargs, set_kwargs)
        link_kwargs["data_sources"] = self._get_data_sources(link_kwargs)

    #---------------------------------------------------------------------------

    def _validate_type(self, coverage):
        return coverage.getType() == self._type 


    def _get_wrapper( self, obj_id ) : 
        wrapper = self.coverage_factory.get( impl_id=self._wrapper, obj_id=obj_id )
        if not wrapper: raise NoSuchCoverageException(obj_id)
        return wrapper


    def get_all_ids(self): 
        """
        Get CoverageIDs of all registered rectified stitched mosaics.

        :rtype: list of CoverageIDs (strings)  
        """
        return [ obj.getCoverageId() for obj in self.coverage_factory.find(
                    impl_ids=[self._wrapper] ) ]


    def check_id(self, obj_id): 
        """
        Check whether the ``obj_id`` identifies an existing rectified stitched 
        mosaic.

        :rtype: boolean  
        """
        try: 
            self._get_wrapper( obj_id )
            return True 
        except NoSuchCoverageException : 
            return False 

#-------------------------------------------------------------------------------
