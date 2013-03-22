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

from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import ManagerError
from eoxserver.resources.coverages.models import PlainCoverageRecord

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.coverage import CoverageManager
from eoxserver.resources.coverages.managers.coverage import CoverageManagerDatasetMixIn

#-------------------------------------------------------------------------------

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


    def get_all_ids(self): 
        """
        Get IDs of all registered rectified datasets.

        :rtype: list of CoverageIDs (strings)  
        """
        raise InternalError("Not implemented.")


    def check_id(self, obj_id): 
        """
        Check whether the ``obj_id`` identifies an existing record.

        :rtype: boolean  
        """
        raise InternalError("Not implemented.")

#-------------------------------------------------------------------------------
