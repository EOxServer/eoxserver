#-----------------------------------------------------------------------
# $Id$
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
from django.contrib.gis.geos import GEOSGeometry
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from eoxserver.resources.coverages.validators import validateEOOM
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory
from eoxserver.core.models import Resource

NCNameValidator = RegexValidator(re.compile(r'^[a-zA-z_][a-zA-Z0-9_.-]*$'), message="This field must contain a valid NCName.")

class NilValueRecord(models.Model):
    reason = models.CharField(max_length=128)
    value = models.IntegerField()

    def __unicode__(self):
        return self.reason+" "+str(self.value)

    class Meta:
        verbose_name = "NilValue"

class ChannelRecord(models.Model):
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=256)
    description = models.TextField()
    definition = models.CharField(max_length=256)
    nil_values = models.ManyToManyField(NilValueRecord, null=True, blank=True) # TODO: NilValues operate on RangeType not Channel
    uom = models.CharField(max_length=16)
    allowed_values_start = models.IntegerField()
    allowed_values_end = models.IntegerField()
    allowed_values_significant_figures = models.IntegerField()
    
    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Channel"

class RangeType(models.Model):
    name = models.CharField(max_length=256)
    channels = models.ManyToManyField(ChannelRecord, through="RangeType2Channel")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "RangeType"
    
class RangeType2Channel(models.Model):
    channel = models.ForeignKey(ChannelRecord)
    range_type = models.ForeignKey(RangeType)
    no = models.PositiveIntegerField()

class RectifiedGridRecord(models.Model):
    def __unicode__(self):
        return str(self.id) + " RectifiedGrid"

    srid = models.IntegerField()

    class Meta:
        verbose_name = "RectifiedGrid"

class AxisRecord(models.Model):
    grid = models.ForeignKey(RectifiedGridRecord, related_name="axis_set")
    label = models.CharField(max_length=64)
    dimension_idx = models.PositiveIntegerField()
    low = models.IntegerField()
    high = models.IntegerField()
    origin_component = models.FloatField()
    offset_vector_component = models.FloatField() # only axis parallel

    class Meta:
        verbose_name = "Axis"
        verbose_name_plural = "Axis"

class LayerMetadataRecord(models.Model):
    key = models.CharField(max_length=256)
    value = models.TextField()

    def __unicode__(self):
        return self.key

    class Meta:
        verbose_name = "Layer Metadata"
        verbose_name_plural = "Layer Metadata"

class FileRecord(models.Model):
    path = models.CharField(max_length=1024)
    #file = models.FileField(upload_to='files') # TODO
    quicklook_path = models.CharField(max_length=1024, blank=True)
    metadata_path = models.CharField(max_length=1024, blank=True)
    metadata_format = models.CharField(max_length=64, blank=True)

    def __unicode__(self):
        return self.path

    class Meta:
        verbose_name = "File"
        verbose_name_plural = "Files"

class LineageRecord(models.Model):

    class Meta:
        verbose_name = "Lineage Entry"
        verbose_name_plural = "Lineage Entries"

class EOMetadataRecord(models.Model):
    timestamp_begin = models.DateTimeField()
    timestamp_end = models.DateTimeField()
    footprint = models.PolygonField(srid=4326, geography=True)
    eo_gml = models.TextField(blank=True, validators=[validateEOOM]) # validate against schema
    objects = models.GeoManager()

    class Meta:
        verbose_name = "EO Metadata Entry"
        verbose_name_plural = "EO Metadata Entries"

    def __unicode__(self):
        return ("BeginTime: %s" % self.timestamp_begin)
    
    def clean(self):
        """
        This method validates the consistency of the EO Metadata record,
        i.e.:
        * check that the begin time in timestamp_begin is the same as in
          EO GML
        * check that the end time in timestamp_end is the same as in EO
          GML
        * check that the footprint is the same as in EO GML
        """
        EPSILON = 1e-10
        
        if self.eo_gml:
            md_int = MetadataInterfaceFactory.getMetadataInterface(self.eo_gml, "eogml")
            
            if self.timestamp_begin != md_int.getBeginTime().replace(tzinfo=None):
                raise ValidationError("EO GML acquisition begin time does not match.")
            if self.timestamp_end != md_int.getEndTime().replace(tzinfo=None):
                raise ValidationError("EO GML acquisition end time does not match.")
            if self.footprint is not None:
                if not self.footprint.equals_exact(GEOSGeometry(md_int.getFootprint()), EPSILON * max(self.footprint.extent)): # compare the footprints with a tolerance in order to account for rounding and string conversion errors
                    raise ValidationError("EO GML footprint does not match.")

class CoverageRecord(Resource):
    coverage_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    range_type = models.ForeignKey(RangeType)
    layer_metadata = models.ManyToManyField(LayerMetadataRecord, null=True, blank=True)

    class Meta:
        abstract = True

class SingleFileCoverageRecord(CoverageRecord):
    grid = models.ForeignKey(RectifiedGridRecord, related_name = "single_file_coverages")
    file = models.ForeignKey(FileRecord, related_name = "single_file_coverages")

    class Meta:
        verbose_name = "Single File Coverage"
        verbose_name_plural = "Single File Coverages"

class EOCoverageRecord(CoverageRecord):
    eo_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOMetadataRecord, related_name="%(class)s_set")
    lineage = models.OneToOneField(LineageRecord, related_name="%(class)s_set")
    
    class Meta:
        abstract = True

    def delete(self):
        eo_metadata = self.eo_metadata
        lineage = self.lineage
        super(EOCoverageRecord, self).delete()
        eo_metadata.delete()
        lineage.delete()

class RectifiedDatasetRecord(EOCoverageRecord):
    grid = models.ForeignKey(RectifiedGridRecord, related_name="rect_datasets")
    file = models.ForeignKey(FileRecord, related_name="rect_datasets")
    automatic = models.BooleanField(default=False) # True means that the dataset was automatically generated from a dataset series's data dir
    visible = models.BooleanField(default=False) # True means that the dataset is visible in the GetCapabilities response

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "Dataset"
        verbose_name_plural = "Datasets"

class RectifiedStitchedMosaicRecord(EOCoverageRecord):
    grid = models.ForeignKey(RectifiedGridRecord, related_name="rect_stitched_mosaics")
    image_pattern = models.CharField(max_length=1024)
    shape_file_path = models.CharField(max_length=1024, blank=True)
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord, related_name = "rect_stitched_mosaics")

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "StitchedMosaic"
        verbose_name_plural = "StitchedMosaics"

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.all():
            dataset.delete()
        super(RectifiedStitchedMosaicRecord, self).delete()
        eo_metadata.delete()

class MosaicDataDirRecord(models.Model):
    mosaic = models.ForeignKey(RectifiedStitchedMosaicRecord, related_name = "data_dirs")
    dir = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.dir

    class Meta:
        verbose_name = "Mosaic Data Directory"
        verbose_name_plural = "Mosaic Data Directories"

class RectifiedDatasetSeriesRecord(Resource):
    eo_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOMetadataRecord, related_name="rect_dataset_series_set")
    image_pattern = models.CharField(max_length=1024)
    rect_stitched_mosaics = models.ManyToManyField(RectifiedStitchedMosaicRecord, blank=True, null=True, related_name="dataset_series")
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord, blank=True, null=True, related_name="rect_dataset_series_set")

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "DatasetSeries"
        verbose_name_plural = "DatasetSeries"

    def clean(self):
        pass
    """
        super(RectifiedDatasetSeriesRecord, self).clean()
        
        for data_dir in self.data_dirs.all():
            try:
                files = findFiles(data_dir.dir, self.image_pattern)
            except OSError, e:
                raise ValidationError("%s: %s"%(e.strerror, e.filename))
            
            for dataset in self.rect_datasets.all():
                #raise ValidationError(self.rect_datasets.all())
                if dataset.file.path in files:
                    raise ValidationError("The dataset with the id %s is already included in the data directory %s"%(dataset.eo_id, data_dir.dir))
    """

    def save(self):
        pass
    """    for data_dir in self.data_dirs.all():
            try:
                files = findFiles(data_dir.dir, self.image_pattern)
            except OSError, e:
                raise ValidationError("%s: %s"%(e.strerror, e.filename))
            
            for dataset in self.rect_datasets.all():
                if dataset.file.path in files:
                    raise ValidationError("The dataset with the id %s is already included in the data directory %s"%(dataset.eo_id, data_dir.dir))
                    
        super(RectifiedDatasetSeriesRecord, self).save()
    """

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.all():
            dataset.delete()
        super(RectifiedDatasetSeriesRecord, self).delete()
        eo_metadata.delete()

class DataDirRecord(models.Model):
    dataset_series = models.ForeignKey(RectifiedDatasetSeriesRecord, related_name="data_dirs")
    dir = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.dir

    class Meta:
        verbose_name = "Data Directory"
        verbose_name_plural = "Data Directories"
