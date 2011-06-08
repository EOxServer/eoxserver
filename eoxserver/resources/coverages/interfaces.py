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
import logging

from eoxserver.core.exceptions import (
    InternalError, InvalidParameterException, UnknownCRSException
)
from eoxserver.core.util.filetools import findFiles
from eoxserver.core.util.timetools import getDateTime
from eoxserver.resources.coverages.models import (
    SingleFileCoverageRecord, RectifiedDatasetRecord,
    RectifiedDatasetSeriesRecord, RectifiedStitchedMosaicRecord,
    RectifiedGridRecord
)
from eoxserver.resources.coverages.domainset import (
    RectifiedGrid, getGridFromFile
)
from eoxserver.resources.coverages.rangetype import (
    Channel, NilValue, getRangeTypeFromFile
)
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory
from eoxserver.resources.coverages.exceptions import (
    NoSuchCoverageException, NoSuchDatasetSeriesException
)


#-----------------------------------------------------------------------
# Abstract Interface Definitions
#-----------------------------------------------------------------------

class CoverageInterface(object):
    """
    The parent class of all coverage interfaces. It defines methods for
    access to coverage data.
    """
    def __init__(self, wcseo_object):
        self.wcseo_object = wcseo_object

    def getCoverageId(self):
        """
        Returns the coverage id.
        
        @return A string representing the coverage id
        """
        return None
    
    def getCoverageSubtype(self):
        """
        Returns the GML coverage subtype.
        
        @return A string representing the coverage subtype
        """
        return None
    
    def getEOCoverageSubtype(self):
        """
        Returns the EO coverage subtype.
        
        @return A string representing the EO coverage subtype
        """
        return None
    
    def getType(self):
        """
        Returns the EOxServer coverage type. Current choices are
        <ul>
        <li><tt>"file"</tt></li>
        <li><tt>"eo.rect_dataset"</tt></li>
        <li><tt>"eo.ref_dataset"</tt></li>
        <li><tt>"eo.rect_stitched_mosaic"</tt></li>
        <li><tt>"eo.ref_stitched_mosaic"</tt></li>
        </ul>
        
        @return A string representing the coverage type
        """
        return None

    def getDatasets(self, **kwargs):
        """
        Returns the EO datasets contained in this coverage; if this
        coverage is a dataself itself, returns a reference to this 
        coverage interface. If provided, the filenames are selected
        according to the keyword arguments included in the request; the
        specific behaviour depends on the type of coverage.
        
        @param  kwargs  keyword arguments for selection of datasets
        @return         a list of {@link eoxserver.lib.interfaces.EOxSDatasetInterface} objects
        """
        
        return None
    
    def getGrid(self):
        """
        Return the coverage's GML Grid information
        
        @return an {@link eoxserver.lib.domainset.EOxSRectifiedGrid} object
        """
        return None
    
    def getRangeType(self):
        """
        Return the GML RangeType information for the coverage
        
        @return a list of {@link eoxserver.lib.rangetype.EOxSChannel} objects
        """
        
        return None
    
    def getLayerMetadata(self):
        """
        Returns metadata key-value-pairs to configure
        the MapServer layer with.
        
        @return a list of tuples of metadata key-value-pairs
        """
        return None

class EOMetadataInterface(object):
    def getEOID(self):
        """
        Returns the EO ID of the EO Coverage or EO Dataset Series.
        
        @return a string representing the EO ID
        """
        return None

    def getBeginTime(self):
        """
        Returns the acquisition begin time of the EO Coverage or
        EO Dataset Series.
        
        @ return a <tt>datetime</tt> object representing the begin time
        """
        return None
        
    def getEndTime(self):
        """
        Returns the acquisition end time of the EO Coverage or
        EO Dataset Series.
        
        @ return a <tt>datetime</tt> object representing the end time
        """
        return None
        
    def getFootprint(self):
        """
        Returns the footprint of the EO Coverage or EO Dataset Series.
        
        @return a <tt>django.contrib.gis.geos.Polygon</tt> object
                containing the footprint
        """
        return None
    
    def getWGS84Extent(self):
        """
        Returns the extent of the EO Coverage or EO Dataset Series
        
        @return a 4-tuple of (minx, miny, maxx, maxy)
        """
        return None
        
    def getEOGML(self):
        """
        Returns the EO GML associated with the coverage
        
        @return a string containing the EO GML
        """
        return None
    
class DatasetInterface(CoverageInterface):
    def getFilename(self):
        return None
    
    def getQuicklookPath(self):
        return None
        
    def getMetadataPath(self):
        return None
    
    def getMetadataFormat(self):
        return None

class EODatasetInterface(DatasetInterface, EOMetadataInterface):
    def getLineage(self):
        return None

class StitchedMosaicInterface(CoverageInterface, EOMetadataInterface):
    def getLineage(self):
        return None
    
    def getShapeFilePath(self):
        return None

class DatasetSeriesInterface(EOMetadataInterface):
    def __init__(self, wcseo_object):
        self.wcseo_object = wcseo_object
    
    def getType(self):
        """
        Returns the dataset series type. Current choices are
        <ul>
        <li><tt>"eo.rect_dataset_series"</tt></li>
        <li><tt>"eo.ref_dataset_series"</tt></li>
        </ul>
        
        @return A string representing the dataset series type
        """
        return None
    
    def getDatasets(self, **kwargs):
        """
        Returns the EO datasets contained in the dataset series. If
        provided, the filenames are selected according to the keyword
        arguments included in the request.
        
        @param  kwargs  keyword arguments for selection of datasets
        @return         a list of {@link eoxserver.lib.interfaces.EOxSEODatasetInterface} objects
        """
        return None
        
#-----------------------------------------------------------------------
# Implementation of model interfaces
#-----------------------------------------------------------------------

class CoverageRecordInterface(object):
    def getCoverageId(self):
        return self.wcseo_object.coverage_id
            
    def _getRectifiedGrid(self):
        offset_vectors = []
        dim = self.wcseo_object.grid.axis_set.count()
        i = 0
        for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx'):
            offset_vectors.append(tuple([0.0 for j in range(0,i)] + [axis.offset_vector_component] + [0.0 for j in range(i+1, dim)]))
            i += 1

        return RectifiedGrid(
            dim = self.wcseo_object.grid.axis_set.count(),
            low = tuple([axis.low for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            high = tuple([axis.high for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            axis_labels = tuple([axis.label for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            srid = self.wcseo_object.grid.srid,
            origin = tuple([axis.origin_component for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            offsets = offset_vectors
        )
    
    def _getReferenceableGrid(self):
        raise InternalError("Referenceable grids are not implemented")

    def getGrid(self):
        if isinstance(self.wcseo_object.grid, RectifiedGridRecord):
            return self._getRectifiedGrid()
        else:
            return self._getReferenceableGrid()

    def getRangeType(self):
        range_type = []
        
        for channel in self.wcseo_object.range_type.channels.order_by('rangetype2channel__no'):
            range_type.append(Channel(
                name = channel.name,
                identifier = channel.identifier,
                description = channel.description,
                definition = channel.definition,
                quality=None,
                nil_values = [NilValue(reason=nil_value.reason, value=nil_value.value) for nil_value in channel.nil_values.all()],
                uom = channel.uom,
                allowed_values_start = channel.allowed_values_start,
                allowed_values_end = channel.allowed_values_end,
                allowed_values_significant_figures = channel.allowed_values_significant_figures
            ))
        
        return range_type
    
    def getLayerMetadata(self):
        return [(kvp.key, kvp.value) for kvp in self.wcseo_object.layer_metadata.all()]
        
class EOMetadataRecordInterface(object):
    def getBeginTime(self):
        return self.wcseo_object.eo_metadata.timestamp_begin
    
    def getEndTime(self):
        return self.wcseo_object.eo_metadata.timestamp_end
    
    def getFootprint(self):
        return self.wcseo_object.eo_metadata.footprint
    
    def getWGS84Extent(self):
        return self.wcseo_object.eo_metadata.footprint.extent
        
    def getEOGML(self):
        return self.wcseo_object.eo_metadata.eo_gml

class EOCoverageRecordInterface(CoverageRecordInterface, EOMetadataRecordInterface):
    def getEOID(self):
        return self.wcseo_object.eo_id
    
    def getLineage(self):
        return None # TODO: Lineage


class FileRecordInterface(object):
    def getFilename(self):
        return self.wcseo_object.file.path
    
    def getQuicklookPath(self):
        return self.wcseo_object.file.quicklook_path
    
    def getMetadataPath(self):
        return self.wcseo_object.file.metadata_path

    def getMetadataFormat(self):
        return self.wcseo_object.file.metadata_format

class RectifiedCompositeObjectInterface(object):
    def getDatasets(self, **kwargs):
        if "containment" in kwargs:
            containment = kwargs["containment"].lower()
            if containment not in ("overlaps", "contains"):
                raise InvalidParameterException("The 'containment' must be either 'overlaps' or 'contains', but is '%s'" % containment)
        else:
            containment = "overlaps"
        
        if "slices" in kwargs:
            slices = kwargs["slices"]
        else:
            slices = []

        if "trims" in kwargs:
            trims = kwargs["trims"]
        else:
            trims = []

        spatial_slices = []
        spatial_trims = []
        
        query_set = self.wcseo_object.rect_datasets.all()
        
        for slice in slices:
            if slice.dimension in ("t", "time", "phenomenonTime"): # TODO
                if slice.crs is None or slice.crs == "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
                    query_set = query_set.filter(
                        eo_metadata__timestamp_begin__lte=slice.slice_point,
                        eo_metadata__timestamp_end__gte=slice.slice_point
                    )
                else:
                    raise UnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % slice.crs)
            elif slice.dimension in ("x", "long", "Long"): # TODO
                spatial_slices.append(slice)
            elif slice.dimension in ("y", "lat", "Lat"): # TODO
                spatial_slices.append(slice)

        for trim in trims:
            if trim.dimension in ("t", "time", "phenomenonTime"): # TODO
                if trim.crs is None or trim.crs == "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
                    if trim.trim_low is not None:
                        dt_low = trim.trim_low
                    else:
                        dt_low = self.getBeginTime()
                        
                    if trim.trim_high is not None:
                        dt_high = trim.trim_high
                    else:
                        dt_high = self.getEndTime()
                    
                    if containment == "overlaps":
                        query_set = query_set.exclude(
                            eo_metadata__timestamp_begin__gt=dt_high
                        ).exclude(
                            eo_metadata__timestamp_end__lt=dt_low
                        )
                    elif containment == "contains":
                        query_set = query_set.filter(
                            eo_metadata__timestamp_begin__gte=dt_low,
                            eo_metadata__timestamp_end__lte=dt_high
                        )
                else:
                    raise UnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)
            elif trim.dimension in ("x", "long", "Long", "y", "lat", "Lat"): # TODO
                spatial_trims.append(trim)
                
        datasets = []
        for dataset_record in query_set:
            dataset = RectifiedDatasetRecordInterface(dataset_record)
            datasets.extend(dataset.getDatasets(containment=containment, slices=spatial_slices, trims=spatial_trims))
        
        return datasets
    

class SingleFileCoverageRecordInterface(CoverageRecordInterface, FileRecordInterface, DatasetInterface):
    def getCoverageSubtype(self):
        return "RectifiedGridCoverage"
    
    def getEOCoverageSubtype(self):
        return "RectifiedDataset"
    
    def getType(self):
        return "file"
    
    def getDatasets(self, **kwargs):
        return [self]

class RectifiedDatasetRecordInterface(EOCoverageRecordInterface, FileRecordInterface, EODatasetInterface):
    def getCoverageSubtype(self):
        return "RectifiedGridCoverage"
        
    def getEOCoverageSubtype(self):
        return "RectifiedDataset"
        
    def getType(self):
        return "eo.rect_dataset"
    
    def getDatasets(self, **kwargs):
        if "containment" in kwargs:
            containment = kwargs["containment"].lower()
            if containment not in ("overlaps", "contains"):
                raise InvalidParameterException("The 'containment' must be either 'overlaps' or 'contains', but is '%s'" % containment)
        else:
            containment = "overlaps"
        
        if "slices" in kwargs:
            slices = kwargs["slices"]
        else:
            slices = []

        if "trims" in kwargs:
            trims = kwargs["trims"]
        else:
            trims = []
            
        for slice in slices:
            if slice.dimension in ("t", "time", "phenomenonTime") and not self.timeSliceWithin(slice): # TODO
                return []
            elif not self.spatialSliceWithin(slice):
                return []
        
        for trim in trims:
            if trim.dimension in ("t", "time", "phenomenonTime"): # TODO
                if containment == "overlaps" and not self.timeOverlaps(trim):
                    return []
                elif containment == "contains" and not self.timeWithin(trim):
                    return []
            
            else:
                if containment == "overlaps" and not self.spatiallyOverlaps(trim):
                    return []
                elif containment == "contains" and not self.spatiallyWithin(trim):
                    return []
        
        return [self]
    
    def timeSliceWithin(self, slice):
        if slice.crs is None or slice.crs == "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
            return (self.getBeginTime() <= slice.slice_point and\
                    slice.slice_point <= self.getEndTime())
        else:
            raise UnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % slice.crs)
    
    def timeOverlaps(self, trim):
        if trim.crs is None or trim.crs == "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
            if trim.trim_low is not None:
                dt_low = trim.trim_low
            else:
                dt_low = self.getBeginTime()
                
            if trim.trim_high is not None:
                dt_high = trim.trim_high
            else:
                dt_high = self.getEndTime()
            
            return ((dt_low <= self.getBeginTime() and self.getBeginTime() <= dt_high) or\
                    (dt_low <= self.getEndTime() and self.getEndTime() <= dt_high))
        else:
            raise UnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)

    def timeWithin(self, trim):
        if trim.crs is None or trim.crs == "http://www.opengis.net/def/trs/ISO-8601/0/Gregorian+UTC":
            if trim.trim_low is not None:
                dt_low = trim.trim_low
            else:
                dt_low = self.getBeginTime()
                
            if trim.trim_high is not None:
                dt_high = trim.trim_high
            else:
                dt_high = self.getEndTime()
            
            return (dt_low <= self.getBeginTime() and self.getEndTime() <= dt_high)
        else:
            raise UnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)
    
    def spatialSliceWithin(self, slice):
        grid = self.getGrid()
        
        return slice.crosses(grid)
    
    def spatiallyOverlaps(self, trim):
        return trim.overlaps(self.getFootprint())
    
    def spatiallyWithin(self, trim):
        return trim.contains(self.getFootprint())

class RectifiedStitchedMosaicRecordInterface(EOCoverageRecordInterface, RectifiedCompositeObjectInterface, StitchedMosaicInterface):
    def getCoverageSubtype(self):
        return "RectifiedGridCoverage"
    
    def getEOCoverageSubtype(self):
        return "RectifiedStitchedMosaic"
    
    def getType(self):
        return "eo.rect_mosaic"
        
    def getShapeFilePath(self):
        return self.wcseo_object.shape_file_path
    
class RectifiedDatasetSeriesRecordInterface(EOMetadataRecordInterface, RectifiedCompositeObjectInterface, DatasetSeriesInterface):
    def getEOID(self):
        return self.wcseo_object.eo_id
        
    def getType(self):
        return "eo.rect_dataset_series"
    

#-----------------------------------------------------------------------
# Factories
#-----------------------------------------------------------------------

class CoverageInterfaceFactory(object):
    @classmethod
    def getCoverageInterface(cls, coverage_id):
        try:
            coverage = SingleFileCoverageRecord.objects.get(coverage_id=coverage_id)
            return SingleFileCoverageRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, SingleFileCoverageRecord.DoesNotExist):
                pass
            elif isinstance(e, SingleFileCoverageRecord.MultipleObjectsReturned):
                raise InternalError("Multiple single file coverages with coverage id '%s'." % coverage_id)
            else:
                raise
        
        try:
            coverage = RectifiedDatasetRecord.objects.get(coverage_id=coverage_id)
            return RectifiedDatasetRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, RectifiedDatasetRecord.DoesNotExist):
                pass
            elif isinstance(e, RectifiedDatasetRecord.MultipleObjectsReturned):
                raise InternalError("Multiple rectified datasets with coverage id '%s'." % coverage_id)
            else:
                raise
        
        try:
            coverage = RectifiedStitchedMosaicRecord.objects.get(coverage_id=coverage_id)
            return RectifiedStitchedMosaicRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, RectifiedStitchedMosaicRecord.DoesNotExist):
                pass
            elif isinstance(e, RectifiedStitchedMosaicRecord.MultipleObjectsReturned):
                raise InternalError("Multiple rectified stitched mosaics with coverage id '%s'." % coverage_id)
            else:
                raise
                
        # TODO: configuration file coverages
        
        raise NoSuchCoverageException("No coverage with coverage id '%s' found" % coverage_id)
        
    @classmethod
    def getCoverageInterfaceByEOID(cls, eo_id):
        try:
            coverage = RectifiedDatasetRecord.objects.get(eo_id=eo_id)
            return RectifiedDatasetRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, RectifiedDatasetRecord.DoesNotExist):
                pass
            elif isinstance(e, RectifiedDatasetRecord.MultipleObjectsReturned):
                raise InternalError("Multiple rectified datasets with EO id '%s'." % eo_id)
            else:
                raise
        
        try:
            coverage = RectifiedStitchedMosaicRecord.objects.get(eo_id=eo_id)
            return RectifiedStitchedMosaicRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, RectifiedStitchedMosaicRecord.DoesNotExist):
                pass
            elif isinstance(e, RectifiedStitchedMosaicRecord.MultipleObjectsReturned):
                raise InternalError("Multiple rectified stitched mosaics with EO id '%s'." % eo_id)
            else:
                raise
        
        raise NoSuchCoverageException("No coverage with EO id '%s' found" % eo_id)

    @classmethod
    def getVisibleCoverageInterfaces(cls):
        cov_ints = []
        
        for coverage in SingleFileCoverageRecord.objects.all():
            cov_ints.append(SingleFileCoverageRecordInterface(coverage))
        
        for coverage in RectifiedDatasetRecord.objects.filter(visible=True):
            cov_ints.append(RectifiedDatasetRecordInterface(coverage))
        
        for coverage in RectifiedStitchedMosaicRecord.objects.all():
            cov_ints.append(RectifiedStitchedMosaicRecordInterface(coverage))
        
        return cov_ints

class DatasetSeriesFactory(object):
    @classmethod
    def getDatasetSeriesInterface(cls, eo_id):
        try:
            series = RectifiedDatasetSeriesRecord.objects.get(eo_id=eo_id)
            return RectifiedDatasetSeriesRecordInterface(series)
        except Exception, e:
            if isinstance(e, RectifiedDatasetSeriesRecord.DoesNotExist):
                pass
            elif isinstance(e, RectifiedDatasetSeriesRecord.MultipleObjectsReturned):
                raise InternalError("Multiple rectified dataset series with EO id '%s'." % eo_id)
            else:
                raise
        
        # TODO: configuration file series
        
        raise NoSuchDatasetSeriesException("No dataset series with EO id '%s' found." % eo_id)
                
    @classmethod
    def getAllDatasetSeriesInterfaces(cls):
        series_ints = []
        
        for series in RectifiedDatasetSeriesRecord.objects.all():
            series_ints.append(RectifiedDatasetSeriesRecordInterface(series))
        
        return series_ints

