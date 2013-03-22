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
from ConfigParser import RawConfigParser
from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.resources.coverages.exceptions import NoSuchDatasetSeriesException

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers.base import BaseManager
from eoxserver.resources.coverages.managers.base import BaseManagerContainerMixIn

#-------------------------------------------------------------------------------

class DatasetSeriesManager(BaseManagerContainerMixIn, BaseManager):
    """
    This manager handles interactions with ``DatasetSeries``.
    
       
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
          
    These parameters can also be used in the context of an 
    :meth:`~BaseManager.update` within the `link` or `unlink` dict.
       
    To specify earth observation related metadata use the ``eo_metadata``
    parameter which has to be of the type :class:`~.EOMetadata`. When updating,
    it has to be placed within the ``set`` dict.
    
    For additional ``set`` parameters for the :meth:`~BaseManager.update` method
    please refer to the :attr:`~.DatasetSeriesWrapper.FIELDS` attribute of the
    according wrapper.

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

    _type0   = "dataset_series"
    _type    = "eo.%s"%_type0
    
    REGISTRY_CONF = {
        "name": "Dataset Series Manager",
        "impl_id": "resources.coverages.managers.DatasetSeriesManager",
        "registry_values": {
            "resources.coverages.interfaces.res_type": _type 
        }
    }
    
    def __init__(self):
        super(DatasetSeriesManager, self).__init__()
        
        self.dataset_series_factory = self.id_factory
        
        self.data_source_factory = System.getRegistry().bind(
            "resources.coverages.data.DataSourceFactory"
        )
    
    def synchronize(self, obj_id):
        """
        Synchronise a dataset series identified by the ``obj_id`` 
        parameter.

        :param obj_id: the ID (EOID) of the object to be synchronised 
        :rtype: no output returned
        """
        """
        This method synchronizes a :class:`~.DatasetSeriesRecord`
        identified by the ``obj_id`` with the file system. It does three tasks:
        
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

        :param obj_id: the ID (CoverageID or EOID) of the object to be synchronised
        :rtype: no output returned
        """

        container = self._get_wrapper( obj_id ) 
        
        self._synchronize(container, container.getDataSources(), container.getEOCoverages())
    
    def _prepare_update_dicts(self, link_kwargs, unlink_kwargs, set_kwargs):
        super(DatasetSeriesManager, self)._prepare_update_dicts(link_kwargs, unlink_kwargs, set_kwargs)
        link_kwargs["data_sources"] = self._get_data_sources(link_kwargs)
    
    def _get_id_factory(self):
        return System.getRegistry().bind(
            "resources.coverages.wrappers.DatasetSeriesFactory"
        )
    
    def _get_id_prefix(self):
        return self._type0

    def _create(self, eo_id, **kwargs):
        #layer_metadata = self._get_layer_metadata(kwargs)
        
        eo_metadata = self._get_eo_metadata(kwargs)
        
        data_sources = self._get_data_sources(kwargs)
        
        coverages = self._get_coverages(kwargs)
        
        dataset_series = self.dataset_series_factory.create(
            impl_id="resources.coverages.wrappers.DatasetSeriesWrapper",
            params={
                "eo_id": eo_id,
                #"layer_metadata": layer_metadata,
                "eo_metadata": eo_metadata,
                "data_sources": data_sources,
                "coverages": coverages
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

    #---------------------------------------------------------------------------

    def delete(self, obj_id):
        """
        Remove a dataset series identified by the ``obj_id`` parameter.

        :param obj_id: the EOID of the object to be deleted 
        :rtype: no output returned
        """
        return self._get_wrapper( obj_id ).deleteModel()


    def _get_wrapper( self, obj_id ) : 
        wrapper = self.dataset_series_factory.get( obj_id=obj_id )
        if not wrapper: raise NoSuchDatasetSeriesException(obj_id)
        return wrapper


    def get_all_ids(self): 
        """
        Get EOIDs of all registered dataset series.

        :rtype: list of EOIDs (strings)  
        """
        return [ obj.getEOID() for obj in self.dataset_series_factory.find() ]


    def check_id(self, obj_id): 
        """
        Check whether the ``obj_id`` identifies an existing dataset series.

        :rtype: boolean  
        """
        try: 
            self._get_wrapper( obj_id )
            return True 
        except NoSuchDatasetSeriesException : 
            return False 

#-------------------------------------------------------------------------------
