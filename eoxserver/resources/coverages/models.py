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

import re
from osgeo.gdalconst import *

from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from eoxserver.core.models import Resource
from eoxserver.resources.coverages.validators import validateEOOM
from eoxserver.resources.coverages.metadata import MetadataInterfaceFactory

NCNameValidator = RegexValidator(re.compile(r'^[a-zA-z_][a-zA-Z0-9_.-]*$'), message="This field must contain a valid NCName.")

class NilValueRecord(models.Model):
    reason = models.CharField(max_length=128, choices=(
        ("http://www.opengis.net/def/nil/OGC/0/inapplicable", "Inapplicable (There is no value)"),
        ("http://www.opengis.net/def/nil/OGC/0/missing", "Missing"),
        ("http://www.opengis.net/def/nil/OGC/0/template", "Template (The value will be available later)"),
        ("http://www.opengis.net/def/nil/OGC/0/unknown", "Unknown"),
        ("http://www.opengis.net/def/nil/OGC/0/withheld", "Withheld (The value is not divulged)"),
        ("http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange", "Above detection range"),
        ("http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange", "Below detection range")
    ))
    value = models.IntegerField()

    def __unicode__(self):
        return self.reason+" "+str(self.value)

    class Meta:
        verbose_name = "NilValue"

class BandRecord(models.Model):
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=256)
    description = models.TextField()
    definition = models.CharField(max_length=256)
    uom = models.CharField(max_length=16)
    nil_values = models.ManyToManyField(NilValueRecord, null=True, blank=True)
    gdal_interpretation = models.IntegerField(default=GCI_Undefined,
        choices=(
            (GCI_Undefined, 'Undefined'),
            (GCI_GrayIndex, 'Grayscale'),
            (GCI_PaletteIndex, 'Palette Index'),
            (GCI_RedBand, 'Red'),
            (GCI_GreenBand, 'Green'),
            (GCI_BlueBand, 'Blue'),
            (GCI_AlphaBand, 'Alpha'),
            (GCI_HueBand, 'Hue'),
            (GCI_SaturationBand, 'Saturation'),
            (GCI_LightnessBand, 'Lightness'),
            (GCI_CyanBand, 'Cyan'),
            (GCI_MagentaBand, 'Magenta'),
            (GCI_YellowBand, 'Yellow'),
            (GCI_BlackBand, 'Black')
        )
    )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Band"


class RangeTypeRecord(models.Model):
    name = models.CharField(max_length=256)
    data_type = models.IntegerField(choices=(
        (GDT_Byte, 'Byte'),
        (GDT_UInt16, 'Unsigned Integer 16-bit'),
        (GDT_Int16, 'Signed Integer 16-bit'),
        (GDT_UInt32, 'Unsigned Integer 32-bit'),
        (GDT_Int32, 'Signed Integer 32-bit'),
        (GDT_Float32, 'Floating Point 32-bit'),
        (GDT_Float64, 'Floating Point 64-bit'),
        (GDT_CInt16, 'GDAL CInt 16-bit'),
        (GDT_CInt32, 'GDAL CInt 32-bit'),
        (GDT_CFloat32, 'GDAL CFloat 32-bit'),
        (GDT_CFloat64, 'GDAL CFloat 64-bit')
    ))
    bands = models.ManyToManyField(BandRecord, through="RangeType2Band")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Range Type"
    
class RangeType2Band(models.Model):
    band = models.ForeignKey(BandRecord)
    range_type = models.ForeignKey(RangeTypeRecord)
    no = models.PositiveIntegerField()

class ExtentRecord(models.Model):
    def __unicode__(self):
        return "Extent (SRID=%d; %f, %f, %f, %f)" % (
            self.srid, self.minx, self.miny, self.maxx, self.maxy
        )

    srid = models.IntegerField()
    size_x = models.IntegerField()
    size_y = models.IntegerField()
    minx = models.FloatField()
    miny = models.FloatField()
    maxx = models.FloatField()
    maxy = models.FloatField()

    class Meta:
        verbose_name = "Extent"

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
    range_type = models.ForeignKey(RangeTypeRecord)
    layer_metadata = models.ManyToManyField(LayerMetadataRecord, null=True, blank=True)

    class Meta:
        abstract = True

class SingleFileCoverageRecord(CoverageRecord):
    extent = models.ForeignKey(ExtentRecord, related_name = "single_file_coverages")
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

class EODatasetRecord(EOCoverageRecord):
    file = models.ForeignKey(FileRecord, related_name="%(class)s_set")
    automatic = models.BooleanField(default=False) # True means that the dataset was automatically generated from a dataset series's data dir
    visible = models.BooleanField(default=False) # True means that the dataset is visible in the GetCapabilities response

    def __unicode__(self):
        return self.eo_id

    class Meta:
        abstract=True
        
class RectifiedDatasetRecord(EODatasetRecord):
    extent = models.ForeignKey(ExtentRecord, related_name="rect_datasets")
    
    class Meta:
        verbose_name = "Rectified Dataset"
        verbose_name_plural = "Rectified Datasets"

class ReferenceableDatasetRecord(EODatasetRecord):
    size_x = models.IntegerField()
    size_y = models.IntegerField()
    
    class Meta:
        verbose_name = "Referenceable Dataset"
        verbose_name_plural = "Referenceable Datasets"

class RectifiedStitchedMosaicRecord(EOCoverageRecord):
    extent = models.ForeignKey(ExtentRecord, related_name="rect_stitched_mosaics")
    image_pattern = models.CharField(max_length=1024)
    storage_dir = models.CharField(max_length=1024)
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord,
                                           null=True, blank=True,
                                           related_name="rect_stitched_mosaics")

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

class DatasetSeriesRecord(Resource):
    eo_id = models.CharField(max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOMetadataRecord,
                                       related_name="dataset_series_set")
    image_pattern = models.CharField(max_length=1024)
    rect_stitched_mosaics = models.ManyToManyField(RectifiedStitchedMosaicRecord,
                                                   blank=True, null=True,
                                                   related_name="dataset_series_set")
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord,
                                           blank=True, null=True,
                                           related_name="dataset_series_set")
    ref_datasets = models.ManyToManyField(ReferenceableDatasetRecord,
                                          blank=True, null=True,
                                          related_name="dataset_series_set")

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "DatasetSeries"
        verbose_name_plural = "DatasetSeries"

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.filter(automatic=True):
            if dataset.dataset_series_set.count() == 1 and \
               dataset.rect_stitched_mosaics.count() == 1:
                dataset.delete()
        for dataset in self.ref_datasets.filter(automatic=True):
            if dataset.dataset_series_set.count() == 1:
                dataset.delete()
        super(DatasetSeriesRecord, self).delete()
        eo_metadata.delete()

class DataDirRecord(models.Model):
    dataset_series = models.ForeignKey(DatasetSeriesRecord, related_name="data_dirs")
    dir = models.CharField(max_length=1024)

    def __unicode__(self):
        return self.dir

    class Meta:
        verbose_name = "Data Directory"
        verbose_name_plural = "Data Directories"
