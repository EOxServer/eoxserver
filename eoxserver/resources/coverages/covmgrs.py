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
This module implements coverage managers that can be used to read data from GDAL
datasets and to register coverages automatically. Furthermore, coverages can be
updated and deleted, e.g. to stay in sync with data on a storage.
"""

import os.path
from ConfigParser import RawConfigParser
import logging
from uuid import uuid4
from datetime import datetime, timedelta

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError, IDInUse
from eoxserver.resources.coverages.interfaces import ManagerInterface
from eoxserver.resources.coverages.exceptions import (
    ManagerError, NoSuchCoverageException, CoverageIdReservedError,
    CoverageIdInUseError, CoverageIdReleaseError
)
from eoxserver.resources.coverages.models import (
    ReservedCoverageIdRecord, CoverageRecord
)

class BaseManager(object):
    def __init__(self):
        self.id_factory = self._get_id_factory()
        
        self.location_factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        self.data_package_factory = System.getRegistry().bind(
            "resources.coverages.data.DataPackageFactory"
        )
    
    def acquireID(self, obj_id=None, fail=False):
        if obj_id:
            if self.id_factory.exists(obj_id=obj_id):
                if fail:
                    raise IDInUse(
                        "The desired ID (%s) is already in use." % obj_id
                    )
                else:
                    new_id = self._generate_id()
            else:
                new_id = obj_id
        else:
            new_id = self._generate_id()
        
        return new_id
        
    def releaseID(self, obj_id):
        pass
        
    def create(self, obj_id=None, **kwargs):
        """
        Creates a new instance of the underlying type and returns an
        according wrapper object.
        The optional parameter ``obj_id`` is used as CoverageID/EOID
        and is generated automatically when omitted. If the given ID
        is already in use, an :exc:`~.IDinUse` exception is raised.
        The other parameters depend on the actual coverage manager
        type.
        """
        if obj_id:
            _id = obj_id
            _release = False
        else:
            _id = self.acquireID()
            _release = True

        try:
            coverage = self._create(_id, **kwargs)
            
            if _release:
                self.releaseID(_id)
            
            return coverage
            
        except:
            if _release:
                self.releaseID(_id)
                
            raise
            
    def update(self, obj_id, **kwargs):
        raise InternalError("Not implemented.")
    
    def delete(self, obj_id):
        raise InternalError("Not implemented.")
    
    def synchronize(self, obj_id):
        raise InternalError("Not implemented.")
        
    def _get_id_factory(self):
        raise InternalError("Not implemented.")
    
    def _generate_id(self):
        return "%s_%s" % (self._get_id_prefix(), uuid4().hex)
    
    def _get_id_prefix(self):
        raise InternalError("Not implemented.")

    def _create_data_package(self, location, metadata_location=None):
        if location.getType() == "local":
            data_package_type = "local"
        elif location.getType() == "ftp":
            data_package_type = "remote"
        elif location.getType() == "rasdaman":
            data_package_type = "rasdaman"
        
        return self.data_package_factory.getOrCreate(
            type=data_package_type,
            location=location,
            metadata_location=metadata_location
        )

class BaseManagerContainerMixIn(object):
    def __init__(self):
        super(BaseManagerContainerMixIn, self).__init__()
        
        self.rect_dataset_mgr = System.getRegistry().bind(
            "resources.coverages.covmgrs.RectifiedDatasetManager"
        )
    
    def _get_data_sources(self, params):
        data_sources = params.get("data_sources", [])
        
        for dir_dict in params.get("data_dirs", []):
            location = self.location_factory.create(
                **dir_dict
            )
            
            search_pattern = dir_dict.get("search_pattern")
            
            data_sources.append(
                self.data_source_factory.getOrCreate(
                    type="data_source",
                    location=location,
                    search_pattern=search_pattern
                )
            )
        
        return data_sources
    
    def _create_contained(self, container, data_sources):
        for data_source in data_sources:
            locations = data_source.detect()
            
            logging.info("Detected locations: %s"%[location.getPath() for location in locations])
            
            for location in locations:
                md_location = self._guess_metadata_location(location)
            
                data_package = self._create_data_package(location, md_location)
                
                coverage_factory = System.getRegistry().bind(
                    "resources.coverages.wrappers.EOCoverageFactory"
                )
                
                filter_exprs = [System.getRegistry().getFromFactory(
                    "resources.coverages.filters.CoverageExpressionFactory", {
                        "op_name": "referenced_by",
                        "operands": (location,)
                    }
                )]
                
                existing_coverages = coverage_factory.find(
                    impl_ids=["resources.coverages.wrappers.RectifiedDatasetWrapper",
                              "resources.coverages.wrappers.ReferenceableDatasetWrapper"],
                    filter_exprs=filter_exprs
                )
                
                if len(existing_coverages) == 1:
                    coverage = existing_coverages[0]
                    logging.info("Add %s (%s) to %s."%(
                            coverage.getCoverageId(), coverage.getType(),
                            container.getType()
                        )
                    )
                    container.addCoverage(existing_coverages[0])
                    
                else:
                    eo_metadata = data_package.readEOMetadata()
                    
                    coverage_id = self.rect_dataset_mgr.acquireID(
                        eo_metadata.getEOID(), fail=True
                    )
                    
                    range_type_name = self._get_contained_range_type_name(
                        container, location
                    )
                    
                    logging.info("Creating new coverage with ID %s." % coverage_id)
                    
                    # TODO: implement creation of ReferenceableDatasets,
                    # RectifiedStitchedMosaics for DatasetSeriesManager
                    self.rect_dataset_mgr.create(
                        coverage_id,
                        location=location,
                        md_location=md_location,
                        range_type_name=range_type_name,
                        data_source=data_source,
                        container=container
                    )
                
                    self.rect_dataset_mgr.releaseID(coverage_id)
                    
                    logging.info("Done creating new coverage with ID %s." % coverage_id)
    
    def _synchronize(self, container, data_sources, datasets):
        self._create_contained(container, data_sources)
        
        # delete all datasets, which do not have a file
        for dataset in datasets:
            if not dataset.getData().getLocation().exists():
                logging.info(
                    "Location %s does not exist. Deleting dangling dataset with ID %s"%(
                        dataset.getData().getLocation().getPath(),
                        dataset.getCoverageId()
                    )
                )
                
                self.rect_dataset_mgr.delete(dataset.getCoverageId())
            
            elif dataset.getAttrValue("automatic"):
                # remove all automatic coverages from a mosaic/dataset series
                # which are not contained in a data source.
                contained = False
                for data_source in container.getDataSources():
                    if data_source.contains(dataset):
                        contained = True
                        break
                
                if not contained:
                    container.removeCoverage(dataset)
    
    def _guess_metadata_location(self, location):
        if location.getType() == "local":
            return self.location_factory.create(
                type="local",
                path="%s.xml" % os.path.splitext(location.getPath())[0]
            )
        elif location.getType() == "ftp":
            return self.location_factory.create(
                type="ftp",
                path="%s.xml" % os.path.splitext(location.getPath())[0],
                host=location.getHost(),
                port=location.getPort(),
                user=location.getUser(),
                passwd=location.getPassword()
            )
        else:
            return None
    
    def _get_contained_range_type_name(self, container, location=None):
        raise InternalError("Not implemented.")

class CoverageManager(BaseManager):
    def __init__(self):
        super(CoverageManager, self).__init__()
        
        self.coverage_factory = self.id_factory
    
    def _get_id_factory(self):
        return System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
    
    def _get_range_type_name(self, params):
        if "range_type_name" in params:
            return params["range_type_name"]
        else:
            raise InternalError(
                "Mandatory 'range_type_name' parameter missing."
            )
    
    def _get_layer_metadata(self, params):
        # TODO: extend this dictionary if necessary
        KEY_MAPPING = {
            "abstract": "ows_abstract",
            "title": "ows_title",
            "keywords": "ows_keywords"
        }
        
        layer_metadata = {}
        
        for key in KEY_MAPPING:
            if key in params:
                layer_metadata[KEY_MAPPING[key]] = params[key]
        
        return layer_metadata

    def _get_existing_coverage(self, data_package):
        existing_coverages = data_package.getCoverages()
        
        if len(existing_coverages) == 0:
            return None
        else:
            return existing_coverages[0]

class CoverageManagerDatasetMixIn(object):
    def _get_location(self, params):
        location = None
        
        if "location" in params:
            location = params["location"]
        
        if "local_path" in params:
            if location:
                raise InternalError(
                    "Parameters defining the data location must be unambiguous."
                )
            else:
                location = self.location_factory.create(
                    type="local",
                    path=params["local_path"]
                )
        
        if "remote_path" in params:
            if location:
                raise InternalError(
                    "Parameters defining the data location must be unambiguous."
                )
            elif "ftp_host" not in params:
                raise InternalError(
                    "If specifying 'remote_path' the 'ftp_host' argument is required."
                )
            else:
                location = self.location_factory.create(
                    type="ftp",
                    path=params["remote_path"],
                    host=params["ftp_host"],
                    port=params.get("ftp_port"),
                    user=params.get("ftp_user"),
                    passwd=params.get("ftp_passwd")
                )
        
        if "collection" in params:
            if location:
                raise InternalError(
                    "Parameters defining the data location must be unambiguous."
                )
            elif "ras_host" not in params:
                raise InternalError(
                    "If specifying 'collection' the 'ras_host' argument is required."
                )
            else:
                location = self.location_factory.create(
                    type="rasdaman",
                    collection=params["collection"],
                    oid=params.get("oid"),
                    host=params["ras_host"],
                    port=params.get("ras_port"),
                    user=params.get("ras_user"),
                    passwd=params.get("ras_passwd"),
                    db_name=params.get("ras_db")
                )
        elif "oid" in params:
            raise InternalError(
                "You must specify a 'collection' to specify a valid rasdaman array location."
            )
        
        if not location:
            raise InternalError(
                "You must specify a data location to create a coverage."
            )
        
        return location 

    def _get_geo_metadata(self, data_package, params):
        geo_metadata = params.get("geo_metadata")
        
        default_srid = params.get("default_srid")
        
        if not geo_metadata and data_package:
            geo_metadata = data_package.readGeospatialMetadata(default_srid)
            
        return geo_metadata

class CoverageManagerEOMixIn(object):
    def _get_metadata_location(self, location, params):
        if "eo_metadata" in params:
            return None
        else:
            md_location = None
            
            if "md_location" in params:
                md_location = params["md_location"]
        
            if "md_local_path" in params:
                if md_location:
                    raise InternalError(
                        "Metadata location must be unambiguous."
                    )
                else:
                    md_location = self.location_factory.create(
                        type="local",
                        path=params["md_local_path"]
                    )
            
            if "md_remote_path" in params:
                if md_location:
                    raise InternalError(
                        "Metadata location must be unambiguous."
                    )
                else:
                    md_location = self.location_factory.create(
                        type="ftp",
                        path=params["md_remote_path"],
                        host=location.getHost(),
                        port=location.getPort(),
                        user=location.getUser(),
                        passwd=location.getPassword()
                    )
            
            if not md_location:
                md_path = "%s.xml" % os.path.splitext(location.getPath())[0]
                
                md_location = self.location_factory.create(
                    type=location.getType(),
                    path=md_path,
                    
                )
            
            return md_location
    
    def _get_eo_metadata(self, data_package, params):
        if "eo_metadata" in params:
            eo_metadata = params["eo_metadata"]
        elif data_package:
            eo_metadata = data_package.readEOMetadata()
        else:
            raise InternalError(
                "Creating EO Coverages requires EO Metadata."
            )
    
        return eo_metadata
    
    def _get_containers(self, params):
        containers = params.get("container_ids", [])
        wrappers = []
        
        for obj_id in containers:
            wrapper = System.getRegistry().getFromFactory(
                "resources.coverages.wrappers.DatasetSeriesFactory",
                {"obj_id": obj_id}
            )
            
            if not wrapper:
                wrapper = System.getRegistry().getFromFactory(
                    "resources.coverages.wrappers.EOCoverageFactory", {
                        "impl_id":"resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
                        "obj_id": obj_id
                    }
                )
            
            if not wrapper:
                raise InternalError(
                    "Dataset Series or Rectified Stitched Mosaic with ID %s not found." % obj_id
                ) 
            
            wrappers.append(wrapper)
        
        return wrappers 

class PlainCoverageManager(CoverageManager, CoverageManagerDatasetMixIn):
    
    # TODO: implement PlainCoverageWrapper, CoverageFactory
    
    def _create(self, coverage_id, **kwargs):
        location = self._get_location(kwargs)
        
        data_package = self._create_data_package(location)
        
        existing_coverage = self._get_existing_coverage(data_package)
        
        if existing_coverage:

            if self._validate_type(existing_coverage):
                return existing_coverage
            else:
                raise ManagerError(
                    "Another coverage with different type, but the same data exists already."
                )
                
        else:
            
            geo_metadata = self._get_geo_metadata(data_package, kwargs)
            
            range_type_name = self._get_range_type_name(location, kwargs)
            
            layer_metadata = self._get_layer_metadata(kwargs)
            
            return self._create_coverage(
                coverage_id,
                data_package,
                geo_metadata,
                range_type_name,
                layer_metadata
            )
    
    def _validate_type(self, coverage):
        return coverage.getType() == "plain"

    def _create_coverage(self, coverage_id, data_package, geo_metadata, range_type_name, layer_metadata):
        pass


class EODatasetManager(CoverageManager, CoverageManagerDatasetMixIn, CoverageManagerEOMixIn):
    def _create(self, coverage_id, **kwargs):
        location = self._get_location(kwargs)
        
        metadata_location = self._get_metadata_location(location, kwargs)
        
        data_package = self._create_data_package(
            location, metadata_location
        )
        
        existing_coverage = self._get_existing_coverage(data_package)
        
        if existing_coverage:
            
            if self._validate_type(existing_coverage):
                return existing_coverage
            else:
                raise ManagerError(
                    "Another coverage with different type, but the same data exists already."
                )
        
        else:
            
            geo_metadata = self._get_geo_metadata(data_package, kwargs)
            
            range_type_name = self._get_range_type_name(kwargs)
            
            layer_metadata = self._get_layer_metadata(kwargs)
            
            eo_metadata = self._get_eo_metadata(data_package, kwargs)
            
            data_source = kwargs.get("data_source")
            
            containers = self._get_containers(kwargs)
            
            return self._create_coverage(
                coverage_id,
                data_package,
                data_source,
                geo_metadata,
                range_type_name,
                layer_metadata,
                eo_metadata,
                container=kwargs.get("container"),
                containers=containers
            )

class RectifiedDatasetManager(EODatasetManager):
    """
    Coverage Manager for `RectifiedDatasets`
    
    .. method:: create(obj_id=None, **kwargs)
    
       This creates and returns a :class:`~.RectifiedDatasetWrapper`
       from the attributes given in ``kwargs``. 
       
       If the ``obj_id`` argument is omitted a new object ID shall be generated
       using the same mechanism as :meth:`acquireID`. If the provided object ID
       is invalid or already in use, appropriate exceptions shall be raised.
       
       To define the data and metadata location, the ``location`` and 
       ``md_location`` parameters can be used, where the value has to implement 
       the :class:`~.LocationInterface`. 
       Alternatively ``local_path`` and ``md_local_path`` 
       can be used to define local locations. For when the data and metadata is 
       located on an FTP server, use ``remote_path`` and ``md_remote_path``
       instead, which also requires the ``ftp_host`` parameter (``ftp_port``, 
       ``ftp_user`` and ``ftp_passwd`` are optional). When the data is located
       in a rasdaman database use the ``collection`` and ``ras_host`` parameters. 
       ``oid``, ``ras_port``, ``ras_user``, ``ras_passwd``, and ``ras_db`` can 
       be used to further specify the location.
       
       To specify geospatial metadata use the ``geo_metadata`` parameter,
       which has to be an instance of :class:`~.GeospatialMetadata`. Optionally
       ``default_srid`` can be used to declare a default SRID.
       
       To specify earth observation related metadata use the ``eo_metadata``
       parameter which has to be of the type :class:`~.EOMetadata`.
       
       The mandatory parameter ``range_type_name`` states which range type
       this coverage is using.
       
       If the created dataset shall be inserted into a `DatasetSeries` or
       `RectifiedStitchedMosaic` a wrapper instance can be passed with the
       ``container`` parameter. Alternatively you can use the ``container_ids``
       parameter, passing a list of IDs referencing either `DatasetSeries`
       or `RectifiedStitchedMosaics`.
       
       Additional metadata can be added with the ``abstract``, ``title``,
       and ``keywords`` parameters.
       
    .. method:: delete(obj_id)
        
        This deletes a `RectifiedDataset` record specified by its 
        ``obj_id``. If no coverage with this ID can be found, an 
        :exc:`~.NoSuchCoverage` exception will be raised.
        
    """
    
    REGISTRY_CONF = {
        "name": "Rectified Dataset Manager",
        "impl_id": "resources.coverages.covmgrs.RectifiedDatasetManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": "eo.rect_dataset"
        }
    }
    
    def delete(self, obj_id):
        wrapper = self.coverage_factory.get(
            impl_id="resources.coverages.wrappers.RectifiedDatasetWrapper",
            obj_id=obj_id
        )
        if not wrapper:
            raise NoSuchCoverageException
        wrapper.deleteModel()
    
    def _validate_type(self, coverage):
        return coverage.getType() == "eo.rect_dataset"
    
    def _create_coverage(self, coverage_id, data_package, data_source, geo_metadata, range_type_name, layer_metadata, eo_metadata, container, containers):
        return self.coverage_factory.create(
            impl_id="resources.coverages.wrappers.RectifiedDatasetWrapper",
            params={
                "coverage_id": coverage_id,
                "data_package": data_package,
                "data_source": data_source,
                "geo_metadata": geo_metadata,
                "range_type_name": range_type_name,
                "layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "container": container,
                "containers": containers
            }
        )
    
    def _get_id_prefix(self):
        return "rect_dataset"
        
RectifiedDatasetManagerImplementation = \
ManagerInterface.implement(RectifiedDatasetManager)

class ReferenceableDatasetManager(EODatasetManager):
    pass
    
    # TODO: implement referenceable grid coverages
    
class RectifiedStitchedMosaicManager(BaseManagerContainerMixIn, CoverageManager):
    """
    Coverage Manager for `RectifiedStitchedMosaics`
    
    .. method:: create(obj_id=None, **kwargs)
    
       This creates and returns a :class:`~.RectifiedStitchedMosaicWrapper`
       from the attributes given in ``kwargs``. 
       
       If the ``obj_id`` argument is omitted a new object ID shall be generated
       using the same mechanism as :meth:`acquireID`. If the provided object ID
       is invalid or already in use, appropriate exceptions shall be raised.
       
       To add data sources to the ``RectifiedStitchedMosaic`` at the time it is
       created the ``data_sources`` and ``data_dirs`` parameters can be used. 
       The ``data_sources`` parameter shall be a list of objects implementing 
       the :class:``~.DataSourceInterface``. Alternatively the ``data_dirs`` 
       parameter shall be a list of dictionaries consisting of the following
       arguments:
       
       * ``search_pattern``: a regular expression to specify what files in the
         directory are considered as data files.
       
       * ``path``: for local or FTP data sources, this parameter shall be a 
         path to a valid directory, containing the data files.
        
       * ``type``: defines the type of the location describing the data source.
         This can either be `local` or `remote`.
       
       To specify geospatial metadata use the ``geo_metadata`` parameter,
       which has to be an instance of :class:`~.GeospatialMetadata`. Optionally
       ``default_srid`` can be used to declare a default SRID.
       
       To specify earth observation related metadata use the ``eo_metadata``
       parameter which has to be of the type :class:`~.EOMetadata`.
       
       The mandatory parameter ``range_type_name`` states which range type
       this coverage is using.
       
       If the created dataset shall be inserted into a `DatasetSeries` or
       `RectifiedStitchedMosaic` a wrapper instance can be passed with the
       ``container`` parameter. Alternatively you can use the ``container_ids``
       parameter, passing a list of IDs referencing either `DatasetSeries`
       or `RectifiedStitchedMosaics`.
       
       Additional metadata can be added with the ``abstract``, ``title``,
       and ``keywords`` parameters. 
    
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
    REGISTRY_CONF = {
        "name": "Rectified Stitched Mosaic Manager",
        "impl_id": "resources.coverages.covmgrs.RectifiedStitchedMosaicManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": "eo.rect_stitched_mosaic"
        }
    }
    
    def delete(self, obj_id):
        wrapper = self.coverage_factory.get(
            impl_id="resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            obj_id=obj_id
        )
        wrapper.delete()
    
    def synchronize(self, obj_id):
        container = self.coverage_factory.get(
            impl_id="resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            obj_id=obj_id
        )
        
        self._synchronize(container, container.getDataSources(), container.getDatasets())
    
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
        
        coverage = self._create_coverage(
            coverage_id,
            geo_metadata,
            range_type_name,
            layer_metadata,
            eo_metadata,
            tile_index,
            data_sources,
            kwargs.get("container"),
            containers
        )
        
        self._create_contained(coverage, data_sources)
        
        self._make_mosaic(coverage)
        
        return coverage
    
    def _create_coverage(self, coverage_id, geo_metadata, range_type_name, layer_metadata, eo_metadata, tile_index, data_sources, container=None, containers=None):
        return self.coverage_factory.create(
            impl_id="resources.coverages.wrappers.RectifiedStitchedMosaicWrapper",
            params={
                "coverage_id": coverage_id,
                "geo_metadata": geo_metadata,
                "range_type_name": range_type_name,
                "layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "tile_index": tile_index,
                "data_sources": data_sources,
                "container": container,
                "containers": containers
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
        return "rect_stitched_mosaic"
    
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
        pass

RectifiedStitchedMosaicManagerImplementation = \
ManagerInterface.implement(RectifiedStitchedMosaicManager)

class DatasetSeriesManager(BaseManagerContainerMixIn, BaseManager):
    """
    This manager handles interactions with ``DatasetSeries``.
    
    .. method:: create(obj_id=None, **kwargs)
    
       This creates and returns a :class:`~.DatasetSeriesWrapper`
       from the attributes given in ``kwargs``. 
       
       If the ``obj_id`` argument is omitted a new object ID shall be generated
       using the same mechanism as :meth:`acquireID`. If the provided object ID
       is invalid or already in use, appropriate exceptions shall be raised.
       
       To add data sources to the ``DatasetSeries`` at the time it is created 
       the ``data_sources`` and ``data_dirs`` parameters can be used. The 
       ``data_sources`` parameter shall be a list of objects implementing the 
       :class:``~.DataSourceInterface``. Alternatively the ``data_dirs`` 
       parameter shall be a list of dictionaries consisting of the following
       arguments:
       
       * ``search_pattern``: a regular expression to specify what files in the
         directory are considered as data files.
       
       * ``path``: for local or FTP data sources, this parameter shall be a 
         path to a valid directory, containing the data files.
        
       * ``type``: defines the type of the location describing the data source.
         This can either be `local` or `remote`.
       
       To specify earth observation related metadata use the ``eo_metadata``
       parameter which has to be of the type :class:`~.EOMetadata`.

    .. method:: synchronize(obj_id)
    
        This method synchronizes a :class:`~.DatasetSeriesRecord` identified by
        the ``obj_id`` with the file system. It does three tasks:
        
        * It scans through all directories specified by its data sources and
          checks if data files exist which do not yet have an according record.
          For each, a :class:`~.RectifiedDatasetRecord` is created and linked
          with the :class:`~.DatasetSeriesRecord`. Also all existing,
          but previously not contained datasets are linked to the `Dataset
          Series`.
        
        * All contained instances of :class:`~.RectifiedDatasetRecord` are
          checked if their data file still exists. If not, the according record
          is unlinked from the `Dataset Series` and deleted.
        
        * All instances of :class:`~.RectifiedDatasetRecord` associated with the
          :class:`~.DatasetSeriesRecord` which are not referenced by a
          data source anymore are unlinked from the `Dataset Series`.

    .. method:: delete(obj_id)
        
        This deletes a `RectifiedDataset` record specified by its 
        ``obj_id``. If no coverage with this ID can be found, an 
        :exc:`~.NoSuchCoverage` exception will be raised.
    """
    
    REGISTRY_CONF = {
        "name": "Dataset Series Manager",
        "impl_id": "resources.coverages.covmgrs.DatasetSeriesManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": "eo.dataset_series"
        }
    }
    
    def __init__(self):
        super(DatasetSeriesManager, self).__init__()
        
        self.dataset_series_factory = self.id_factory
        
        self.data_source_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
    
    def synchronize(self, obj_id):
        container = self.dataset_series_factory.get(
            obj_id=obj_id
        )
        
        self._synchronize(container, container.getDataSources(), container.getEOCoverages())
        
    def _get_id_factory(self):
        return System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
    
    def _get_id_prefix(self):
        return "dataset_series"

    def _create(self, eo_id, **kwargs):
        #layer_metadata = self._get_layer_metadata(kwargs)
        
        eo_metadata = self._get_eo_metadata(kwargs)
        
        data_sources = self._get_data_sources(kwargs)
        
        dataset_series = self.dataset_series_factory.create(
            impl_id="resources.coverages.wrappers.DatasetSeriesWrapper",
            params={
                "eo_id": eo_id,
                #"layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "data_sources": data_sources
            }
        )
        
        self._create_contained(dataset_series, data_sources)
        
        return dataset_series

    def _get_eo_metadata(self, kwargs):
        if "eo_metadata" in kwargs:
            return kwargs["eo_metadata"]
        else:
            raise InternalError(
                "Mandatory 'eo_metadata' keyword argument missing."
            )
    
    def _get_contained_range_type_name(self, container, location=None):
        range_type_name = None
        
        if location.getType() == "local":
            conf_path = "%s.conf" % os.path.splitext(location.getPath())[0]
            
            if os.path.exists(conf_path):
                parser = RawConfigParser()
                parser.read(conf_path)
                if parser.has_option("range_type", "range_type_name"):
                    range_type_name = parser.get("range_type", "range_type_name")
            else:
                def_path = os.path.join(
                    os.path.dirname(location.getPath()),
                    "__default__.conf"
                )
            
                if os.path.exists(def_path):
                    parser = RawConfigParser()
                    parser.read(def_path)
                    if parser.has_option("range_type", "range_type_name"):
                        range_type_name = parser.get("range_type", "range_type_name")
                        
        if range_type_name:
            return range_type_name
        else:
            return "RGB"

DatasetSeriesManagerImplementation = \
ManagerInterface.implement(DatasetSeriesManager)

class CoverageIdManager(BaseManager):
    """
    Manager for Coverage IDs.
    """
    
    def reserve(self, coverage_id, request_id=None, until=None):
        """
        Tries to reserve a ``coverage_id`` until a given datetime. If ``until``
        is omitted, the configuration value 
        ``resources.coverages.coverage_id.reservation_time`` is used.
        
        If the ID is already reserved, a :class:`~.CoverageIdReservedError` is
        raised. If the ID is already taken by an existing coverage a :class:
        `~.CoverageIdInUseError` is raised.
        """
        
        obj, _ = ReservedCoverageIdRecord.objects.get_or_create(
            coverage_id=coverage_id,
            defaults={
                "until": datetime.now()
            }
        )
        
        if not until:
            values = System.getConfig().getConfigValue(
                "resources.coverages.coverage_id", "reservation_time"
            ).split(":")
            
            for _ in xrange(len(values[:4]) - 4):
                values.insert(0, 0)
            
            dt = timedelta(days=int(values[0]), hours=int(values[1]),
                           minutes=int(values[2]), seconds=int(values[3]))
            until = datetime.now() + dt
        
        if datetime.now() < obj.until:
            raise CoverageIdReservedError(
                "Coverage ID '%s' is reserved until %s"%(coverage_id, obj.until)
            )
        elif CoverageRecord.objects.filter(coverage_id=coverage_id).count() > 0:
            raise CoverageIdInUseError("Coverage ID %s is already in use")
        
        obj.request_id = request_id
        obj.until = until
        obj.save()
        
    def release(self, coverage_id, fail=False):
        """
        Releases a previously reserved ``coverage_id``.
        
        If ``fail`` is set to ``True``, an exception is raised when the ID was 
        not previously reserved.
        """
        
        try: 
            obj = ReservedCoverageIdRecord.objects.get(coverage_id=coverage_id)
            obj.delete()
            
        except ReservedCoverageIdRecord.DoesNotExist:
            if fail:
                raise CoverageIdReleaseError(
                    "Coverage ID '%s' was not reserved" % coverage_id
                )
    
    def available(self, coverage_id):
        """
        Returns a boolean value, indicating if a ``coverage_id`` is still 
        available.
        
        A coverage ID is considered available if no :class:`~.CoverageRecord` 
        and :class:`~.ReservedCoverageIdRecord` with that ID exists.
        """
        
        return not (
            ReservedCoverageIdRecord.objects.filter(
                coverage_id=coverage_id,
                until__gte=datetime.now()
            ).count() > 0 or
            CoverageRecord.objects.filter(coverage_id=coverage_id).count() > 0
        )
    
    def getRequestId(self, coverage_id):
        """
        Returns the request ID associated with a :class:
        `~.ReservedCoverageIdRecord` or `None` if the no record with that ID is
        available.
        """
        
        try:
            obj = ReservedCoverageIdRecord.objects.get(coverage_id=coverage_id)
            return obj.request_id
        except ReservedCoverageIdRecord.DoesNotExist:
            return None
        
    def getCoverageIds(self, request_id):
        """
        Returns a list of all coverage IDs associated with a specific request
        ID.
        """
        return [
            obj.coverage_id
            for obj in ReservedCoverageIdRecord.objects.filter(
                request_id=request_id
            )
        ]
        
    def _get_id_factory(self):
        # Unused, but would raise an exception.
        return None
