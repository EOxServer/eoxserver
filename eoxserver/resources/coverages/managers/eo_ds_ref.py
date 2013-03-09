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

from eoxserver.resources.coverages.exceptions import NoSuchCoverageException

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.eo_ds import EODatasetManager

#-------------------------------------------------------------------------------

class ReferenceableDatasetManager(EODatasetManager):
    # TODO documentation
    """

        Coverage Manager for `ReferenceableDatasets`. 

        Sorry, but no one has bothered to document this class yet. 
    
    """

    _wrapper = "resources.coverages.wrappers.ReferenceableDatasetWrapper"
    _type0   = "ref_dataset"
    _type    = "eo.%s"%_type0

    REGISTRY_CONF = {
        "name": "Referenceable Dataset Manager",
        "impl_id": "resources.coverages.managers.ReferenceableDatasetManager",
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
    
    def _validate_type(self, coverage):
        return coverage.getType() == self._type  
    
    def _create_coverage(self, coverage_id, data_package, data_source, geo_metadata, range_type_name, layer_metadata, eo_metadata, container, containers, visible):
        return self.coverage_factory.create(
            impl_id=self._wrapper,
            params={
                "coverage_id": coverage_id,
                "data_package": data_package,
                "data_source": data_source,
                "geo_metadata": geo_metadata,
                "range_type_name": range_type_name,
                "layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "container": container,
                "containers": containers,
                "visible": visible
            }
        )
    
    def _get_id_prefix(self):
        return self._type0

    #---------------------------------------------------------------------------

    def _get_wrapper( self, obj_id ) : 
        wrapper = self.coverage_factory.get( impl_id=self._wrapper, obj_id=obj_id )
        if not wrapper: raise NoSuchCoverageException(obj_id)
        return wrapper


    def get_all_ids(self): 
        """
        Get CoverageIDs of all registered referenceable datasets.

        :rtype: list of CoverageIDs (strings)  
        """
        return [ obj.getCoverageId() for obj in self.coverage_factory.find(
                    impl_ids=[self._wrapper] ) ]


    def check_id(self, obj_id): 
        """
        Check whether the ``obj_id`` identifies an existing referenceable
        dataset.

        :rtype: boolean  
        """
        try: 
            self._get_wrapper( obj_id )
            return True 
        except NoSuchCoverageException : 
            return False 


    def is_automatic(self, obj_id): 
        """
        For the dataset identified by the ``obj_id`` parameter return value of
        the ``automatic`` boolean flag. Returns 

        :param obj_id: the ID (CoverageID or EOID) of the object to be deleted 
        :rtype: boolean value, ``True`` if the dataset is automatic 
        """
        return self._get_wrapper( obj_id ).isAutomatic()

#-------------------------------------------------------------------------------
