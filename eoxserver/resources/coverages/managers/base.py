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

import os.path
import logging

from uuid import uuid4

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import ManagerError
from eoxserver.resources.coverages.exceptions import NoSuchCoverageException

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.id_manager import CoverageIdManager

#-------------------------------------------------------------------------------

logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------

class BaseManager(object):
    """
    """
    
    def __init__(self):
        self.id_factory = self._get_id_factory()
        
        self.location_factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        self.data_package_factory = System.getRegistry().bind(
            "resources.coverages.data.DataPackageFactory"
        )
        
    def create(self, obj_id=None, request_id=None, **kwargs):
        """
        Creates a new instance of the underlying type and returns an according
        wrapper object. The optional parameter ``obj_id`` is used as 
        CoverageID/EOID and a UUID is generated automatically when omitted.
        
        If the ID was previously reserved by a specific ``request_id`` this 
        parameter must be set.
        
        The other parameters depend on the actual coverage manager type and will
        be documented there.
        
        If the given ID is already in use, an :exc:`~.CoverageIdInUseError`
        exception is raised. If the ID is already reserved by another
        ``request_id``, an :exc:`~.CoverageIdReservedError` is raised.
        These exceptions are sub-classes of :exc:`~.CoverageIdError`.
        
        :param obj_id: the ID (CoverageID or EOID) of the object to be created
        :type obj_id: string
        :param request_id: an optional request ID for the acquisition of the 
                           CoverageID/EOID.
        :type request_id: string
        :param kwargs: the arguments 
        :rtype: a wrapper of the created object
        """
        
        id_mgr = CoverageIdManager()
        
        if obj_id is None:
            # generate a new ID
            for _ in range(3):
                new_id = self._generate_id()
                if id_mgr.available(new_id):
                    obj_id = new_id
                    break
            else:
                raise InternalError("Could not generate a unique identifier.")
            
        id_mgr.reserve(obj_id, request_id)
        
        try:
            coverage = self._create(obj_id, **kwargs)
        
        finally:
            id_mgr.release(obj_id, fail=True)
        
        return coverage
            
    def update(self, obj_id, link=None, unlink=None, set=None):
        """
        Updates the coverage/dataset series identified by ``obj_id``. The 
        ``link`` and ``unlink`` dicts are used to add or remove references to
        other objects, whereas the ``set`` dict values are used to set 
        attributes of the objects. This can be either a set of values (like
        ``geo_metadata`` or ``eo_metadata``) or single values as defined in the
        ``FIELDS`` dict of the according wrapper.
        
        For all supported attributes please refer to the actually used manager.
        
        :param obj_id: the ID (CoverageID or EOID) of the object to be updated
        :type obj_id: string
        :param link: objects to be linked with
        :type link: dict or None
        :param unlink: objects to be unlinked
        :type unlink: dict or None
        :param set: attributes to be set
        :type set: dict or None
        :rtype: a wrapper of the altered object
        """
        # get the three update dicts
        link_kwargs = link if link is not None else {}
        unlink_kwargs = unlink if unlink is not None else {}
        set_kwargs = set if set is not None else {}
        
        # prepare the update dicts
        self._prepare_update_dicts(link_kwargs, unlink_kwargs, set_kwargs)
        
        # get the correct wrapper
        wrapper = self.id_factory.get(obj_id=obj_id)
        
        if wrapper is None:
            raise NoSuchCoverageException(obj_id)
        
        wrapper.updateModel(link_kwargs, unlink_kwargs, set_kwargs)
        
        # update the fields
        keys = wrapper.getAttrNames()
        for key, value in set_kwargs.items():
            if key in keys:
                wrapper.setAttrValue(key, value)
                
        wrapper.saveModel()
        
        return wrapper
        
    def _prepare_update_dicts(self, link_kwargs, unlink_kwargs, set_kwargs):
        # Override this function to prepare the three dictionaries
        # prior to the update of the model
        pass
    
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

#-------------------------------------------------------------------------------

class BaseManagerContainerMixIn(object):
    def __init__(self):
        super(BaseManagerContainerMixIn, self).__init__()
        
        self.rect_dataset_mgr = System.getRegistry().bind(
            "resources.coverages.managers.RectifiedDatasetManager"
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
    
    def _get_coverages(self, params):
        coverages = params.get("coverages", [])
        
        coverage_factory = System.getRegistry().bind(
            "resources.coverages.wrappers.EOCoverageFactory"
        )
        for cid in params.get("coverage_ids", []):
            coverage = coverage_factory.get(obj_id=cid)
            if not coverage:
                raise NoSuchCoverageException(cid)
            coverages.append(coverage)
        
        return coverages
    
    def _create_contained(self, container, data_sources):
        # TODO: make this more efficient by using updateModel()
        
        new_datasets = []
        for data_source in data_sources:
            locations = data_source.detect()
            
            logger.info("Detected locations: %s"%[location.getPath() for location in locations])
            
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
                    logger.info("Add %s (%s) to %s."%(
                            coverage.getCoverageId(), coverage.getType(),
                            container.getType()
                        )
                    )
                    container.addCoverage(existing_coverages[0])
                    new_datasets.append(existing_coverages[0])
                    
                else:
                    eo_metadata = data_package.readEOMetadata()
                    
                    coverage_id_mgr = CoverageIdManager()
                    
                    coverage_id = coverage_id_mgr.reserve(
                        eo_metadata.getEOID()
                    )
                    
                    try:
                        range_type_name = self._get_contained_range_type_name(
                            container, location
                        )
                        
                        if container.getType() == "eo.rect_stitched_mosaic":
                            default_srid = container.getSRID()
                        else:
                            default_srid = None
                        
                        logger.info("Creating new coverage with ID %s." % coverage_id)
                        # TODO: implement creation of ReferenceableDatasets,
                        # RectifiedStitchedMosaics for DatasetSeriesManager
                        new_dataset = self.rect_dataset_mgr.create(
                            coverage_id,
                            location=location,
                            md_location=md_location,
                            range_type_name=range_type_name,
                            data_source=data_source,
                            container=container,
                            default_srid=default_srid
                        )
                        
                        logger.info("Done creating new coverage with ID %s." % coverage_id)
                        
                        new_datasets.append(new_dataset)
                        
                    finally:
                        coverage_id_mgr.release(coverage_id)
                    
        
        return new_datasets
    
    def _synchronize(self, container, data_sources, datasets):
        # TODO: make this more efficient by using updateModel()
        
        new_datasets = self._create_contained(container, data_sources)

        # if new datasets have been created the container metadata
        # have already been updated
        do_md_update = not len(new_datasets)
        
        # delete all datasets, which do not have a file
        for dataset in datasets:
            if dataset.getType() == "eo.rect_stitched_mosaic":
                # do not delete the tile index from a stitched mosaic
                continue
            
            if not dataset.getData().getLocation().exists():
                logger.info(
                    "Location %s does not exist. Deleting dangling dataset with ID %s"%(
                        dataset.getData().getLocation().getPath(),
                        dataset.getCoverageId()
                    )
                )
                
                self.rect_dataset_mgr.delete(dataset.getCoverageId())
                
                # force updating the metadata
                do_md_update = True
            
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
                    do_md_update = True

        # if no update has been done do it now
        if do_md_update:
            container.updateModel({}, {}, {})
        
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
    
    def _prepare_update_dicts(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(BaseManagerContainerMixIn, self)._prepare_update_dicts(link_kwargs, unlink_kwargs, set_kwargs)
        link_kwargs["coverages"] = self._get_coverages(link_kwargs)
        unlink_kwargs["coverages"] = self._get_coverages(unlink_kwargs)

#-------------------------------------------------------------------------------
