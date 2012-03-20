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

from osgeo import gdalconst
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

from django.contrib.gis.db import models
from django.contrib.gis.geos.polygon import Polygon
from django.contrib.gis.geos.error import GEOSException

from eoxserver.core.models import Resource
from eoxserver.backends.models import (
    Location, LocalPath, RemotePath,
    RasdamanLocation, CacheFile
)
from eoxserver.resources.coverages.validators import (
    validateEOOM, validateCoverageIDnotInEOOM
)

NCNameValidator = RegexValidator(re.compile(r'^[a-zA-z_][a-zA-Z0-9_.-]*$'), message="This field must contain a valid NCName.")

class NilValueRecord(models.Model):
    reason = models.CharField(max_length=128, default="http://www.opengis.net/def/nil/OGC/0/unknown", 
        choices=(
            ("http://www.opengis.net/def/nil/OGC/0/inapplicable", "Inapplicable (There is no value)"),
            ("http://www.opengis.net/def/nil/OGC/0/missing", "Missing"),
            ("http://www.opengis.net/def/nil/OGC/0/template", "Template (The value will be available later)"),
            ("http://www.opengis.net/def/nil/OGC/0/unknown", "Unknown"),
            ("http://www.opengis.net/def/nil/OGC/0/withheld", "Withheld (The value is not divulged)"),
            ("http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange", "Above detection range"),
            ("http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange", "Below detection range")
        )
    )
    value = models.IntegerField()

    def __unicode__(self):
        return self.reason+" "+str(self.value)

    class Meta:
        verbose_name = "Nil Value"

class BandRecord(models.Model):
    name = models.CharField(max_length=256)
    identifier = models.CharField(max_length=256)
    description = models.TextField()
    definition = models.CharField(max_length=256)
    uom = models.CharField("UOM", max_length=16)
    nil_values = models.ManyToManyField(NilValueRecord, null=True, blank=True, verbose_name="Nil Value")
    gdal_interpretation = models.IntegerField("GDAL Interpretation", default=gdalconst.GCI_Undefined,
        choices=(
            (gdalconst.GCI_Undefined, 'Undefined'),
            (gdalconst.GCI_GrayIndex, 'Grayscale'),
            (gdalconst.GCI_PaletteIndex, 'Palette Index'),
            (gdalconst.GCI_RedBand, 'Red'),
            (gdalconst.GCI_GreenBand, 'Green'),
            (gdalconst.GCI_BlueBand, 'Blue'),
            (gdalconst.GCI_AlphaBand, 'Alpha'),
            (gdalconst.GCI_HueBand, 'Hue'),
            (gdalconst.GCI_SaturationBand, 'Saturation'),
            (gdalconst.GCI_LightnessBand, 'Lightness'),
            (gdalconst.GCI_CyanBand, 'Cyan'),
            (gdalconst.GCI_MagentaBand, 'Magenta'),
            (gdalconst.GCI_YellowBand, 'Yellow'),
            (gdalconst.GCI_BlackBand, 'Black')
        )
    )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Band"


class RangeTypeRecord(models.Model):
    name = models.CharField(max_length=256)
    data_type = models.IntegerField(choices=(
        (gdalconst.GDT_Byte, 'Byte'),
        (gdalconst.GDT_UInt16, 'Unsigned Integer 16-bit'),
        (gdalconst.GDT_Int16, 'Signed Integer 16-bit'),
        (gdalconst.GDT_UInt32, 'Unsigned Integer 32-bit'),
        (gdalconst.GDT_Int32, 'Signed Integer 32-bit'),
        (gdalconst.GDT_Float32, 'Floating Point 32-bit'),
        (gdalconst.GDT_Float64, 'Floating Point 64-bit'),
        (gdalconst.GDT_CInt16, 'GDAL CInt 16-bit'),
        (gdalconst.GDT_CInt32, 'GDAL CInt 32-bit'),
        (gdalconst.GDT_CFloat32, 'GDAL CFloat 32-bit'),
        (gdalconst.GDT_CFloat64, 'GDAL CFloat 64-bit')
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

    class Meta:
        verbose_name = "Band in Range type"

class ExtentRecord(models.Model):
    def __unicode__(self):
        return "Extent (SRID=%d; %f, %f, %f, %f; Size: %d x %d)" % (
            self.srid, self.minx, self.miny, self.maxx, self.maxy, self.size_x, self.size_y
        )

    srid = models.IntegerField("SRID")
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

class LineageRecord(models.Model):

    class Meta:
        verbose_name = "Lineage Entry"
        verbose_name_plural = "Lineage Entries"

class EOMetadataRecord(models.Model):
    timestamp_begin = models.DateTimeField("Begin of acquisition")
    timestamp_end = models.DateTimeField("End of acquisition")
    footprint = models.MultiPolygonField(srid=4326)
    eo_gml = models.TextField("EO O&M", blank=True, validators=[validateEOOM]) # validate against schema
    objects = models.GeoManager()

    class Meta:
        verbose_name = "EO Metadata Entry"
        verbose_name_plural = "EO Metadata Entries"

    def __unicode__(self):
        return ("BeginTime: %s" % self.timestamp_begin)
    
    
    def save(self, *args, **kwargs):
        from eoxserver.core.util.timetools import UTCOffsetTimeZoneInfo
        if self.timestamp_begin.tzinfo is None:
            dt = self.timestamp_begin.replace(tzinfo=UTCOffsetTimeZoneInfo())
            self.timestamp_begin = dt.astimezone(UTCOffsetTimeZoneInfo())
            
        if self.timestamp_end.tzinfo is None:
            dt = self.timestamp_end.replace(tzinfo=UTCOffsetTimeZoneInfo())
            self.timestamp_end = dt.astimezone(UTCOffsetTimeZoneInfo())
        models.Model.save(self, *args, **kwargs)
    
    def clean(self):
        pass

class DataSource(models.Model): # Maybe make two sub models for local and remote storages.
    """
    
    """
    location = models.ForeignKey(Location, related_name="data_sources")
    search_pattern = models.CharField(max_length=1024, null=True)
    
    class Meta:
        unique_together = ('location', 'search_pattern')
        
    def __unicode__(self):
        return "%s: %s" % (str(self.location), self.search_pattern)

class DataPackage(models.Model):
    data_package_type = models.CharField(max_length=32, editable=False)
    metadata_format_name = models.CharField(max_length=128, null=True, blank=True)
    
    def __unicode__(self):
        if self.data_package_type == "local":
            return "Local Data Package: %s / %s" % (
                self.localdatapackage.data_location,
                self.localdatapackage.metadata_location,
            )
            
        elif self.data_package_type == "remote":
            return "Remote Data Package: %s / %s" % (
                self.remotedatapackage.data_location,
                self.remotedatapackage.metadata_location,
            )
        elif self.data_package_type == "rasdaman":
            return "Rasdaman Data Package: %s / %s" % (
                self.rasdamandatapackage.data_location,
                self.rasdamandatapackage.metadata_location,
            )
        else:
            return "Unknown location type"

    
class LocalDataPackage(DataPackage):
    DATA_PACKAGE_TYPE = "local"
    
    data_location = models.ForeignKey(LocalPath, related_name="data_file_packages")
    metadata_location = models.ForeignKey(LocalPath, related_name="metadata_file_packages", null=True)

class RemoteDataPackage(DataPackage):
    DATA_PACKAGE_TYPE = "remote"
    
    data_location = models.ForeignKey(RemotePath, related_name="data_file_packages")
    metadata_location = models.ForeignKey(RemotePath, related_name="metadata_file_packages", null=True)
    
    cache_file = models.ForeignKey(CacheFile, related_name="remote_data_packages", null=True)
    
    def delete(self):
        cache_file = self.cache_file
        super(RemoteDataPackage, self).delete()
        cache_file.delete()

class RasdamanDataPackage(DataPackage):
    DATA_PACKAGE_TYPE = "rasdaman"
    
    data_location = models.ForeignKey(RasdamanLocation, related_name="data_packages")
    metadata_location = models.ForeignKey(LocalPath, related_name="rasdaman_metadata_file_packages", null=True)

class TileIndex(models.Model):
    storage_dir = models.CharField(max_length=1024)
    
    class Meta:
        verbose_name = "Tile Index"
        verbose_name_plural = "Tile Indices"

class ReservedCoverageIdRecord(models.Model):
    until = models.DateTimeField()
    request_id = models.CharField(max_length=256, null=True)
    coverage_id = models.CharField("Coverage ID", max_length=256, unique=True, validators=[NCNameValidator])

class CoverageRecord(Resource):
    coverage_id = models.CharField("Coverage ID", max_length=256, unique=True, validators=[NCNameValidator])

    range_type = models.ForeignKey(RangeTypeRecord, on_delete=models.PROTECT)
    layer_metadata = models.ManyToManyField(LayerMetadataRecord, null=True, blank=True)
    automatic = models.BooleanField(default=False) # True means that the dataset was automatically generated from a dataset series's data dir
    data_source = models.ForeignKey(DataSource, related_name="%(class)s_set", null=True, blank=True, on_delete=models.SET_NULL) # Has to be set if automatic is true.

    def clean(self):
        super(CoverageRecord, self).clean()
        if self.automatic and self.data_source is None:
            raise ValidationError('DataSource has to be set if automatic is true.')

class PlainCoverageRecord(CoverageRecord):
    extent = models.ForeignKey(ExtentRecord, related_name = "single_file_coverages")
    data_package = models.ForeignKey(DataPackage, related_name="plain_coverages")

    class Meta:
        verbose_name = "Single File Coverage"
        verbose_name_plural = "Single File Coverages"
        
    def delete(self):
        extent = self.extent
        super(PlainCoverageRecord, self).delete()
        extent.delete()

class EOCoverageMixIn(models.Model):
    eo_id = models.CharField("EO ID", max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOMetadataRecord,
                                       related_name="%(class)s_set",
                                       verbose_name="EO Metadata Entry")
    lineage = models.OneToOneField(LineageRecord, related_name="%(class)s_set")
    
    class Meta:
        abstract = True

    def delete(self):
        eo_metadata = self.eo_metadata
        lineage = self.lineage
        super(EOCoverageMixIn, self).delete()
        eo_metadata.delete()
        lineage.delete()

class EODatasetMixIn(EOCoverageMixIn):
    data_package = models.ForeignKey(DataPackage, related_name="%(class)s_set")
    visible = models.BooleanField(default=False) # True means that the dataset is visible in the GetCapabilities response

    def __unicode__(self):
        return self.eo_id

    class Meta:
        abstract=True
    
    def delete(self):
        data_package = self.data_package
        super(EOCoverageMixIn, self).delete()
        data_package.delete()
        
class RectifiedDatasetRecord(CoverageRecord, EODatasetMixIn):
    extent = models.ForeignKey(ExtentRecord, related_name="rect_datasets")
    
    class Meta:
        verbose_name = "Rectified Dataset"
        verbose_name_plural = "Rectified Datasets"
    
    def clean(self):
        super(RectifiedDatasetRecord, self).clean()
        
        # TODO: this does not work in the admins changelist.save method
        # A wrong WKB is inside the eo_metadata.footprint entry
        try:
            footprint = self.eo_metadata.footprint
            EPSILON = abs((self.extent.maxx - self.extent.minx) / self.extent.size_x)
            bbox = Polygon.from_bbox((self.extent.minx - EPSILON,
                                     self.extent.miny - EPSILON,
                                     self.extent.maxx + EPSILON,
                                     self.extent.maxy + EPSILON)) # TODO: Adjust according to axis order of SRID.
            bbox.set_srid(int(self.extent.srid))
            
            if footprint.srid != bbox.srid:
                footprint.transform(bbox.srs)
            
            if not bbox.contains(footprint):
                raise ValidationError("Extent does not surround footprint. Extent: '%s' Footprint: '%s'" % (str(bbox), str(footprint)))
        except GEOSException:
            pass
        
        validateCoverageIDnotInEOOM(self.coverage_id, self.eo_metadata.eo_gml)
    
    def delete(self):
        extent = self.extent
        super(EOCoverageMixIn, self).delete()
        extent.delete()

class ReferenceableDatasetRecord(CoverageRecord, EODatasetMixIn):
    size_x = models.IntegerField()
    size_y = models.IntegerField()
    
    class Meta:
        verbose_name = "Referenceable Dataset"
        verbose_name_plural = "Referenceable Datasets"
        
    def clean(self):
        super(ReferenceableDatasetRecord, self).clean()
        validateCoverageIDnotInEOOM(self.coverage_id, self.eo_metadata.eo_gml)

class RectifiedStitchedMosaicRecord(CoverageRecord, EOCoverageMixIn):
    extent = models.ForeignKey(ExtentRecord, related_name="rect_stitched_mosaics")
    data_sources = models.ManyToManyField(DataSource,
                                          null=True, blank=True,
                                          related_name="rect_stitched_mosaics")
    tile_index = models.ForeignKey(TileIndex, related_name="rect_stitched_mosaics")
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord,
                                           null=True, blank=True,
                                           related_name="rect_stitched_mosaics",
                                           verbose_name="Rectified Dataset(s)")

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "Stitched Mosaic"
        verbose_name_plural = "Stitched Mosaics"
        
    def clean(self):
        super(RectifiedStitchedMosaicRecord, self).clean()
        
        footprint = self.eo_metadata.footprint
        bbox = Polygon.from_bbox((self.extent.minx, self.extent.miny, 
                                 self.extent.maxx, self.extent.maxy))
        bbox.set_srid(int(self.extent.srid))
        
        if footprint.srid != bbox.srid:
            footprint.transform(bbox.srs)
        
        if not bbox.contains(footprint):
            raise ValidationError(
                "Extent does not surround footprint. Extent: '%s' Footprint: " 
                "'%s'" % (str(bbox), str(footprint))
            )
        
        validateCoverageIDnotInEOOM(self.coverage_id, self.eo_metadata.eo_gml)

    def delete(self):
        tile_index = self.tile_index
        # TODO maybe delete only automatic datasets?
        for dataset in self.rect_datasets.all():
            dataset.delete()
        super(RectifiedStitchedMosaicRecord, self).delete()
        tile_index.delete()
    
class DatasetSeriesRecord(Resource):
    eo_id = models.CharField("EO ID", max_length=256, unique=True, validators=[NCNameValidator])
    eo_metadata = models.OneToOneField(EOMetadataRecord,
                                       related_name="dataset_series_set",
                                       verbose_name="EO Metadata Entry")
    data_sources = models.ManyToManyField(DataSource,
                                          null=True, blank=True,
                                          related_name="dataset_series_set")
    rect_stitched_mosaics = models.ManyToManyField(RectifiedStitchedMosaicRecord,
                                                   blank=True, null=True,
                                                   related_name="dataset_series_set",
                                                   verbose_name="Stitched Mosaic(s)")
    rect_datasets = models.ManyToManyField(RectifiedDatasetRecord,
                                           blank=True, null=True,
                                           related_name="dataset_series_set",
                                           verbose_name="Rectified Dataset(s)")
    ref_datasets = models.ManyToManyField(ReferenceableDatasetRecord,
                                          blank=True, null=True,
                                          related_name="dataset_series_set",
                                          verbose_name="Referenceable Dataset(s)")

    def __unicode__(self):
        return self.eo_id

    class Meta:
        verbose_name = "Dataset Series"
        verbose_name_plural = "Dataset Series"

    def delete(self):
        eo_metadata = self.eo_metadata
        for dataset in self.rect_datasets.filter(automatic=True):
            if dataset.dataset_series_set.count() == 1 and \
               dataset.rect_stitched_mosaics.count() == 0:
                dataset.delete()
        for dataset in self.ref_datasets.filter(automatic=True):
            if dataset.dataset_series_set.count() == 1:
                dataset.delete()
        super(DatasetSeriesRecord, self).delete()
        eo_metadata.delete()
