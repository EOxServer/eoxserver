#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

"""
This module contains the definition of coverage and dataset series
interfaces. These provide a harmonized interface to coverage data that
can be stored in different formats and has different types.
"""
import logging

from eoxserver.lib.config import EOxSConfig, EOxSCoverageConfig
from eoxserver.lib.domainset import EOxSRectifiedGrid, getGridFromFile
from eoxserver.lib.rangetype import EOxSChannel, EOxSNilValue, getRangeTypeFromFile
from eoxserver.lib.util import findFiles, getDateTime
from eoxserver.lib.metadata import EOxSMetadataInterfaceFactory
from eoxserver.lib.exceptions import (
    EOxSInternalError, EOxSNoSuchCoverageException, EOxSInvalidParameterException,
    EOxSUnknownCRSException, EOxSNoSuchDatasetSeriesException
)
from eoxserver.server.models import (
    EOxSSingleFileCoverageRecord, EOxSRectifiedDatasetRecord,
    EOxSRectifiedDatasetSeriesRecord, EOxSRectifiedStitchedMosaicRecord,
    EOxSRectifiedGridRecord
)

#-----------------------------------------------------------------------
# Abstract Interface Definitions
#-----------------------------------------------------------------------

class EOxSCoverageInterface(object):
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

class EOxSEOMetadataInterface(object):
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
    
class EOxSDatasetInterface(EOxSCoverageInterface):
    def getFilename(self):
        return None
    
    def getQuicklookPath(self):
        return None
        
    def getMetadataPath(self):
        return None
    
    def getMetadataFormat(self):
        return None

class EOxSEODatasetInterface(EOxSDatasetInterface, EOxSEOMetadataInterface):
    def getLineage(self):
        return None

class EOxSStitchedMosaicInterface(EOxSCoverageInterface, EOxSEOMetadataInterface):
    def getLineage(self):
        return None
    
    def getShapeFilePath(self):
        return None

class EOxSDatasetSeriesInterface(EOxSEOMetadataInterface):
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

class EOxSCoverageRecordInterface(object):
    def getCoverageId(self):
        return self.wcseo_object.coverage_id
            
    def _getRectifiedGrid(self):
        offset_vectors = []
        dim = self.wcseo_object.grid.axis_set.count()
        i = 0
        for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx'):
            offset_vectors.append(tuple([0.0 for j in range(0,i)] + [axis.offset_vector_component] + [0.0 for j in range(i+1, dim)]))
            i += 1

        return EOxSRectifiedGrid(
            dim = self.wcseo_object.grid.axis_set.count(),
            low = tuple([axis.low for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            high = tuple([axis.high for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            axis_labels = tuple([axis.label for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            srid = self.wcseo_object.grid.srid,
            origin = tuple([axis.origin_component for axis in self.wcseo_object.grid.axis_set.order_by('dimension_idx')]),
            offsets = offset_vectors
        )
    
    def _getReferenceableGrid(self):
        raise EOxSInternalError("Referenceable grids are not implemented")

    def getGrid(self):
        if isinstance(self.wcseo_object.grid, EOxSRectifiedGridRecord):
            return self._getRectifiedGrid()
        else:
            return self._getReferenceableGrid()

    def getRangeType(self):
        range_type = []
        
        for channel in self.wcseo_object.range_type.channels.order_by('eoxsrangetype2channel__no'):
            range_type.append(EOxSChannel(
                name = channel.name,
                identifier = channel.identifier,
                description = channel.description,
                definition = channel.definition,
                quality=None,
                nil_values = [EOxSNilValue(reason=nil_value.reason, value=nil_value.value) for nil_value in channel.nil_values.all()],
                uom = channel.uom,
                allowed_values_start = channel.allowed_values_start,
                allowed_values_end = channel.allowed_values_end,
                allowed_values_significant_figures = channel.allowed_values_significant_figures
            ))
        
        return range_type
    
    def getLayerMetadata(self):
        return [(kvp.key, kvp.value) for kvp in self.wcseo_object.layer_metadata.all()]
        
class EOxSEOMetadataRecordInterface(object):
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

class EOxSEOCoverageRecordInterface(EOxSCoverageRecordInterface, EOxSEOMetadataRecordInterface):
    def getEOID(self):
        return self.wcseo_object.eo_id
    
    def getLineage(self):
        return None # TODO: Lineage


class EOxSFileRecordInterface(object):
    def getFilename(self):
        return self.wcseo_object.file.path
    
    def getQuicklookPath(self):
        return self.wcseo_object.file.quicklook_path
    
    def getMetadataPath(self):
        return self.wcseo_object.file.metadata_path

    def getMetadataFormat(self):
        return self.wcseo_object.file.metadata_format

class EOxSRectifiedCompositeObjectInterface(object):
    def getDatasets(self, **kwargs):
        if "containment" in kwargs:
            containment = kwargs["containment"].lower()
            if containment not in ("overlaps", "contains"):
                raise EOxSInvalidParameterException("The 'containment' must be either 'overlaps' or 'contains', but is '%s'" % containment)
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
                    raise EOxSUnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % slice.crs)
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
                    raise EOxSUnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)
            elif trim.dimension in ("x", "long", "Long", "y", "lat", "Lat"): # TODO
                spatial_trims.append(trim)
                
        datasets = []
        for dataset_record in query_set:
            dataset = EOxSRectifiedDatasetRecordInterface(dataset_record)
            datasets.extend(dataset.getDatasets(containment=containment, slices=spatial_slices, trims=spatial_trims))
        
        return datasets
    

class EOxSSingleFileCoverageRecordInterface(EOxSCoverageRecordInterface, EOxSFileRecordInterface, EOxSDatasetInterface):
    def getCoverageSubtype(self):
        return "RectifiedGridCoverage"
    
    def getEOCoverageSubtype(self):
        return "RectifiedDataset"
    
    def getType(self):
        return "file"
    
    def getDatasets(self, **kwargs):
        return [self]

class EOxSRectifiedDatasetRecordInterface(EOxSEOCoverageRecordInterface, EOxSFileRecordInterface, EOxSEODatasetInterface):
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
                raise EOxSInvalidParameterException("The 'containment' must be either 'overlaps' or 'contains', but is '%s'" % containment)
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
            raise EOxSUnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % slice.crs)
    
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
            raise EOxSUnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)

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
            raise EOxSUnknownCRSException("Time reference system '%s' not recognized. Please use UTC." % trim.crs)
    
    def spatialSliceWithin(self, slice):
        grid = self.getGrid()
        
        return slice.crosses(grid)
    
    def spatiallyOverlaps(self, trim):
        return trim.overlaps(self.getFootprint())
    
    def spatiallyWithin(self, trim):
        return trim.contains(self.getFootprint())

class EOxSRectifiedStitchedMosaicRecordInterface(EOxSEOCoverageRecordInterface, EOxSRectifiedCompositeObjectInterface, EOxSStitchedMosaicInterface):
    def getCoverageSubtype(self):
        return "RectifiedGridCoverage"
    
    def getEOCoverageSubtype(self):
        return "RectifiedStitchedMosaic"
    
    def getType(self):
        return "eo.rect_mosaic"
        
    def getShapeFilePath(self):
        return self.wcseo_object.shape_file_path
    
class EOxSRectifiedDatasetSeriesRecordInterface(EOxSEOMetadataRecordInterface, EOxSRectifiedCompositeObjectInterface, EOxSDatasetSeriesInterface):
    def getEOID(self):
        return self.wcseo_object.eo_id
        
    def getType(self):
        return "eo.rect_dataset_series"
    

#-----------------------------------------------------------------------
# Implementation of configuration file interfaces
#-----------------------------------------------------------------------

# TODO

#-----------------------------------------------------------------------
# Factories
#-----------------------------------------------------------------------

class EOxSCoverageInterfaceFactory(object):
    @classmethod
    def getCoverageInterface(cls, coverage_id):
        try:
            coverage = EOxSSingleFileCoverageRecord.objects.get(coverage_id=coverage_id)
            return EOxSSingleFileCoverageRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, EOxSSingleFileCoverageRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSSingleFileCoverageRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple single file coverages with coverage id '%s'." % coverage_id)
            else:
                raise
        
        try:
            coverage = EOxSRectifiedDatasetRecord.objects.get(coverage_id=coverage_id)
            return EOxSRectifiedDatasetRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, EOxSRectifiedDatasetRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSRectifiedDatasetRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple rectified datasets with coverage id '%s'." % coverage_id)
            else:
                raise
        
        try:
            coverage = EOxSRectifiedStitchedMosaicRecord.objects.get(coverage_id=coverage_id)
            return EOxSRectifiedStitchedMosaicRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, EOxSRectifiedStitchedMosaicRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSRectifiedStitchedMosaicRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple rectified stitched mosaics with coverage id '%s'." % coverage_id)
            else:
                raise
                
        # TODO: configuration file coverages
        
        raise EOxSNoSuchCoverageException("No coverage with coverage id '%s' found" % coverage_id)
        
    @classmethod
    def getCoverageInterfaceByEOID(cls, eo_id):
        try:
            coverage = EOxSRectifiedDatasetRecord.objects.get(eo_id=eo_id)
            return EOxSRectifiedDatasetRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, EOxSRectifiedDatasetRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSRectifiedDatasetRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple rectified datasets with EO id '%s'." % eo_id)
            else:
                raise
        
        try:
            coverage = EOxSRectifiedStitchedMosaicRecord.objects.get(eo_id=eo_id)
            return EOxSRectifiedStitchedMosaicRecordInterface(coverage)
        except Exception, e:
            if isinstance(e, EOxSRectifiedStitchedMosaicRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSRectifiedStitchedMosaicRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple rectified stitched mosaics with EO id '%s'." % eo_id)
            else:
                raise
        
        raise EOxSNoSuchCoverageException("No coverage with EO id '%s' found" % eo_id)

    @classmethod
    def getVisibleCoverageInterfaces(cls):
        cov_ints = []
        
        for coverage in EOxSSingleFileCoverageRecord.objects.all():
            cov_ints.append(EOxSSingleFileCoverageRecordInterface(coverage))
        
        for coverage in EOxSRectifiedDatasetRecord.objects.filter(visible=True):
            cov_ints.append(EOxSRectifiedDatasetRecordInterface(coverage))
        
        for coverage in EOxSRectifiedStitchedMosaicRecord.objects.all():
            cov_ints.append(EOxSRectifiedStitchedMosaicRecordInterface(coverage))
        
        return cov_ints

class EOxSDatasetSeriesFactory(object):
    @classmethod
    def getDatasetSeriesInterface(cls, eo_id):
        try:
            series = EOxSRectifiedDatasetSeriesRecord.objects.get(eo_id=eo_id)
            return EOxSRectifiedDatasetSeriesRecordInterface(series)
        except Exception, e:
            if isinstance(e, EOxSRectifiedDatasetSeriesRecord.DoesNotExist):
                pass
            elif isinstance(e, EOxSRectifiedDatasetSeriesRecord.MultipleObjectsReturned):
                raise EOxSInternalError("Multiple rectified dataset series with EO id '%s'." % eo_id)
            else:
                raise
        
        # TODO: configuration file series
        
        raise EOxSNoSuchDatasetSeriesException("No dataset series with EO id '%s' found." % eo_id)
                
    @classmethod
    def getAllDatasetSeriesInterfaces(cls):
        series_ints = []
        
        for series in EOxSRectifiedDatasetSeriesRecord.objects.all():
            series_ints.append(EOxSRectifiedDatasetSeriesRecordInterface(series))
        
        return series_ints

