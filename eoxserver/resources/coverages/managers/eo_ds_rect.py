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

class RectifiedDatasetManager(EODatasetManager):
    """
    Coverage Manager for `RectifiedDatasets`. The following parameters can be
    used for the :meth:`~BaseManager.create` and :meth:`~BaseManager.update`
    methods.
    
    To define the data and metadata location, the ``location`` and 
    ``md_location`` parameters can be used, where the value has to implement the
    :class:`~.LocationInterface`. Alternatively ``local_path`` and 
    ``md_local_path`` can be used to define local locations. For when the data 
    and metadata is located on an FTP server, use ``remote_path`` and 
    ``md_remote_path`` instead, which also requires the ``ftp_host`` parameter 
    (``ftp_port``, ``ftp_user`` and ``ftp_passwd`` are optional). When the data 
    is located in a rasdaman database use the ``collection`` and ``ras_host``
    parameters. ``oid``, ``ras_port``, ``ras_user``, ``ras_passwd``, and 
    ``ras_db`` can be used to further specify the location.
    Currently, these parameters can only be used within the
    :meth:`~BaseManager.create` method and not within the 
    :meth:`~BaseManager.update` method 
    
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
    parameter, passing a list of IDs referencing either `DatasetSeries` or 
    `RectifiedStitchedMosaics`. When used in the context of an
    :meth:`~BaseManager.update`, both parameters can be placed within the
    ``link`` or the ``unlink`` dict, to either add or remove a reference to the
    container.
    
    Additional metadata can be added with the ``abstract``, ``title``,
    and ``keywords`` parameters.
    
    For additional ``set`` parameters for the :meth:`~BaseManager.update` method
    please refer to the :attr:`~.RectifiedDatasetWrapper.FIELDS` attribute of 
    the according wrapper.
    """

    _wrapper = "resources.coverages.wrappers.RectifiedDatasetWrapper"
    _type0   = "rect_dataset"
    _type    = "eo.%s"%_type0
    
    REGISTRY_CONF = {
        "name": "Rectified Dataset Manager",
        "impl_id": "resources.coverages.managers.RectifiedDatasetManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": _type
        }
    }
    
    def delete(self, obj_id):
        """
        Remove a rectified dataset identified by the ``obj_id`` parameter.

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

    #--------------------------------------------------------------------------

    def _get_wrapper( self, obj_id ) : 
        wrapper = self.coverage_factory.get( impl_id=self._wrapper, obj_id=obj_id )
        if not wrapper: raise NoSuchCoverageException(obj_id)
        return wrapper


    def get_all_ids(self): 
        """
        Get CoverageIDs of all registered rectified datasets.

        :rtype: list of CoverageIDs (strings)  
        """
        return [ obj.getCoverageId() for obj in self.coverage_factory.find(
                    impl_ids=[self._wrapper] ) ]


    def check_id(self, obj_id): 
        """
        Check whether the ``obj_id`` identifies an existing rectified dataset.

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
