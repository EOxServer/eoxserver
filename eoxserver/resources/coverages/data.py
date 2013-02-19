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

import os.path
import logging

from eoxserver.contrib import gdal
from eoxserver.core.system import System
from eoxserver.core.records import (
    RecordWrapper, RecordWrapperFactoryInterface, RecordWrapperFactory
)
from eoxserver.core.exceptions import InternalError
from eoxserver.backends.cache import CacheFileWrapper
from eoxserver.resources.coverages.exceptions import (
    EngineError, MetadataException
)
from eoxserver.resources.coverages.models import (
    DataSource, DataPackage, LocalDataPackage, RemoteDataPackage,
    RasdamanDataPackage, TileIndex
)
from eoxserver.resources.coverages.interfaces import (
    DataSourceInterface, DataPackageInterface, TileIndexInterface
)
from eoxserver.resources.coverages.geo import GeospatialMetadata
from eoxserver.resources.coverages.formats import getFormatRegistry


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# Data source wrappers
#-------------------------------------------------------------------------------

class DataSourceWrapper(RecordWrapper):
    """
    This class implements :class:`~.DataSourceInterface`. It inherits from
    :class:`~.RecordWrapper`.
    
    .. method:: setAttrs(**kwargs)
    
       :class:`DataSourceWrapper` defines two attributes that can be assigned
       to an instance:
    
       * ``location``: the location of the data source (a local or remote path
         to a directory)
       * ``search_pattern``: the search pattern defined for the data source
         (optional)
    
    .. method:: sync
    
       See :meth:`.RecordWrapper.sync`.
       
    .. method:: getRecord
    
       See :meth:`.RecordWrapper.getRecord`
    """
    
    REGISTRY_CONF = {
        "name": "Data Source Wrapper",
        "impl_id": "resources.coverages.data.DataSourceWrapper",
        "factory_ids": (
            "resources.coverages.data.DataSourceFactory",
        )
    }
    
    def __init__(self):
        self.record = None
        
        self.location = None
        self.search_pattern = None
    
    def getType(self):
        """
        Returns ``"data_source"``.
        """
        
        return "data_source"
    
    def detect(self):
        """
        Detect files at the location that match the given search pattern.
        Returns a list of locations. If no location has been defined yet,
        return an empty list.
        """
        
        if self.record:
            location = System.getRegistry().getFromFactory(
                factory_id="backends.factories.LocationFactory",
                params={
                    "record": self.record.location
                }        
            )
            
            return location.detect(self.record.search_pattern)
        elif self.location:
            return self.location.detect(self.search_pattern)
        else:
            return []
    
    def contains(self, wrapper):
        """
        Check if the DataSource contains a coverage with a certain ID
        """
        res_id = wrapper.getModel().pk
        
        if self.record:
            return self.record.coveragerecord_set.filter(pk=res_id).count() > 0
        else:
            return False
    
    def _validate_record(self, record):
        if not isinstance(record, DataSource):
            raise InternalError(
                "Cannot assign '%s' object to data source record." % \
                    record.__class__.__name__
            )
    # use default _set_record method
        
    def _validate_attrs(self, **kwargs):
        if "location" not in kwargs:
            raise InternalError(
                "Missing mandatory 'location' keyword argument when initializing data source wrapper."
            )
    
    def _set_attrs(self, **kwargs):
        self.location = kwargs["location"]
        self.search_pattern = kwargs.get("search_pattern")

    def _fetch_unique_record(self):
        return self._fetch()
    
    # use default _fetch method
    
    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "location" in fields:
            if self.location:
                query["location"] = self.location.getRecord()
            else:
                query["location"] = None
        
        if fields is None or "search_pattern" in fields:
            query["search_pattern"] = self.search_pattern
        
        return query
    
    def _get_query_set(self, query):
        return DataSource.objects.filter(**query)
    
    def _create_record(self):
        if self.location:
            location_record = self.location.getRecord()
        else:
            raise InternalError(
                "Cannot create data source without location."
            )
        
        self.record = DataSource.objects.create(
            location=location_record,
            search_pattern=self.search_pattern
        )

DataSourceWrapperImplementation = \
DataSourceInterface.implement(DataSourceWrapper)

#-------------------------------------------------------------------------------
# Data package wrappers
#-------------------------------------------------------------------------------

class DataPackageWrapper(RecordWrapper):
    """
    This is the common base class for data package wrappers. It derives from
    :class:`~.RecordWrapper`.
    
    .. method:: setAttrs(**kwargs)
    
       :class:`DataPackageWrapper` defines three attributes that can be assigned
       to any data package instance:
    
       * ``location``: the location of the data; the location type depends on
         the concrete data package subclass
       * ``metadata_location``: the location of the metadata; the location type
         depends on the concrete data package subclass
       * ``metadata_format_name``: the name of the metadata format; can be
         derived automatically from the metadata using :meth:`readEOMetadata`
    
    .. method:: sync
    
       See :meth:`.RecordWrapper.sync`.
       
    .. method:: getRecord
    
       See :meth:`.RecordWrapper.getRecord`
    """
    
    def __init__(self):
        super(DataPackageWrapper, self).__init__()
        
        self.metadata_format_name = None
        self.location = None
        self.metadata_location = None
    
    def open(self):
        """
        Open the underlying dataset with GDAL and return a
        :class:`osgeo.gdal.Dataset` object. This method raises
        :exc:`~.EngineError` if GDAL was not able to open the dataset. It
        raises :exc:`~.DataAccessError` if the dataset could not be made
        accessible to GDAL (e.g. download of a remote FTP resource failed).
        """
        
        self.prepareAccess()
        
        gdal_str = self.getGDALDatasetIdentifier()
        
        try:
            ds = gdal.Open(str(gdal_str))
            
            if ds is None:
                raise EngineError(
                    "Could not open GDAL Dataset '%s'." % gdal_str
                )
            else:
                return ds
        
        except Exception, e:
            raise EngineError(
                "Could not open GDAL Dataset '%s'. Error message: '%s'" % (
                    gdal_str, str(e)
                )
            )
    
    def getSourceFormat(self): 
        """
        Return the source data file format. 
        """
        return str( self.record.source_format )

    def getLocation(self):
        """
        Return the location of the data, i.e. an object implementing
        :class:`~.LocationInterface`. The location type depends on the
        concrete data package subclass.
        """
        
        if self.record:
            return System.getRegistry().getFromFactory(
                "backends.factories.LocationFactory",
                params = {
                    "record": self.record.data_location
                }
            )
        else:
            return self.location
    
    def getMetadataLocation(self):
        """
        Return the location of the metadata, i.e. an object implementing
        :class:`~.LocationInterface`. The location type depends on the
        concrete data package subclass.
        """
        
        if self.record and self.record.metadata_location:
            return System.getRegistry().getFromFactory(
                "backends.factories.LocationFactory",
                params = {
                    "record": self.record.metadata_location
                }
            )
        elif not self.record:
            return self.metadata_location
        elif not self.metadata_location:
            return None
    
    def getCoverages(self):
        """
        Return the coverages that use this data package.
        """
        
        if self.record:
            return System.getRegistry().bind(
                "resources.coverages.wrappers.EOCoverageFactory"
            ).find(
                impl_ids = [
                    "resources.coverages.wrappers.RectifiedDatasetWrapper",
                    "resources.coverages.wrappers.ReferenceableDatasetWrapper"
                    # TODO: add plain coverages
                ],
                filter_exprs = [
                    System.getRegistry().getFromFactory(
                        factory_id = "resources.coverages.filters.CoverageExpressionFactory",
                        params = {
                            "op_name": "attr",
                            "operands": ("data_package", "=", self.record.pk)
                        }
                    )
                ]
            )
        else:
            return []
            
    def readGeospatialMetadata(self, default_srid=None):
        """
        Read geospatial metadata from the underlying dataset. The return value
        is a :class:`~.GeospatialMetadata` instance. The method accepts an
        optional integer ``default_srid`` argument which predefines the
        output SRID if it cannot be retrieved from the dataset; see
        :meth:`~.GeospatialMetadata.readFromDataset`.
        
        The dataset is opened using :meth:`open`; it may raise
        :exc:`~.DataAccessError` or :exc:`~.EngineError` in the error cases
        described there.
        """
        
        ds = self.open()
        
        return GeospatialMetadata.readFromDataset(ds, default_srid)
    
    def readEOMetadata(self):
        """
        Read EO Metadata from the metadata location and return an
        :class:`~.EOMetadata` instance. :exc:`~.DataAccessError` may be raised
        if the metadata location cannot be made accessible (e.g. an XML 
        metadata file cannot be retrieved from a remote location).
        :exc:`~.MetadataException` will be raised if the metadata cannot be
        read (e.g. because a metadata file does not contain valid XML).
        """
        
        if self.getMetadataLocation():
            self._prepare_metadata_access()
            
            try:
                md_location = self._get_accessible_metadata_location()
            
                md_reader = System.getRegistry().findAndBind(
                    intf_id = "resources.coverages.interfaces.EOMetadataReader",
                    params = {
                        "location": md_location
                        #"resources.coverages.interfaces.location_type": md_location.getType(),
                        #"resources.coverages.interfaces.encoding_type": "xml" # TODO: make this configurable
                    }
                )
            
                eo_metadata = md_reader.readEOMetadata(md_location)
                
                self.metadata_format_name = \
                    eo_metadata.getMetadataFormat().getName()
                
                self._post_metadata_access()
            except:
                self._post_metadata_access()
                raise MetadataException("")
                
            return eo_metadata
        else:
            return None
    
    def prepareAccess(self):
        """
        Prepare access to the underlying dataset. This makes the underlying
        dataset accessible so that :meth:`getAccessibleLocation` and
        :meth:`getGDALDatasetIdentifier` can yield meaningful results. Concrete
        subclasses have to override this. By default :exc:`~.InternalError` is
        raised.
        """
        
        raise InternalError("Not implemented.")
    
    def getAccessibleLocation(self):
        """
        Get an accessible location of the underlying dataset. A previous
        successful call to :meth:`prepareAccess` may be necessary for this
        method to yield a meaningful result. Concrete subclasses have to
        override this. By default :exc:`~.InternalError` is raised.
        """
        
        raise InternalError("Not implemented.")
    
    def getGDALDatasetIdentifier(self):
        """
        Get a GDAL dataset identifier for the underlying dataset, i.e. the
        string to be passed on to the :func:`gdal.Open` function. A previous
        successful call to :meth:`prepareAccess` may be necessary for this
        method to yield a meaningful result. Concrete subclasses have to
        override this. By default :exc:`~.InternalError` is raised.
        """
        
        raise InternalError("Not implemented.")

    def _validate_attrs(self, **kwargs):
        if not "location" in kwargs:
            raise InternalError(
                "When assigning attributes to a local data package you must either provide a 'location' keyword argument"
            )

    def _set_attrs(self, **kwargs):
        # set attributes
                
        self.location = kwargs["location"]
        
        self.metadata_location = kwargs.get("metadata_location")
        self.metadata_format_name = kwargs.get("metadata_format_name")
    
    def _fetch_unique_record(self):
        # no uniqueness constraints apply
        
        return None

    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "location" in fields:
            query["data_location"] = self.getLocation().getRecord()
        
        if fields is None or "metadata_location" in fields:
            metadata_location = self.getMetadataLocation()
            
            if metadata_location:
                query["metadata_location"] = metadata_location.getRecord()
            else:
                query["metadata_location"] = None
                
        
        if fields is None or "metadata_format_name" in fields:
            query["metadata_format_name"] = self.metadata_format_name
    
        return query
    
    def _prepare_metadata_access(self):
        # called by :meth:`readEOMetadata` to prepare access to a remote
        # metadata resource
        
        raise InternalError("Not implemented.")
    
    def _get_accessible_metadata_location(self):
        # called by :meth:`readEOMetadata` to retrieve an accessible location
        # for a metadata resource
        
        raise InternalError("Not implemented.")
    
    def _post_metadata_access(self):
        # called by :meth:`readEOMetadata` to clean up after metadata decoding
        
        raise InternalError("Not implemented.")

class LocalDataPackageWrapper(DataPackageWrapper):
    """
    This is a wrapper for data packages stored in files on the local file
    system. It inherits from :class:`DataPackageWrapper`. See there for the
    inherited methods.
    """
    
    REGISTRY_CONF = {
        "name": "Local Data Package Wrapper",
        "impl_id": "resources.coverages.data.LocalDataPackageWrapper",
        "factory_ids": (
            "resources.coverages.data.DataPackageFactory",
        )
    }
    
    def __init__(self, **kwargs):
        super(LocalDataPackageWrapper, self).__init__(**kwargs)
        self.source_format = None
    
    def getDataStructureType(self):
        """
        Returns ``"file"``.
        """
        
        return "file"
    
    def getType(self):
        """
        Returns ``"local"``.
        """
        
        return "local"
    
    def prepareAccess(self):
        """
        Nothing to be done here as locations on the local file system are
        accessible by themselves.
        """
        pass
    
    def getAccessibleLocation(self):
        """
        Returns the same as :meth:`getLocation`.
        """
        return self.getLocation()
                
    def getGDALDatasetIdentifier(self):
        """
        Returns the path to the data file.
        
        .. note:: This does not account for data formats where the dataset is
           structured into subdatasets. This is future work
        """
        return os.path.abspath(self.getLocation().getPath())
    
    def _validate_record(self, record):
        # raise :exc:`~.InternalError` if the model record is not of type
        # :class:`~.LocalDataPackage`.
        
        if record.data_package_type != "local":
            raise InternalError(
                "Cannot assign '%s' type data package record to local data package." %\
                record.data_package_type
            )
            
    def _set_record(self, record):
        # be sure to set the model record to the :class:`~.LocalDataPackage`
        # instance (the model record instance may be an instance of
        # the superclass :class:`~.DataPackage` as well)
        
        if isinstance(record, LocalDataPackage):
            self.record = record
        else:
            self.record = record.localdatapackage
    
    def _set_attrs(self, **kwargs):
        super(LocalDataPackageWrapper, self)._set_attrs(**kwargs)
        self.source_format = kwargs.get("source_format")
        
        if self.source_format is None:
            driver_name = "GDAL/" + self.open().GetDriver().ShortName
            frmt = getFormatRegistry().getFormatsByDriver(driver_name)[0]
            self.source_format = frmt.mimeType
    
    def _get_query_set(self, query):
        return LocalDataPackage.objects.filter(**query)
        
    def _create_record(self):
        # create a model record from the instance attributes
        
        if self.metadata_location:
            metadata_location_record = self.metadata_location.getRecord()
        else:
            metadata_location_record = None
        
        self.record = LocalDataPackage.objects.create(
            data_package_type = LocalDataPackage.DATA_PACKAGE_TYPE,
            data_location = self.location.getRecord(),
            metadata_location = metadata_location_record,
            metadata_format_name = self.metadata_format_name,
            source_format = self.source_format
        )
        
    def _prepare_metadata_access(self):
        # nothing to be done here
        
        pass
    
    def _get_accessible_metadata_location(self):
        # return local metadata file location
        
        return self.getMetadataLocation()
    
    def _post_metadata_access(self):
        # nothing to be done here
        
        pass

LocalDataPackageWrapperImplementation = \
DataPackageInterface.implement(LocalDataPackageWrapper)

class RemoteDataPackageWrapper(DataPackageWrapper):
    """
    This is a wrapper for data stored in a remote repository accessible via
    FTP. It inherits from :class:`DataPackageWrapper`. See there for the
    inherited methods.
    
    This class wraps not only the (remote) locations of data and metadata, but
    also :class:`~.CacheFileWrapper` instances for locally cached copies of the
    respective files.
    
    .. method:: initialize(**kwargs)
    
       In addition to the attributes declared in
       :meth:`DataPackageWrapper.initialize` this method accepts an optional
       ``cache_file`` keyword argument which is expected to be an instance of
       :class:`~.CacheFileWrapper`.
    """
    
    REGISTRY_CONF = {
        "name": "Remote Data Package Wrapper",
        "impl_id": "resources.coverages.data.RemoteDataPackageWrapper",
        "factory_ids": (
            "resources.coverages.data.DataPackageFactory",
        )
    }
    
    def __init__(self):
        super(RemoteDataPackageWrapper, self).__init__()
        
        self.cache_file = None
        self.md_cache_file = None
    
    def getDataStructureType(self):
        """
        Returns ``"file"``.
        """
        
        return "file"
    
    def getType(self):
        """
        Returns ``"remote"``.
        """
        
        return "remote"
    
    def prepareAccess(self):
        """
        Loads a remote data file into the local cache, if necessary. Never
        omit the call to :meth:`prepareAccess` when attempting to access a
        remote dataset, subsequent method calls to :meth:`open`,
        :meth:`getAccessibleLocation` and :meth:`getGDALDatasetIdentifier` may
        fail.
        """
        
        if not self.cache_file:
            if self.record and self.record.cache_file:
                self.cache_file = CacheFileWrapper(self.record.cache_file)
                
                self.cache_file.access()
            else:
                remote_location = self.getLocation()
                
                self.cache_file = CacheFileWrapper.create(
                    os.path.basename(remote_location.getPath())
                )
                
                self.cache_file.copy(remote_location)
                
                if self.record:
                    self.record.cache_file = self.cache_file.getModel()
                    
                    self.record.save()
        else:
            self.cache_file.access()
    
    def getAccessibleLocation(self):
        """
        Returns the location of the locally cached data file.
        """
        
        if self.cache_file:
            return self.cache_file.getLocation()
        else:
            raise InternalError(
                "Cache file not present or not initialized. Please do always call prepareAccess() before accessing a remote data package."
            )
        
    def getGDALDatasetIdentifier(self):
        """
        Returns the path to the location of the locally cached data file.
        """
        
        return os.path.abspath(self.getAccessibleLocation().getPath())
        
    def _validate_record(self, record):
        # check if the model record points to a remote data package
        
        if record.data_package_type != "remote":
            raise InternalError(
                "Cannot assign '%s' type data package record to remote data package." %\
                record.data_package_type
            )
            
    def _set_record(self, record):
        # be sure to set the model record to the :class:`~.RemoteDataPackage`
        # instance
        
        if isinstance(record, RemoteDataPackage):
            self.record = record
        else:
            self.record = record.remotedatapackage
    
    def _set_attrs(self, **kwargs):
        # set attributes; raises :exc:`~.InternalError` if no ``location``
        # keyword argument is given
        
        super(RemoteDataPackageWrapper, self)._set_attrs(**kwargs)
        
        self.cache_file = kwargs.get("cache_file")
        self.source_format = kwargs.get("source_format")
        
        if self.source_format is None:
            driver_name = "GDAL/" + self.open().GetDriver().ShortName
            frmt = getFormatRegistry().getFormatsByDriver(driver_name)[0]
            self.source_format = frmt.mimeType

    def _get_query(self, fields=None):
        query = super(RemoteDataPackageWrapper, self)._get_query(fields)
        
        if fields is None or "cache_file" in fields:
            if self.cache_file:
                query["cache_file"] = self.cache_file.getModel()
            else:
                query["cache_file"] = None
        
        return query
    
    def _get_query_set(self, query):
        return RemoteDataPackage.objects.filter(**query)
    
    def _create_record(self):
        # create :class:`~.RemoteDataPackage` resource
        
        
        if self.cache_file:
            cache_file_record = self.cache_file.getModel()
        else:
            cache_file_record = None
        
        if self.metadata_location:
            metadata_location_record = self.metadata_location.getRecord()
        else:
            metadata_location_record = None
        
        self.record = RemoteDataPackage.objects.create(
            data_package_type = RemoteDataPackage.DATA_PACKAGE_TYPE,
            data_location = self.location.getRecord(),
            metadata_location = metadata_location_record,
            metadata_format_name = self.metadata_format_name,
            cache_file = cache_file_record,
            source_format = self.source_format
        )
        
    def _prepare_metadata_access(self):
        # fetch a local copy of the metadata file (create a cache file for it)
        
        remote_location = self.getMetadataLocation()
        
        self.md_cache_file = CacheFileWrapper.create(
            os.path.basename(remote_location.getPath())
        )
        
        self.md_cache_file.copy(remote_location)
    
    def _get_accessible_metadata_location(self):
        # return the location of the locally cached metadata file
        
        if self.md_cache_file:
            return self.md_cache_file.getLocation()
        else:
            raise InternalError(
                "Cannot access metadata cache file. Did you call _prepare_metadata_access()?"
            )
    
    def _post_metadata_access(self):
        # remove the locally cached metadata file and the corresponding
        # database record
        
        if self.md_cache_file:
            self.md_cache_file.purge()
        
            del self.md_cache_file

RemoteDataPackageWrapperImplementation = \
DataPackageInterface.implement(RemoteDataPackageWrapper)

class RasdamanDataPackageWrapper(DataPackageWrapper):
    """
    This is a wrapper for rasdaman data packages. It inherits from
    :class:`DataPackageWrapper`. See there for the inherited methods.
    """
    
    REGISTRY_CONF = {
        "name": "Rasdaman Data Package Wrapper",
        "impl_id": "resources.coverages.data.RasdamanDataPackageWrapper",
        "factory_ids": (
            "resources.coverages.data.DataPackageFactory",
        )
    }

    def getSourceFormat(self): 
        """
        Return the source data file format. 
        """
        return None 

    def getDataStructureType(self):
        """
        Returns ``"rasdaman_array"``.
        """
        
        return "rasdaman_array"
    
    def getType(self):
        """
        Returns ``"rasdaman_array"``.
        """
        
        return "rasdaman"

    def prepareAccess(self):
        """
        Nothing to be done here. Though not necessarily local the rasdaman
        data is always accessible in the sense that its always possible to
        connect to it without further preconditions.
        """
        
        pass
    
    def getAccessibleLocation(self):
        """
        Return the rasdaman array location.
        """
        
        return self.getLocation()
    
    def getGDALDatasetIdentifier(self):
        """
        Returns a connection string to the rasdaman database combined with
        a query indicating the given dataset. This is the format GDAL expects
        for reading data from a rasdaman array.
        """
        
        location = self.getLocation()
        
        rasdaman_strs = ["rasdaman:"]

        rasdaman_strs.append("host='%s'" % location.getHost())

        if location.getPort() is not None:
            rasdaman_strs.append("port='%d'" % location.getPort())

        # TODO: check if this is a valid parameter
        #if location.getDBName() is not None:
        #    rasdaman_strs.append(
        #        "dbname='%s'" % location.getDBName()
        #    )

        if location.getUser() is not None:
            rasdaman_strs.append("user='%s'" % location.getUser())

        if location.getPassword() is not None:
            rasdaman_strs.append(
                "password='%s'" % location.getPassword()
            )
        
        
        if location.getOID():
            rasdaman_strs.append(
                "query='select ( a [$x_lo:$x_hi,$y_lo:$y_hi] ) from %s as a where oid(a)=%f'" %\
                (location.getCollection(), location.getOID())
                
            )
        else:
            rasdaman_strs.append(
                "query='select ( a [$x_lo:$x_hi,$y_lo:$y_hi] ) from %s as a'" % location.getCollection()
            )
        
        return " ".join(rasdaman_strs)

    def _validate_record(self, record):
        # check if the model record points to a rasdaman array data package.
        
        if record.data_package_type != "rasdaman":
            raise InternalError(
                "Cannot assign '%s' type data package record to rasdaman data package." %\
                record.data_package_type
            )
            
    def _set_record(self, record):
        # be sure to set the model record to a :class:`RasdamanDataPackage`
        # instance
        
        if isinstance(record, RasdamanDataPackage):
            self.record = record
        else:
            self.record = record.rasdamandatapackage
    
    def _get_query_set(self, query):
        return RasdamanDataPackage.objects.filter(**query)

    def _create_record(self):
        # create a :class:`RasdamanDataPackage` model record.
        
        if self.metadata_location:
            metadata_location_record = self.metadata_location.getRecord()
        else:
            metadata_location_record = None
        
        self.record = RasdamanDataPackage.objects.create(
            data_package_type = RasdamanDataPackage.DATA_PACKAGE_TYPE,
            data_location = self.location.getRecord(),
            metadata_location = metadata_location_record,
            metadata_format_name = self.metadata_format_name
        )
        
    def _prepare_metadata_access(self):
        # nothing to be done here; metadata is expected to reside on the local
        # file system
        
        pass
    
    def _get_accessible_metadata_location(self):
        # return the location of the metadata file on the local file system
        
        return self.getMetadataLocation()
    
    def _post_metadata_access(self):
        # nothing to be done here
        
        pass

RasdamanDataPackageWrapperImplementation = \
DataPackageInterface.implement(RasdamanDataPackageWrapper)

#-------------------------------------------------------------------------------
# Tile index wrapper
#-------------------------------------------------------------------------------


class TileIndexWrapper(RecordWrapper):
    """
    This class wraps a tile index. It inherits from
    :class:`~.RecordWrapper`.
    
    .. method:: initialize(**kwargs)
    
       Apart from the mandatory ``record`` keyword argument, this method accepts
       a ``storage_dir`` argument which will be saved as instance attribute.
       An :exc:`~.InternalError` will be raised if neither of the two is given.
       The ``storage_dir`` denotes the path to the local directory where to
       find a tile index shape file as well as the actual tiles (usually
       stored in a directory tree under that directory).
    """
    
    REGISTRY_CONF = {
        "name": "Tile Index Wrapper",
        "impl_id": "resources.coverages.data.TileIndexWrapper",
        "factory_ids": (
            "resources.coverages.data.TileIndexFactory",
        )
    }
    
    def __init__(self):
        super(TileIndexWrapper, self).__init__()
        
        self.storage_dir = None

    def getSourceFormat(self): 
        """
        Return the source data file format. 
        """
        # TODO: implement proper source format for tile arrays 
        return "image/tiff"
    
    def getType(self):
        """
        Returns ``"index"``.
        """
        
        return "index"
    
    
    def getDataStructureType(self):
        """
        Returns ``"index"``.
        """
        
        return "index"
    
    def getStorageDir(self):
        """
        Returns the path to the directory where to find the tile index shape
        file as well as the actual tiles.
        """
        
        if self.record:
            return self.record.storage_dir
        else:
            return self.storage_dir
    
    def getShapeFilePath(self):
        """
        Returns the path to the tile index shape file.
        """
        
        return os.path.join(self.getStorageDir(), "tindex.shp")
    
    def _validate_record(self, record):
        if not isinstance(record, TileIndex):
            raise InternalError(
                "Cannot assign '%s' record to tile index wrapper." %\
                record.__class__.__name__
            )
    
    # use default _set_record implementation
    
    def _validate_attrs(self, **kwargs):
        if "storage_dir" not in kwargs:
            raise InternalError(
                "'storage_dir' keyword arguments needed to initialize tile index."
            )
    
    def _set_attrs(self, **kwargs):
        self.storage_dir = kwargs["storage_dir"]
    
    def _fetch_unique_record(self):
        # no uniqueness constraints apply
        
        return None
    
    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "storage_dir" in query:
            query["storage_dir"] = self.getStorageDir()
        
        return query
    
    def _get_query_set(self, query):
        return TileIndex.objects.filter(**query)
    
    def _create_record(self):
        self.record = TileIndex.objects.create(storage_dir = self.storage_dir)

TileIndexWrapperImplementation = \
TileIndexInterface.implement(TileIndexWrapper)

#-------------------------------------------------------------------------------
# Factories
#-------------------------------------------------------------------------------

class DataSourceFactory(RecordWrapperFactory):
    """
    This is a factory for :class:`DataSourceWrapper` objects. It inherits from
    :class:`~.RecordWrapperFactory`.
    """
    REGISTRY_CONF = {
        "name": "Data Source Factory",
        "impl_id": "resources.coverages.data.DataSourceFactory",
        "binding_method": "direct"
    }
    
    def _get_record_by_pk(self, pk):
        return DataSource.objects.get(pk=pk)
    
    def _get_record_wrapper(self, record):
        wrapper = DataSourceWrapper()
        wrapper.setRecord(record)
        
        return wrapper

DataSourceFactoryImplementation = \
RecordWrapperFactoryInterface.implement(DataSourceFactory)

class DataPackageFactory(RecordWrapperFactory):
    """
    This factory gives access to data package wrappers. It inherits from
    :class:`~.RecordWrapperFactory`.
    """
    
    REGISTRY_CONF = {
        "name": "Data Package Factory",
        "impl_id": "resources.coverages.data.DataPackageFactory",
        "binding_method": "direct"
    }

    def _get_record_by_pk(self, pk):
        return DataPackage.objects.get(pk=pk)
    
    def _get_record_wrapper(self, record):
        wrapper = self.impls[record.data_package_type]()
        wrapper.setRecord(record)
        
        return wrapper
                
DataPackageFactoryImplementation = \
RecordWrapperFactoryInterface.implement(DataPackageFactory)

class TileIndexFactory(RecordWrapperFactory):
    """
    This is a factory for :class:`TileIndexWrapper` objects. It inherits from
    :class:`~.RecordWrapperFactory`.
    """
    
    REGISTRY_CONF = {
        "name": "Tile Index Factory",
        "impl_id": "resources.coverages.data.TileIndexFactory",
        "binding_method": "direct"
    }
    
    def _get_record_by_pk(self, pk):
        return TileIndex.objects.get(pk=pk)
        
    def _get_record_wrapper(self, record):
        wrapper = TileIndexWrapper()
        wrapper.setRecord(record)
        
        return wrapper

TileIndexFactoryImplementation = \
RecordWrapperFactoryInterface.implement(TileIndexFactory)
