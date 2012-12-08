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

from eoxserver.resources.coverages.exceptions import ManagerError

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.coverage import CoverageManager
from eoxserver.resources.coverages.managers.coverage import CoverageManagerDatasetMixIn
from eoxserver.resources.coverages.managers.coverage import CoverageManagerEOMixIn

#-------------------------------------------------------------------------------

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
            
            visible = kwargs.get("visible", True)
            
            return self._create_coverage(
                coverage_id,
                data_package,
                data_source,
                geo_metadata,
                range_type_name,
                layer_metadata,
                eo_metadata,
                container=kwargs.get("container"),
                containers=containers,
                visible=visible
            )
    
    
    def _prepare_update_dicts(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(EODatasetManager, self)._prepare_update_dicts(link_kwargs, unlink_kwargs, set_kwargs) 
    
        link_kwargs["containers"] = self._get_containers(link_kwargs)
        unlink_kwargs["containers"] = self._get_containers(unlink_kwargs)

#-------------------------------------------------------------------------------
