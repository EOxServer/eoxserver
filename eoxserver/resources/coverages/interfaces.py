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

"""
This module contains the definition of coverage and dataset series
interfaces. These provide a harmonized interface to coverage data that
can be stored in different formats and has different types.
"""

from datetime import datetime

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface
from eoxserver.core.records import RecordWrapperInterface
from eoxserver.core.resources import ResourceInterface
from eoxserver.resources.coverages.rangetype import RangeType

#-----------------------------------------------------------------------
# Data Interfaces
#-----------------------------------------------------------------------

class DataSourceInterface(RegisteredInterface):
    """
    This interface shall be implemented by Data Sources. They represent
    locations where information about a collection of Data Packages
    can be retrieved.
    
    .. method:: detect
    
       This method shall return a list of Data Packages, i.e. objects
       implementing :class:`DataPackageInterface`, related to the
       Data Source.
       
    .. method:: contains
    
       This method shall return ``True`` if a data source references
       a dataset, ``False`` otherwise.
    
    """
    
    REGISTRY_CONF = {
        "name": "Data Source Interface",
        "intf_id": "backends.interfaces.DataSource",
        "binding_method": "factory"
    }
    
    detect = Method(
        returns = ListArg("@return")
    )
    
    contains = Method(
        ObjectArg("wrapper"),
        returns = BoolArg("@return")
    )

class CoverageDataInterface(RecordWrapperInterface):
    """
    This is the common base interface for coverage data.
    
    ..
    
    .. method:: getDataStructureType
    
       This method shall return a string denoting the data structure
       type of the data.
    """
    
    REGISTRY_CONF = {
        "name": "Coverage Data Interface",
        "intf_id": "resources.coverages.interfaces.CoverageData",
        "binding_method": "factory"
    }
    
    getDataStructureType = Method(
        returns = StringArg("@return")
    )

class DataPackageInterface(CoverageDataInterface):
    """
    This interface shall be implemented by Data Packages. Data Packages
    provide an abstraction layer for various kinds of file-based or
    database-based datasets. Internally, data packages store information
    about the location of the original data and (for remote backends) the
    location of a locally accessible copy.
    
    Methods for high-level data access:

    .. method:: open
    
       This method shall open the data package. It shall return an
       object representing the underlying dataset in the engine
       defined by the data format of the data package.
       
    .. method:: getLocation
    
       Returns the location of the data, i.e. an object that implements
       :class:`~.LocationInterface`. Note that this location is not necessarily
       directly accessible from the local file system or operating system, but
       may be remote. For fetching an accessible location, see
       :meth:`prepareAccess` and :meth:`getAccessibleLocation`.
    
    .. method:: getMetadataLocation
    
       Returns the location of the metadata, i.e. an object that implements
       :class:`~.LocationInterface`.
    
    .. method:: readGeospatialMetadata(default_srid=None)
    
       This method shall return an object containing the geospatial
       metadata stored with the data package. It accepts an optional
       ``default_srid`` parameter which indicates the SRID to use if it cannot
       be read from the data package.
    
    .. method:: readEOMetadata
    
       This method shall return an object containing the EO metadata
       required by EOxServer and stored with the data package.
       
    Methods for low-level data access; use these with care:
    
    .. method:: prepareAccess
    
       This method has to be called before any attempt to actually
       access the data. It shall prepare access, e.g. by retrieving
       remote data or unpacking complex packages, so that subsequent
       calls to :meth:`getAccessibleLocation` and
       :meth:`getAccessiblePath` can return meaningful results. It
       shall raise :exc:`~.DataAccessError` in case of an error.
       
    .. method:: getAccessibleLocation
    
       This method shall return a location, i.e. an object implementing
       :class:`LocationInterface`. An :exc:`InternalError` shall be
       raised if the data package is not accessible (e.g. because
       :meth:`prepareAccess` has not been called or the call failed)
       
    .. method:: getGDALDatasetIdentifier
    
       This method shall return a string to be used to open the data package
       in GDAL. It shall raise :exc:`~.InternalError` if the data package
       cannot be opened in GDAL.
    
    """
    REGISTRY_CONF = {
        "name": "Data Package Interface",
        "intf_id": "resources.coverages.interfaces.DataPackage",
        "binding_method": "factory"
    }
    
    getType = Method(
        returns = StringArg("@return")
    )
    
    open = Method(
        returns = ObjectArg("@return")
    )

    getLocation = Method(
        returns = ObjectArg("@return")
    )
    
    getMetadataLocation = Method(
        returns = ObjectArg("@return")
    )
    
    getCoverages = Method(
        returns = ListArg("@return")
    )
    
    readGeospatialMetadata = Method(
        IntArg("default_srid", default=None),
        returns = ObjectArg("@return")
    )
    
    readEOMetadata = Method(
        returns = ObjectArg("@return")
    )
    
    prepareAccess = Method()

    getAccessibleLocation = Method(
        returns = ObjectArg("@return")
    )
    
    getGDALDatasetIdentifier = Method(
        returns = StringArg("@return")
    )


class TileIndexInterface(CoverageDataInterface):
    """
    This interface provides the methods necessary to access tile index
    information for coverages.
    
    :Interface ID: resources.coverages.interfaces.TileIndex
    
    .. method:: getShapeFilePath
    
       This method shall return the path to the shape file that holds
       information about the tiles the coverage is split up into.
    """
    REGISTRY_CONF = {
        "name": "Tile Index Interface",
        "intf_id": "resources.coverages.interfaces.TileIndex",
        "binding_method": "factory"
    }
    
    getShapeFilePath = Method(
        returns=StringArg("@return")
    )

#-------------------------------------------------------------------------------
# Metadata Interfaces
#-------------------------------------------------------------------------------
    
class MetadataFormatInterface(RegisteredInterface):
    """
    This is a (very basic) interface for metadata formats. So far, it defines
    only one method:
    
    .. method:: getName
    
       This method shall return the name of the format.

    .. method:: getMetadataKeys
    
       This method shall return a list of metadata keys that are known to the
       metadata format
       
    .. method:: getMetadataValues(keys, raw_metadata)
    
       This method shall return a dictionary of metadata keys and values. The
       dictionary keys shall correspond to the keys conveyed with the request,
       the dictionary values shall be the respective metadata values, or
       ``None`` if the key is not known or no metadata value is defined for the
       specific metadata instance.
       
       The ``raw_metadata`` argument shall point to the raw metadata input.
       The method shall raise :exc:`~.InternalError` if the format cannot
       decode the raw metadata content, e.g. because it is in the wrong data
       format.
    """
    
    REGISTRY_CONF = {
        "name": "Metadata Format Interface",
        "intf_id": "resources.coverages.interfaces.MetadataFormat",
        "binding_method": "testing"
    }
    
    getName = Method(
        returns = StringArg("@return")
    )
    
    getMetadataKeys = Method(
        returns = ListArg("@return")
    )
    
    getMetadataValues = Method(
        ListArg("keys"),
        Arg("raw_metadata"),
        returns = DictArg("@return")
    )
    
class EOMetadataFormatInterface(MetadataFormatInterface):
    """
    This interface is intended for EO metadata formats and extends
    :class:`MetadataFormatInterface`.
    
    .. method:: getEOMetadata(raw_metadata)
    
       This method shall decode the raw metadata passed to it and return an
       EO Metadata object, i.e. an implementation of
       :class:`EOMetadataInterface`.
       
       The method shall raise :exc:`~.InternalError` if the format cannot
       decode the raw metadata content, e.g. because it is in the wrong data
       format.
    """
    
    REGISTRY_CONF = {
        "name": "EO Metadata Format Interface",
        "intf_id": "resources.coverages.interfaces.EOMetadataFormat"
    }
    
    getEOMetadata = Method(
        Arg("raw_metadata"),
        returns = ObjectArg("@return")
    )

class GenericMetadataInterface(RegisteredInterface):
    """
    This is an interface for objects containing metadata of any kind. They can
    be retrieved using a key-value-pair schema.
    
    .. method:: getMetadataFormat
    
       This method shall return the metadata format, i.e. an object implementing
       :class:`MetadataFormatInterface`.
       
    .. method:: getMetadataKeys
    
       This method shall return a list of metadata keys that are understood by
       the metadata interface.
       
    .. method:: getMetadataValues(keys)
    
       This method shall return a dictionary of metadata keys and values. The
       dictionary keys shall correspond to the keys conveyed with the request,
       the dictionary values shall be the respective metadata values, or
       ``None`` if the key is not known or no metadata value is defined for the
       specific metadata instance.
    """
    
    REGISTRY_CONF = {
        "name": "Metadata Interface",
        "intf_id": "resources.coverages.interfaces.Metadata",
        "binding_method": "direct"
    }
    
    getMetadataFormat = Method(
        returns = ObjectArg("@return")
    )

    getMetadataKeys = Method(
        returns = ListArg("@return")
    )
    
    getMetadataValues = Method(
        ListArg("keys"),
        returns = DictArg("@return")
    )
    
    getRawMetadata = Method(
        returns = StringArg("@return")
    )

class EOMetadataInterface(RegisteredInterface):
    """
    This an interface for objects carrying basic EO Metadata. It is the base
    for metadata reader interfaces as well as EO-WCS object interfaces. Note
    that it does NOT inherit from :class:`MetadataInterface`, so key-value-pair
    access to metadata values is not possible.
    
    .. method:: getEOID
    
       This method shall return the EO ID of the coverage wrapped by the
       implementation
    
    .. method:: getBeginTime
    
       This method shall return the acquisition begin date and time of
       the EO coverage wrapped by the implementation. The type of the
       return value is expected to be :class:`datetime.datetime`.

    .. method:: getEndTime

       This method shall return the acquisition end date and time of the
       EO coverage wrapped by the implementation. The type of the return
       value is expected to be :class:`datetime.datetime`.
    
    .. method:: getFootprint

       This method shall return the acquisition footprint of the EO
       coverage wrapped by the implementation. The type of the return
       value is expected to be :class:`django.contrib.gis.geos.GEOSGeometry`.
    
    """
    
    REGISTRY_CONF = {
        "name": "EO Metadata Interface",
        "intf_id": "resources.coverages.interfaces.EOMetadata",
        "binding_method": "direct"
    }
    
    getEOID = Method(
        returns=StringArg("@return")
    )

    getBeginTime = Method(
        returns=ObjectArg("@return", arg_class=datetime)
    )
    
    getEndTime = Method(
        returns=ObjectArg("@return", arg_class=datetime)
    )
    
    getFootprint = Method(
        returns=ObjectArg("@return", arg_class=GEOSGeometry)
    )

class GenericEOMetadataInterface(GenericMetadataInterface, EOMetadataInterface):
    """
    An interface combining generic and EO metadata access. Inherits from
    :class:`MetadataInterface` and :class:`EOMetadataInterface`.
    """
    REGISTRY_CONF = {
        "name": "Generic EO Metadata Interface",
        "intf_id": "resources.coverages.interfaces.GenericEOMetadata"
    }

class EOMetadataReaderInterface(RegisteredInterface):
    """
    This interfaces shall be implemented by objects that can read EO Metadata
    sources and translate them to EO Metadata objects. Implementations can be
    found in the registry by key-value-pair matching. The interface defines two
    registry keys:
    
    * ``resources.coverages.interfaces.location_type``: the type of the
      location, e.g. ``local`` (this is two abstract from file or catalogue
      record access)
    * ``resources.coverages.interfaces.encoding_type``: the way how the
      metadata was encoded; most common are XML encoding in a metadata file or
      catalogue record and metadata tags in a data file
    
    .. method:: readEOMetadata(location)
    
       This method shall read the object at the given ``location`` and return
       the decoded EO Metadata found in it. It shall raise
       :exc:`~.InternalError` if the location or encoding type do not match the
       implementation specification or :exc:`~.DataAccessError` if the
       underlying resource cannot be accessed.
    """
    
    REGISTRY_CONF = {
        "name": "EO Metadata Reader Interface",
        "intf_id": "resources.coverages.interfaces.EOMetadataReader",
        #"binding_method": "kvp",
        "binding_method": "testing",
        "registry_keys": (
            "resources.coverages.interfaces.location_type",
            "resources.coverages.interfaces.encoding_type"
        )
    }

    readEOMetadata = Method(
        ObjectArg("location"),
        returns = ObjectArg("@return")
    )

#-----------------------------------------------------------------------
# Coverage and Dataset Series Interfaces
#-----------------------------------------------------------------------

class CoverageInterface(ResourceInterface):
    """
    The parent class of all coverage interfaces. It defines methods for
    access to coverage data. It inherits from
    :class:`~.ResourceInterface`.
    
    :Interface ID: resources.coverages.interfaces.Coverage
    
    .. method:: getCoverageId
    
       This method shall return the coverage id of the coverage resource
       wrapped by the implementation
    
    .. method:: getCoverageSubtype
    
       This method shall return the GML coverage subtype of the coverage
       resource wrapped by the implementation
       
    .. method:: getType
    
       This method shall return the EOxServer coverage type of the
       coverage wrapped by the implementation. Current choices are:
    
       * ``file``
       * ``eo.rect_dataset``
       * ``eo.ref_dataset``
       * ``eo.rect_stitched_mosaic``
    
    .. method:: getSize
    
       This method shall return the size of the coverage wrapped by the
       implementation. The return value is expected to be a 2-tuple
       of integers ``(xsize, ysize)``.
       
    .. method:: getRangeType
    
       This method shall return a :class:`~.RangeType` instance
       containing the data type and band structure of the coverage
       wrapped by the implementation
    
    .. method:: getDataStructureType
    
       This method shall return the type of the data structure that contains the
       coverage's data. See :meth:`CoverageDataInterface.getDataStructureType`.
       Note that this does not define the implementation of the coverage data
       object returned with :meth:`getData`.
    
    .. method:: getData
    
       This method shall return an object that provides access to the coverage
       data, i.e. an implementation of :class:`CoverageDataInterface`.
    
    .. method:: getLayerMetadata
    
       This method shall return a list containing 2-tuples of MapServer
       metadata key-value-pairs that will be tagged on the MapServer
       layer representing this coverage.
    """
    
    REGISTRY_CONF = {
        "name": "Coverage Interface",
        "intf_id": "resources.coverages.interfaces.Coverage"
    }


    getCoverageId = Method(
        returns=StringArg("@return")
    )
    
    getCoverageSubtype = Method(
        returns=StringArg("@return")
    )

    getType = Method(
        returns=StringArg("@return")
    )

    getSize = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )
    
    getRangeType = Method(
        returns=ObjectArg("@return", arg_class=RangeType)
    )
    
    getDataStructureType = Method(
        returns=StringArg("@return")
    )
    
    getData = Method(
        returns=ObjectArg("@return")
    )
    
    getLayerMetadata = Method(
        returns=ListArg("@return", arg_class=tuple)
    )
    
    matches = Method(
        ListArg("filter_exprs"),
        returns=BoolArg("@return")
    )

class RectifiedGridInterface(RegisteredInterface):
    """
    This interface defines methods to access rectified grid information,
    namely the coordinate reference system ID and the geographical
    extent of the coverage. It is intended to be used as mix-in for
    coverage interfaces.
    
    :Interface ID: resources.coverages.interfaces.RectifiedGrid
    
    .. method:: getSRID
    
       This method shall return the EPSG SRID of the coverage's
       coordinate reference system (CRS)
    
    .. method:: getExtent
    
       This method shall return the extent of the coverage wrapped by
       the implementation. The return value is expected to be a 4-tuple
       of floating point coordinates (minx, miny, maxx, maxy) expressed
       in the CRS described by the SRID returned with :meth:`getSRID`.
    """
    
    REGISTRY_CONF = {
        "name": "Rectified Grid Interface (mix-in for coverages)",
        "intf_id": "resources.coverages.interfaces.RectifiedGrid"
    }
    
    getSRID = Method(
        returns=IntArg("@return")
    )
        
    getExtent = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )
    
    getResolution = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )

class ReferenceableGridInterface(RegisteredInterface):
    """
    This interface defines methods for access to referenceable grid
    information.
    
    :Interface ID: resources.coverages.interfaces.ReferenceableGrid

    .. method:: getSRID
    
       This method shall return the EPSG SRID of the coordinate reference 
       system (CRS) of the coverages tie-points. 
    
    .. method:: getExtent
    
       This method shall return the extent of the coverage wrapped by
       the implementation. The return value is expected to be a 4-tuple
       of floating point coordinates (minx, miny, maxx, maxy) expressed
       in the CRS described by the SRID returned with :meth:`getSRID`.
    """
    
    REGISTRY_CONF = {
        "name": "Referenceable Grid Interface (mix-in for coverages)",
        "intf_id": "resources.coverages.interfaces.ReferenceableGrid"
    }
    
    getSRID = Method(
        returns=IntArg("@return")
    )
        
    getExtent = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )
    

class EOWCSObjectInterface(EOMetadataInterface):
    """
    This is the interface for EO Coverage subtypes as defined by the
    Earth Observation Application Profile for WCS 2.0. It inherits from
    :class:`EOMetadataInterface`. It should not be implemented directly; you'd
    rather use its descendants.
    
    .. method:: getWGS84Extent
    
       This method shall return the WGS 84 extent of the EO coverage
       wrapped by the implementation. The return value shall be a 4-tuple
       of floating point coordinates (minlon, minlat, maxlon, maxlat)
       given in the WGS 84 coordinate system (EPSG:4326).

    .. method:: getEOGML

       This method shall return the EO GML (EO O&M) conformant metadata
       stored with the EO coverage. If no EO O&M metadata is available,
       the empty string will be returned

    """
    
    REGISTRY_CONF = {
        "name": "Interface for EO-WCS Objects",
        "intf_id": "resources.coverages.interfaces.EOWCSObject"
    }

    getWGS84Extent = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )
    
    getEOGML = Method(
        returns=StringArg("@return")
    )

class EOCoverageInterface(CoverageInterface, EOWCSObjectInterface):
    """
    This interface is the base interface for implementations of EO
    Coverages according to the WCS 2.0 EO-AP (EO-WCS). It inherits from
    :class:`CoverageInterface` and class:`EOWCSObjectInterface`. It is not
    intended to be implemented directly; rather one of its descendants shall
    be used.
    
    :Interface ID: resources.coverages.interfaces.EOCoverage
    
    .. method:: getEOCoverageSubtype
    
       This method shall return the EO coverage subtype of the coverage
       wrapped by the implementation
       
    .. method:: getDatasets(filter_exprs=None)
    
       This method shall return a list of dataset wrappers for the
       datasets contained in the coverage wrapped by the implemention.
       The optional ``filter_exprs`` argument is expected to be a list
       of filter expressions to be applied to the datasets or ``None``.
       In case no contained dataset matches the filter expressions an
       empty list shall be returned.
    
       In case of atomic coverages which do not contain any datasets
       (e.g. RectifiedDatasets themselves) a list containing the
       coverage wrapper itself shall be returned. In case filter
       expressions are provided with the call these shall be applied;
       if the coverage does not match them an empty list shall be
       returned.
    
    .. method:: getLineage
    
       This method shall return the content of the lineage object stored
       with the EO coverage wrapped by the implementation. Note that this
       element is not yet specified in detail in the specification at
       the moment (2011-05-26). If no lineage is available, None shall
       be returned.
    
    .. method:: getContainers
    
       This method shall return a list of container wrappers (Stitched
       Mosaic or Dataset Series wrappers) the coverage is contained in.
       The empty list shall be returned if the coverage is not related
       to any container object.
       
    .. method:: getContainerCount
    
       This method shall return the number of container objects the
       EO Coverage is contained in.
    
    .. method:: containedIn(res_id)
    
       This method shall return ``True`` if the EO coverage is
       contained in the container object (Stitched Mosaic or Dataset
       Series) specified by the ``wrapper``, ``False`` otherwise.
    
    .. method:: contains(res_id)
    
       This method shall return ``True`` if the EO coverage is a
       container object and contains the coverage with resource
       specified by the ``wrapper``, ``False`` otherwise.
    """
    REGISTRY_CONF = {
        "name": "EO Coverage Interface",
        "intf_id": "resources.coverages.interfaces.EOCoverage"
    }


    getEOCoverageSubtype = Method(
        returns=StringArg("@return")
    )

    getDatasets = Method(
        ListArg("filter_exprs", default=None),
        returns=ListArg("@return")
    )
    
    getLineage = Method(
        returns=ObjectArg("@return")
    )
    
    getContainers = Method(
        returns=ListArg("@return")
    )
    
    getContainerCount = Method(
        returns=IntArg("@return")
    )
    
    containedIn = Method(
        ObjectArg("wrapper"),
        returns=BoolArg("@return")
    )
    
    contains = Method(
        ObjectArg("wrapper"),
        returns=BoolArg("@return")
    )

class RectifiedDatasetInterface(EOCoverageInterface, RectifiedGridInterface):
    """
    This class is intended for implementations of RectifiedDataset
    objects according to the WCS 2.0 EO-AP (EO-WCS). It inherits from
    :class:`~.EODatasetInterface` and :class:`~.RectifiedGridInterface`.
    
    :Interface ID: resources.coverages.interfaces.RectifiedDataset
    """
    REGISTRY_CONF = {
        "name": "Rectified Dataset Interface",
        "intf_id": "resources.coverages.interfaces.RectifiedDataset"
    }

class ReferenceableDatasetInterface(EOCoverageInterface, ReferenceableGridInterface):
    """
    This class is intended for implementations of RectifiedDataset
    objects according to the WCS 2.0 EO-AP (EO-WCS). It inherits from
    :class:`~.EODatasetInterface` and
    :class:`ReferenceableGridInterface`.

    .. note:: the design of this interface is still TBD
    
    :Interface ID: resources.coverages.interfaces.ReferenceableDataset
    
    """
    REGISTRY_CONF = {
        "name": "Referenceable Dataset Interface",
        "intf_id": "resources.coverages.interfaces.ReferenceableDataset"
    }
    
class ContainerInterface(RegisteredInterface):
    """
    This is the common interface for coverages and series containing
    EO Coverages.
    
    .. method:: contains(wrapper)
    
       Returns a boolean value describing if the container contains the resource
       specified by the given ``wrapper``.
    
    .. method:: addCoverage(wrapper)
    
       Add resource specified by the given ``wrapper``.
    
    .. method:: removeCoverage(wrapper)
    
       Remove resource specified by the given ``wrapper``.
    
    .. method:: getDataSources
    
       This method shall return a list of data sources, i.e. objects
       implementing :class:`DataSourceInterface` for the given container.
       It is intended for use in
       :mod:`eoxserver.resources.coverages.synchronize`.
    """
    
    REGISTRY_CONF = {
        "name": "Container Interface",
        "intf_id": "resources.coverages.interfaces.Container"
    }
    
    contains = Method(
        ObjectArg("wrapper"),
        returns=BoolArg("@return")
    )
    
    addCoverage = Method(
        ObjectArg("wrapper")
    )
    
    removeCoverage = Method(
        ObjectArg("wrapper")
    )
    
    getDataSources = Method(
        returns=ListArg("@return")
    )

class RectifiedStitchedMosaicInterface(EOCoverageInterface, RectifiedGridInterface, ContainerInterface):
    """
    This class is intended for implementations of Rectified Stitched
    Mosaic objects according to WCS 2.0 EO-AP (EO-WCS). It inherits from
    :class:`~.EOCoverageInterface`, :class:`~.RectifiedGridInterface`
    and :class:`~.TileIndexInterface`.
    
    :Interface ID: resources.coverages.interfaces.RectifiedStitchedMosaic
    
    .. method:: getDataDirs:
    
       This method shall return a list of directories which hold the
       stitched mosaic data.

    .. method:: getImagePattern
    
       This method shall return the filename pattern for image files
       to be included in the stitched mosaic.
    """
    REGISTRY_CONF = {
        "name": "Rectified Stitched Mosaic Interface",
        "intf_id": "resources.coverages.interfaces.RectifiedStitchedMosaic"
    }

class DatasetSeriesInterface(ResourceInterface, EOWCSObjectInterface):
    """
    This interface is intended for implementations of Dataset Series
    according to the WCS 2.0 EO-AP (EO-WCS). It inherits from 
    :class:`~.ResourceInterface` and :class:`~.EOWCSObjectInterface`.
    
    :Interface ID: resources.coverages.interfaces.DatasetSeries
    
    .. method:: getType
    
       Shall return ``"eo.dataset_series"``.
    
    .. method:: getEOCoverages(filter_exprs=None)

       This method shall return a list of EOCoverage wrappers for the
       datasets and stitched mosaics contained in the dataset series
       wrapped by the implementation. The optional ``filter_exprs``
       argument is expected to be a list of filter expressions to be
       applied to the datasets or ``None``. In case no contained dataset
       matches the filter expressions an empty list shall be returned.
       
    .. method:: getDatasets(filter_exprs=None)
    
       This method shall return a list of RectifiedDataset and 
       ReferenceableDataset wrappers contained in the dataset series. The
       optional ``filter_exprs`` argument is expected to be a list of filter
       expressions to be applied to the datasets or ``None``. In case no
       contained dataset matches the filter expressions an empty list shall be
       returned.

    .. method:: contains(wrapper)
    
       This method shall return ``True`` if the EO Coverage specified by 
       ``wrapper`` is contained in the Dataset Series, ``False`` otherwise.
    
    """
    REGISTRY_CONF = {
        "name": "Dataset Series Interface",
        "intf_id": "resources.coverages.interfaces.DatasetSeries"
    }
    
    getType = Method(
        returns=StringArg("@return")
    )

    getEOCoverages = Method(
        ListArg("filter_exprs", default=None),
        returns=ListArg("@return")
    )
    
    getDatasets = Method(
        ListArg("filter_exprs", default=None),
        returns=ListArg("@return")
    )

    contains = Method(
        ObjectArg("wrapper"),
        returns=BoolArg("@return")
    )

class ManagerInterface(RegisteredInterface):
    """
    This is an interface for coverage and dataset series managers. These
    managers shall facilitate registration of data in the database providing an
    easy-to-use interface for application programmers.
    
    Managers are bound to a certain resource type, e.g. a DatasetSeries or a
    RectifiedStitchedMosaic. It suffices to have one manager per resource type
    as it can be invoked for many objects of this type.
    
    .. method:: acquireID(obj_id=None, fail=False)
    
       This method shall acquire a valid and unique object ID and return it.
       The caller can provide a suggestion ``obj_id``. In this case, the
       method shall try to acquire this object ID. The optional ``fail``
       argument determines what the method shall do in case it cannot acquire
       the given ``obj_id``. If it is set to ``True``, the method shall raise
       an exception, otherwise it shall degrade gracefully returning a newly
       generated object ID.
       
       The implementation should be able to guarantee that the acquired ID
       cannot be used by other threads of execution unless it is released
       and left unused. If it cannot assure this, the deviation shall be
       documented with a warning.
    
    .. method:: releaseID(obj_id)
    
       This method shall release an object ID ``obj_id`` that has been
       acquired with :meth:`acquireID` beforehand. In case the object ID has
       been left unused, it shall be free to be acquired again.
    
    .. method:: create(obj_id=None, **kwargs)
    
       This method shall create and return a coverage or dataset series wrapper
       from the attributes given in ``kwargs``. The actual range of keyword
       arguments accepted may depend on the resource type and the
       implementation.
       
       If the ``obj_id`` argument is omitted a new object ID shall be generated
       using the same mechanism as :meth:`acquireID`. If the provided object ID
       is invalid or already in use, appropriate exceptions shall be raised.
    
    .. method:: update(obj_id, **kwargs)
    
       This method shall update the coverage or dataset series with ID
       ``obj_id`` with new parameters provided as keyword arguments. The actual
       range of keyword arguments accepted may depend on the resource type and
       the implementation and should correlate with the arguments accepted by
       :meth:`create` as far as possible.
       
       The method shall return the updated coverage or dataset series wrapper.
       
       It shall raise :exc:`~.NoSuchCoverage` if there is no coverage or
       dataset series with ID ``obj_id``.
    
    .. method:: delete(obj_id)
    
       This method shall delete the coverage or dataset with ID ``obj_id``.
       
       It shall raise :exc:`~.NoSuchCoverage` if there is no coverage or
       dataset series with ID ``obj_id``.
    """
    REGISTRY_CONF = {
        "name": "Manager Interface for EO Objects",
        "intf_id": "resources.coverages.interfaces.Manager",
        "binding_method": "kvp",
        "registry_keys": (
            "resources.coverages.interfaces.res_type",
        )
    }
    
    create = Method(
        StringArg("obj_id", default=None),
        StringArg("request_id", default=None),
        KwArgs("kwargs"),
        returns = ObjectArg("@return")
    )
    
    update = Method(
        StringArg("obj_id"),
        DictArg("link"),
        DictArg("unlink"),
        DictArg("set"),
        returns = ObjectArg("@return")
    )
    
    delete = Method(
        StringArg("obj_id")
    )
    
    synchronize = Method(
        StringArg("obj_id")
    )
