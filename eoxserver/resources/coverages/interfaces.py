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
This module contains the definition of coverage and dataset series
interfaces. These provide a harmonized interface to coverage data that
can be stored in different formats and has different types.
"""

from datetime import datetime

from django.contrib.gis.geos import GEOSGeometry

from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface
from eoxserver.core.resources import ResourceInterface
from eoxserver.resources.coverages.rangetype import RangeType

#-----------------------------------------------------------------------
# Abstract Interface Definitions
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
       * ``eo.ref_stitched_mosaic``
    
    .. method:: getSize
    
       This method shall return the size of the coverage wrapped by the
       implementation. The return value is expected to be a 2-tuple
       of integers ``(xsize, ysize)``.
       
    .. method:: getRangeType
    
       This method shall return a :class:`~.RangeType` instance
       containing the data type and band structure of the coverage
       wrapped by the implementation
    
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
    
    getLayerMetadata = Method(
        returns=ListArg("@return", arg_class=tuple)
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

class ReferenceableGridInterface(RegisteredInterface):
    """
    This interface defines methods for access to referenceable grid
    information.
    
    .. note:: the design of this interface is still TBD
    
    :Interface ID: resources.coverages.interfaces.ReferenceableGrid
    """
    
    REGISTRY_CONF = {
        "name": "Referenceable Grid Interface (mix-in for coverages)",
        "intf_id": "resources.coverages.interfaces.ReferenceableGrid"
    }
    
    pass # TODO: methods for access to referenceable grid information
    
class DatasetInterface(RegisteredInterface):
    """
    This interface shall wrap Datasets that are stored in data
    packages together with metadata and quicklooks.
    
    :Interface ID: resources.coverages.interfaces.Dataset
    
    .. method:: getFilename

       This method shall return the file name of the dataset wrapped by
       the implementation
    
    .. method:: getQuicklookPath

       This method shall return the path to the quicklook of a dataset
       wrapped by the implementation. In case there is no quicklook
       defined the empty string shall be returned.
    
    .. method:: getMetadataPath
    
       This method shall return the path to the metadata file of the
       dataset wrapped by the implementation

    .. method:: getMetadataFormat

       This method shall return the name of the format of the metadata
       file associated with the dataset.

    """
    
    REGISTRY_CONF = {
        "name": "Dataset Interface",
        "intf_id": "resources.coverages.interfaces.Dataset"
    }
    
    getFilename = Method(
        returns=StringArg("@return")
    )
    
    getQuicklookPath = Method(
        returns=StringArg("@return")
    )
    
    getMetadataPath = Method(
        returns=StringArg("@return")
    )
    
    getMetadataFormat = Method(
        returns=StringArg("@return")
    )

class TileIndexInterface(RegisteredInterface):
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
        "intf_id": "resources.coverages.interfaces.TileIndex"
    }
    
    getShapeFilePath = Method(
        returns=StringArg("@return")
    )

class EOMetadataInterface(RegisteredInterface):
    """
    This is the interface for EO Coverage subtypes as defined by the
    Earth Observation Application Profile for WCS 2.0. It should not be
    implemented directly; you'd rather use its descendants.
    
    :Interface ID: resources.coverages.interfaces.EOMetadata
    
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
       value is expected to be ``django.contrib.gis.geos.GEOSGeometry``
    
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
        "name": "EO Coverage Interface",
        "intf_id": "resources.coverages.interfaces.EOMetadata"
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
    
    getWGS84Extent = Method(
        returns=ObjectArg("@return", arg_class=tuple)
    )
    
    getEOGML = Method(
        returns=StringArg("@return")
    )

class EOCoverageInterface(CoverageInterface, EOMetadataInterface):
    """
    This interface is the base interface for implementations of EO
    Coverages according to the WCS 2.0 EO-AP. It is not intended to
    be implemented directly; rather one of its descendants shall
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
       Series) with resource primary key ``res_id``, ``False``
       otherwise.
    
    .. method:: contains(res_id)
    
       This method shall return ``True`` if the EO coverage is a
       container object and contains the coverage with resource
       primary key ``res_id``, ``False`` otherwise.
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
        IntArg("res_id"),
        returns=BoolArg("@return")
    )
    
    contains = Method(
        IntArg("res_id"),
        returns=BoolArg("@return")
    )
    
class EODatasetInterface(EOCoverageInterface, DatasetInterface):
    """
    This is the base interface for EO Dataset implementations according
    to WCS 2.0 EO-AP. It is not intended to be implemented directly;
    rather one of its descendants shall be used. It inherits from
    :class:`~.EOCoverageInterface` and :class:`~.DatasetInterface`.
    
    :Interface ID: resources.coverages.interfaces.EODataset
    """
    REGISTRY_CONF = {
        "name": "EO Dataset Interface",
        "intf_id": "resources.coverages.interfaces.EODataset"
    }

class RectifiedDatasetInterface(EODatasetInterface, RectifiedGridInterface):
    """
    This class is intended for implementations of RectifiedDataset
    objects according to the WCS 2.0 EO-AP. It inherits from
    :class:`~.EODatasetInterface` and :class:`~.RectifiedGridInterface`.
    
    :Interface ID: resources.coverages.interfaces.RectifiedDataset
    """
    REGISTRY_CONF = {
        "name": "Rectified Dataset Interface",
        "intf_id": "resources.coverages.interfaces.RectifiedDataset"
    }

class ReferenceableDatasetInterface(EODatasetInterface, ReferenceableGridInterface):
    """
    This class is intended for implementations of RectifiedDataset
    objects according to the WCS 2.0 EO-AP. It inherits from
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
    
    .. method:: addCoverage(res_type, res_id)
    
       Add resource with type ``res_type`` and primary key ``res_id``
       to container.
    
    .. method:: removeCoverage(res_type, res_id)
    
       Remove resource with type ``res_type`` and primary key
       ``res_id``
    
    .. method:: getDataDirs
    
       This method shall return a list of directories which hold the
       dataset series data.
    
    .. method:: getImagePattern
    
       This method shall return the filename pattern for image files
       to be included in the dataset series.
    """
    
    REGISTRY_CONF = {
        "name": "Container Interface",
        "intf_id": "resources.coverages.interfaces.Container"
    }
    
    addCoverage = Method(
        StringArg("res_type"),
        IntArg("res_id")
    )
    
    removeCoverage = Method(
        StringArg("res_type"),
        IntArg("res_id")
    )
    
    getDataDirs = Method(
        returns=ListArg("@return")
    )
    
    getImagePattern = Method(
        returns=StringArg("@return")
    )

class RectifiedStitchedMosaicInterface(EOCoverageInterface, RectifiedGridInterface, ContainerInterface, TileIndexInterface):
    """
    This class is intended for implementations of Rectified Stitched
    Mosaic objects according to WCS 2.0 EO-AP. It inherits from
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

class DatasetSeriesInterface(ResourceInterface, EOMetadataInterface):
    """
    This interface is intended for implementations of Dataset Series
    according to the WCS 2.0 EO-AP. It inherits from 
    :class:`~.ResourceInterface` and :class:`~.EOMetadataInterface`.
    
    :Interface ID: resources.coverages.interfaces.DatasetSeries
    
    .. method:: getEOCoverages(filter_exprs=None)

       This method shall return a list of EOCoverage wrappers for the
       datasets and stitched mosaics contained in the dataset series
       wrapped by the implementation. The optional ``filter_exprs``
       argument is expected to be a list of filter expressions to be
       applied to the datasets or ``None``. In case no contained dataset
       matches the filter expressions an empty list shall be returned.

    .. method:: contains(res_id)
    
       This method shall return ``True`` if the EO Coverage with
       resource primary key ``res_id`` is contained in the Dataset
       Series, ``False`` otherwise.
    

    """
    REGISTRY_CONF = {
        "name": "Dataset Series Interface",
        "intf_id": "resources.coverages.interfaces.DatasetSeries"
    }
        

    getEOCoverages = Method(
        ListArg("filter_exprs", default=None),
        returns=ListArg("@return")
    )
    
    contains = Method(
        IntArg("res_id"),
        returns=BoolArg("@return")
    )
