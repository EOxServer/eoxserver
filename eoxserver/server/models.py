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

import re

from django.contrib.gis.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.validators import RegexValidator

NCNameValidator = RegexValidator(re.compile(r'^[a-zA-z_][a-zA-Z0-9_.-]*$'), message="This field must contain a valid NCName.")

class EOxSNilValueRecord(models.Model):
    reason = models.CharField(max_length=128)
    value = models.IntegerField()

    def __unicode__(self):
        return self.reason+" "+str(self.value)

    class Meta:
        verbose_name = "NilValue"

class EOxSChannelRecord(models.Model):
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=256)
    description = models.TextField()
    definition = models.CharField(max_length=256)
    nil_values = models.ManyToManyField(EOxSNilValueRecord, null=True, blank=True) # TODO: NilValues operate on RangeType not Channel
    uom = models.CharField(max_length=16)
    allowed_values_start = models.IntegerField()
    allowed_values_end = models.IntegerField()
    allowed_values_significant_figures = models.IntegerField()
    
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Channel"

class EOxSRangeType(models.Model):
    name = models.CharField(max_length=256)
    channels = models.ManyToManyField(EOxSChannelRecord, through="EOxSRangeType2Channel")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "RangeType"
    
class EOxSRangeType2Channel(models.Model):
    channel = models.ForeignKey(EOxSChannelRecord)
    range_type = models.ForeignKey(EOxSRangeType)
    no = models.PositiveIntegerField()

class EOxSRectifiedGridRecord(models.Model):
    def __unicode__(self):
        return str(self.id) + " RectifiedGrid"

    srid = models.IntegerField()

    class Meta:
        verbose_name = "RectifiedGrid"

class EOxSAxisRecord(models.Model):
    grid = models.ForeignKey(EOxSRectifiedGridRecord, related_name="axis_set")
    label = models.CharField(max_length=64)
    dimension_idx = models.PositiveIntegerField()
    low = models.IntegerField()
    high = models.IntegerField()
    origin_component = models.FloatField()
    offset_vector_component = models.FloatField() # only axis parallel

class EOxSLayerMetadataRecord(models.Model):
    key = models.CharField(max_length=256)
    value = models.TextField()

    def __unicode__(self):
        return self.key

    class Meta:
        verbose_name = "Layer Metadata"
        verbose_name_plural = "Layer Metadata"

class EOxSFileRecord(models.Model):
    path = models.CharField(max_length=1024)
    quicklook_path = models.CharField(max_length=1024, blank=True)
    metadata_path = models.CharField(max_length=1024, blank=True)
    metadata_format = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        return self.path

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"

class EOxSLineageRecord(models.Model):

    class Meta:
        verbose_name = "Lineage Entry"
        verbose_name_plural = "Lineage Entries"

class EOxSEOMetadataRecord(models.Model):
    timestamp_begin = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    footprint = models.PolygonField(srid=4326, geography=True)
    eo_gml = models.TextField(blank=True)
    objects = models.GeoManager()

    def __unicode__(self):
        return ("BeginTime: %s" % self.timestamp_begin)

    class Meta:
        verbose_name = "EO Metadata Entry"
        verbose_name_plural = "EO Metadata Entries"

class EOxSCoverageRecord(models.Model):
    coverage_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    range_type = models.ForeignKey(EOxSRangeType)
    layer_metadata = models.ManyToManyField(EOxSLayerMetadataRecord, null=True, blank=True)

    class Meta:
        abstract = True

class EOxSSingleFileCoverageRecord(EOxSCoverageRecord):
    grid = models.ForeignKey(EOxSRectifiedGridRecord, related_name = "single_file_coverages")
    file = models.ForeignKey(EOxSFileRecord, related_name = "single_file_coverages")

    class Meta:
        verbose_name = "Single File Coverage"
        verbose_name_plural = "Single File Coverages"

class EOxSEOCoverageRecord(EOxSCoverageRecord):
    eo_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOxSEOMetadataRecord, related_name="%(class)s_set")
    lineage = models.OneToOneField(EOxSLineageRecord, related_name="%(class)s_set")
    
    class Meta:
        abstract = True

    def delete(self):
        eo_metadata = self.eo_metadata
        lineage = self.lineage
        super(EOxSEOCoverageRecord, self).delete()
        eo_metadata.delete()
        lineage.delete()

class EOxSRectifiedDatasetRecord(EOxSEOCoverageRecord):
    grid = models.ForeignKey(EOxSRectifiedGridRecord, related_name="rect_datasets")
    file = models.ForeignKey(EOxSFileRecord, related_name="rect_datasets")
    automatic = models.BooleanField(default=False) # True means that the dataset was automatically generated from a dataset series's data dir
    visible = models.BooleanField(default=False) # True means that the dataset is visible in the GetCapabilities response
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    contained_in = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"

class EOxSRectifiedStitchedMosaicRecord(EOxSEOCoverageRecord):
    grid = models.ForeignKey(EOxSRectifiedGridRecord, related_name="rect_stitched_mosaics")
    rect_datasets = generic.GenericRelation(EOxSRectifiedDatasetRecord)
    image_pattern = models.CharField(max_length=1024)
    shape_file_path = models.CharField(max_length=1024, blank=True)

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "StitchedMosaic"
        verbose_name_plural = "StitchedMosaics"

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.all():
            dataset.delete()
        super(EOxSRectifiedStitchedMosaicRecord, self).delete()
        eo_metadata.delete()

class EOxSMosaicDataDirRecord(models.Model):
    mosaic = models.ForeignKey(EOxSRectifiedStitchedMosaicRecord, related_name = "data_dirs")
    dir = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.dir

    class Meta:
        verbose_name = "Mosaic Data Directory"
        verbose_name_plural = "Mosaic Data Directories"

class EOxSRectifiedDatasetSeriesRecord(models.Model):
    eo_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOxSEOMetadataRecord, related_name="rect_dataset_series_set")
    image_pattern = models.CharField(max_length=1024)
    rect_datasets = generic.GenericRelation(EOxSRectifiedDatasetRecord)

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "DatasetSeries"
        verbose_name_plural = "DatasetSeries"

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.all():
            dataset.delete()
        super(EOxSRectifiedDatasetSeriesRecord, self).delete()
        eo_metadata.delete()

class EOxSDataDirRecord(models.Model):
    dataset_series = models.ForeignKey(EOxSRectifiedDatasetSeriesRecord, related_name="data_dirs")
    dir = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.dir

    class Meta:
        verbose_name = "Data Directory"
        verbose_name_plural = "Data Directories"
