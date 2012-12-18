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

import os

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import MetadataException

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.base import BaseManager

#-------------------------------------------------------------------------------

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

#-------------------------------------------------------------------------------

class CoverageManagerDatasetMixIn(object):
    def _get_location(self, params, fail=True):
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
        
        if not location and fail:
            raise InternalError(
                "You must specify a data location to create a coverage."
            )
        
        return location 

    def _get_geo_metadata(self, data_package, params):
        geo_metadata = params.get("geo_metadata")
        
        default_srid = params.get("default_srid")
        
        if not geo_metadata and data_package:
            geo_metadata = data_package.readGeospatialMetadata(default_srid)
            if geo_metadata is None:
                raise InternalError("Geospatial Metadata could not be read from "
                                    "the dataset.")
            
        return geo_metadata

#-------------------------------------------------------------------------------

class CoverageManagerEOMixIn(object):
    def _get_metadata_location(self, location, params, force=True):
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
        
        if not md_location and force:
            md_path = "%s.xml" % os.path.splitext(location.getPath())[0]
            
            md_location = self.location_factory.create(
                type=location.getType(),
                path=md_path,
                
            )
        
        return md_location
    
    def _get_eo_metadata(self, data_package, params):
        try:
            if data_package:
                return data_package.readEOMetadata()
        except MetadataException:
            if "eo_metadata" in params:
                return params["eo_metadata"]
            else:
                raise
        
        if "eo_metadata" in params:
            return params["eo_metadata"]
        
        raise MetadataException("Creating EO Coverages requires EO Metadata.")
    
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

#-------------------------------------------------------------------------------
