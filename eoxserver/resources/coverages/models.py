# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

# pep8: disable=E501

import json
from datetime import datetime
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.gis.db import models
from django.contrib.gis.db.models import Extent, Union
from django.db.models import Min, Max, Q
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from model_utils.managers import InheritanceManager

from eoxserver.backends import models as backends
from eoxserver.core.util.timetools import isoformat
from eoxserver.render.browse.generate import (
    parse_expression, extract_fields, BandExpressionError
)


mandatory = dict(null=False, blank=False)
optional = dict(null=True, blank=True)
searchable = dict(null=True, blank=True, db_index=True)

optional_protected = dict(null=True, blank=True, on_delete=models.PROTECT)
mandatory_protected = dict(null=False, blank=False, on_delete=models.PROTECT)

optional_indexed = dict(blank=True, null=True, db_index=True)
common_value_args = dict(
    on_delete=models.SET_NULL, null=True, blank=True,
    related_name="metadatas"
)

name_validators = [
    RegexValidator(
        re.compile(r'^[a-zA-z_][a-zA-Z0-9_]*$'),
        message="This field must contain a valid Name."
    )
]

identifier_validators = [
    RegexValidator(
        re.compile(r'^[a-zA-z_][a-zA-Z0-9_.-]*$'),
        message="This field must contain a valid NCName."
    )
]


def band_expression_validator(band_expression):
    if not band_expression:
        return

    try:
        parse_expression(band_expression)
    except BandExpressionError as e:
        raise ValidationError(str(e))


# ==============================================================================
# "Type" models
# ==============================================================================


class FieldType(models.Model):
    coverage_type = models.ForeignKey('CoverageType', related_name='field_types', **mandatory)
    index = models.PositiveSmallIntegerField(**mandatory)
    identifier = models.CharField(max_length=512, validators=identifier_validators, **mandatory)
    description = models.TextField(**optional)
    definition = models.CharField(max_length=512, **optional)
    unit_of_measure = models.CharField(max_length=64, **optional)
    wavelength = models.FloatField(**optional)
    significant_figures = models.PositiveSmallIntegerField(**optional)
    numbits = models.PositiveSmallIntegerField(**optional)
    signed = models.BooleanField(default=True, **mandatory)
    is_float = models.BooleanField(default=False, **mandatory)

    class Meta:
        ordering = ('index',)
        unique_together = (
            ('index', 'coverage_type'), ('identifier', 'coverage_type')
        )

    def __str__(self):
        return self.identifier


class AllowedValueRange(models.Model):
    field_type = models.ForeignKey(FieldType, related_name='allowed_value_ranges')
    start = models.FloatField(**mandatory)
    end = models.FloatField(**mandatory)


class NilValue(models.Model):
    NIL_VALUE_CHOICES = (
        ("http://www.opengis.net/def/nil/OGC/0/inapplicable", "Inapplicable (There is no value)"),
        ("http://www.opengis.net/def/nil/OGC/0/missing", "Missing"),
        ("http://www.opengis.net/def/nil/OGC/0/template", "Template (The value will be available later)"),
        ("http://www.opengis.net/def/nil/OGC/0/unknown", "Unknown"),
        ("http://www.opengis.net/def/nil/OGC/0/withheld", "Withheld (The value is not divulged)"),
        ("http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange", "Above detection range"),
        ("http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange", "Below detection range")
    )
    field_types = models.ManyToManyField(FieldType, related_name='nil_values', blank=True)
    value = models.CharField(max_length=512, **mandatory)
    reason = models.CharField(max_length=512, choices=NIL_VALUE_CHOICES, **mandatory)


class MaskType(models.Model):
    name = models.CharField(max_length=512, validators=name_validators, **mandatory)
    product_type = models.ForeignKey('ProductType', related_name='mask_types', **mandatory)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (
            ('name', 'product_type'),
        )


class CoverageType(models.Model):
    name = models.CharField(max_length=512, unique=True, validators=name_validators, **mandatory)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=512, unique=True, validators=name_validators, **mandatory)
    allowed_coverage_types = models.ManyToManyField(CoverageType, related_name='allowed_product_types', blank=True)

    def __str__(self):
        return self.name


class CollectionType(models.Model):
    name = models.CharField(max_length=512, unique=True, validators=name_validators, **mandatory)
    allowed_coverage_types = models.ManyToManyField(CoverageType, related_name='allowed_collection_types', blank=True)
    allowed_product_types = models.ManyToManyField(ProductType, related_name='allowed_collection_types', blank=True)

    def __str__(self):
        return self.name


class BrowseType(models.Model):
    product_type = models.ForeignKey(ProductType, related_name="browse_types", **mandatory)
    name = models.CharField(max_length=256, validators=name_validators, blank=True, null=False)

    red_or_grey_expression = models.CharField(max_length=512, validators=[band_expression_validator], **optional)
    green_expression = models.CharField(max_length=512, validators=[band_expression_validator], **optional)
    blue_expression = models.CharField(max_length=512, validators=[band_expression_validator], **optional)
    alpha_expression = models.CharField(max_length=512, validators=[band_expression_validator], **optional)

    red_or_grey_nodata_value = models.FloatField(**optional)
    green_nodata_value = models.FloatField(**optional)
    blue_nodata_value = models.FloatField(**optional)
    alpha_nodata_value = models.FloatField(**optional)

    red_or_grey_range_min = models.FloatField(**optional)
    green_range_min = models.FloatField(**optional)
    blue_range_min = models.FloatField(**optional)
    alpha_range_min = models.FloatField(**optional)

    red_or_grey_range_max = models.FloatField(**optional)
    green_range_max = models.FloatField(**optional)
    blue_range_max = models.FloatField(**optional)
    alpha_range_max = models.FloatField(**optional)

    def __str__(self):
        if self.name:
            return self.name
        return "Default Browse Type for '%s'" % self.product_type

    def clean(self):
        return validate_browse_type(self)

    class Meta:
        unique_together = (
            ('name', 'product_type'),
        )


# ==============================================================================
# Metadata models for each Collection, Product or Coverage
# ==============================================================================


def axis_accessor(pattern, value_map=None):
    def _get(self):
        values = []
        for i in range(1, 5):
            value = getattr(self, pattern % i)
            if value is not None:
                values.append(value_map[value] if value_map else value)
            else:
                break
        return values
    return _get


class Grid(models.Model):
    AXIS_TYPES = [
        (0, 'spatial'),
        (1, 'elevation'),
        (2, 'temporal'),
        (3, 'other'),
    ]

    # allow named grids but also anonymous ones
    name = models.CharField(max_length=256, unique=True, null=True, blank=False, validators=name_validators)

    coordinate_reference_system = models.TextField(**mandatory)

    axis_1_name = models.CharField(max_length=256, **mandatory)
    axis_2_name = models.CharField(max_length=256, **optional)
    axis_3_name = models.CharField(max_length=256, **optional)
    axis_4_name = models.CharField(max_length=256, **optional)

    axis_1_type = models.SmallIntegerField(choices=AXIS_TYPES, **mandatory)
    axis_2_type = models.SmallIntegerField(choices=AXIS_TYPES, **optional)
    axis_3_type = models.SmallIntegerField(choices=AXIS_TYPES, **optional)
    axis_4_type = models.SmallIntegerField(choices=AXIS_TYPES, **optional)

    # using 'char' here, to allow a wide range of datatypes (such as time)
    # when axis_1_offset is null, then this grid is referenceable
    axis_1_offset = models.CharField(max_length=256, **optional)
    axis_2_offset = models.CharField(max_length=256, **optional)
    axis_3_offset = models.CharField(max_length=256, **optional)
    axis_4_offset = models.CharField(max_length=256, **optional)

    resolution = models.PositiveIntegerField(**optional)

    axis_names = property(axis_accessor('axis_%d_name'))
    axis_types = property(axis_accessor('axis_%d_type', dict(AXIS_TYPES)))
    axis_offsets = property(axis_accessor('axis_%d_offset'))

    def __str__(self):
        if self.name:
            return self.name
        elif self.resolution is not None \
                and len(self.coordinate_reference_system) < 15:
            return '%s (%d)' % (
                self.coordinate_reference_system, self.resolution
            )
        return super(Grid, self).__str__()

    def clean(self):
        validate_grid(self)


class GridFixture(models.Model):
    # optional here to allow 'referenceable' coverages
    grid = models.ForeignKey(Grid, **optional_protected)

    axis_1_origin = models.CharField(max_length=256, **optional)
    axis_2_origin = models.CharField(max_length=256, **optional)
    axis_3_origin = models.CharField(max_length=256, **optional)
    axis_4_origin = models.CharField(max_length=256, **optional)

    axis_1_size = models.PositiveIntegerField(**mandatory)
    axis_2_size = models.PositiveIntegerField(**optional)
    axis_3_size = models.PositiveIntegerField(**optional)
    axis_4_size = models.PositiveIntegerField(**optional)

    origin = property(axis_accessor('axis_%d_origin'))
    size = property(axis_accessor('axis_%d_size'))

    class Meta:
        abstract = True


# ==============================================================================
# Actual item models: Collection, Product and Coverage
# ==============================================================================

eo_object_identifier_validators = identifier_validators if getattr(settings, 'EOXS_VALIDATE_IDS_NCNAME', True) else []

@python_2_unicode_compatible
class EOObject(models.Model):
    """ Base class for Collections, Products and Coverages
    """
    identifier = models.CharField(max_length=256, unique=True, validators=eo_object_identifier_validators, **mandatory)

    begin_time = models.DateTimeField(**optional)
    end_time = models.DateTimeField(**optional)
    footprint = models.GeometryField(**optional)

    inserted = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = InheritanceManager()

    def __str__(self):
        return self.identifier


class Collection(EOObject):
    collection_type = models.ForeignKey(CollectionType, related_name='collections', **optional_protected)

    grid = models.ForeignKey(Grid, **optional)


class Mosaic(EOObject, GridFixture):
    coverage_type = models.ForeignKey(CoverageType, related_name='mosaics', **mandatory_protected)

    collections = models.ManyToManyField(Collection, related_name='mosaics', blank=True)


class Product(EOObject):
    product_type = models.ForeignKey(ProductType, related_name='products', **optional_protected)

    collections = models.ManyToManyField(Collection, related_name='products', blank=True)
    package = models.OneToOneField(backends.Storage, **optional_protected)


class Coverage(EOObject, GridFixture):
    coverage_type = models.ForeignKey(CoverageType, related_name='coverages', **optional_protected)

    collections = models.ManyToManyField(Collection, related_name='coverages', blank=True)
    mosaics = models.ManyToManyField(Mosaic, related_name='coverages', blank=True)
    parent_product = models.ForeignKey(Product, related_name='coverages', **optional)


class ReservedIDManager(models.Manager):
    """ Model manager for `ReservedID` models for easier handling. Returns only
        `QuerySets` that contain valid reservations.
        """
    def get_original_queryset(self):
        return super(ReservedIDManager, self).get_queryset()

    def get_queryset(self):
        Q = models.Q
        return self.get_original_queryset().filter(
            Q(until__isnull=True) | Q(until__gt=now())
        )

    def cleanup_reservations(self):
        Q = models.Q
        self.get_original_queryset().filter(
            Q(until__isnull=False) | Q(until__lte=now())
        ).delete()

    def remove_reservation(self, identifier=None, request_id=None):
        if not identifier and not request_id:
            raise ValueError("Either identifier or request ID required")

        if identifier:
            model = self.get_original_queryset().get(identifier=identifier)
            if request_id and model.request_id != request_id:
                raise ValueError(
                    "Given request ID does not match the reservation."
                )
        else:
            model = self.get_original_queryset().get(request_id=request_id)
            model.delete()


class ReservedID(EOObject):
    """ Model to reserve a specific ID. The field `until` can be used to
        specify the end of the reservation.
        """
    until = models.DateTimeField(**optional)
    request_id = models.CharField(max_length=256, **optional)

    objects = ReservedIDManager()


# ==============================================================================
# DataItems subclasses
# ==============================================================================

class MetaDataItem(backends.DataItem):
    SEMANTIC_CHOICES = [
        (0, 'other'),
        (1, 'description'),
        (2, 'documentation'),
        (3, 'thumbnail'),
    ]

    semantic_names = {
        code: name
        for code, name in SEMANTIC_CHOICES
    }

    semantic_codes = {
        name: code
        for code, name in SEMANTIC_CHOICES
    }

    eo_object = models.ForeignKey(EOObject, related_name='metadata_items', **mandatory)
    semantic = models.SmallIntegerField(choices=SEMANTIC_CHOICES, **optional)

    class Meta:
        unique_together = [('eo_object', 'semantic')]



class Browse(backends.DataItem):
    product = models.ForeignKey(Product, related_name='browses', **mandatory)
    browse_type = models.ForeignKey(BrowseType, **optional)
    style = models.CharField(max_length=256, **optional)

    coordinate_reference_system = models.TextField(**mandatory)
    min_x = models.FloatField(**mandatory)
    min_y = models.FloatField(**mandatory)
    max_x = models.FloatField(**mandatory)
    max_y = models.FloatField(**mandatory)
    width = models.PositiveIntegerField(**mandatory)
    height = models.PositiveIntegerField(**mandatory)

    class Meta:
        unique_together = [('product', 'browse_type', 'style')]


class Mask(backends.DataItem):
    product = models.ForeignKey(Product, related_name='masks', **mandatory)
    mask_type = models.ForeignKey(MaskType, **mandatory)

    geometry = models.GeometryField(**optional)


class ProductDataItem(backends.DataItem):
    product = models.ForeignKey(Product, related_name='product_data_items', **mandatory)


class ArrayDataItem(backends.DataItem):
    BANDS_INTERPRETATION_CHOICES = [
        (0, 'fields'),
        (1, 'dimension')
    ]

    coverage = models.ForeignKey(EOObject, related_name='arraydata_items', **mandatory)

    field_index = models.PositiveSmallIntegerField(default=0, **mandatory)
    band_count = models.PositiveSmallIntegerField(default=1, **mandatory)

    subdataset_type = models.CharField(max_length=64, **optional)
    subdataset_locator = models.CharField(max_length=1024, **optional)

    bands_interpretation = models.PositiveSmallIntegerField(default=0, choices=BANDS_INTERPRETATION_CHOICES, **mandatory)

    class Meta:
        unique_together = [('coverage', 'field_index')]


# ==============================================================================
# Additional Metadata Models for Collections, Products and Coverages
# ==============================================================================


class CollectionMetadata(models.Model):
    collection = models.OneToOneField(Collection, related_name='collection_metadata')

    product_type = models.CharField(max_length=256, **optional_indexed)
    doi = models.CharField(max_length=256, **optional_indexed)
    platform = models.CharField(max_length=256, **optional_indexed)
    platform_serial_identifier = models.CharField(max_length=256, **optional_indexed)
    instrument = models.CharField(max_length=256, **optional_indexed)
    sensor_type = models.CharField(max_length=256, **optional_indexed)
    composite_type = models.CharField(max_length=256, **optional_indexed)
    processing_level = models.CharField(max_length=256, **optional_indexed)
    orbit_type = models.CharField(max_length=256, **optional_indexed)
    spectral_range = models.CharField(max_length=256, **optional_indexed)
    wavelength = models.IntegerField(**optional_indexed)
    # hasSecurityConstraints = models.CharField(**optional_indexed)
    # dissemination = models.CharField(**optional_indexed)

    product_metadata_summary = models.TextField(**optional)
    coverage_metadata_summary = models.TextField(**optional)


# ==============================================================================
# "Common value" tables to store string enumerations
# ==============================================================================


class AbstractCommonValue(models.Model):
    value = models.CharField(max_length=256, db_index=True, unique=True)

    def __unicode__(self):
        return self.value

    class Meta:
        abstract = True


class OrbitNumber(AbstractCommonValue):
    pass


class Track(AbstractCommonValue):
    pass


class Frame(AbstractCommonValue):
    pass


class SwathIdentifier(AbstractCommonValue):
    pass


class ProductVersion(AbstractCommonValue):
    pass


class ProductQualityDegredationTag(AbstractCommonValue):
    pass


class ProcessorName(AbstractCommonValue):
    pass


class ProcessingCenter(AbstractCommonValue):
    pass


class SensorMode(AbstractCommonValue):
    pass


class ArchivingCenter(AbstractCommonValue):
    pass


class ProcessingMode(AbstractCommonValue):
    pass


class AcquisitionStation(AbstractCommonValue):
    pass


class AcquisitionSubType(AbstractCommonValue):
    pass


class ProductMetadata(models.Model):
    PRODUCTION_STATUS_CHOICES = (
        (0, 'ARCHIVED'),
        (1, 'ACQUIRED'),
        (2, 'CANCELLED')
    )

    ACQUISITION_TYPE_CHOICES = (
        (0, 'NOMINAL'),
        (1, 'CALIBRATION'),
        (2, 'OTHER')
    )

    ORBIT_DIRECTION_CHOICES = (
        (0, 'ASCENDING'),
        (1, 'DESCENDING')
    )

    PRODUCT_QUALITY_STATUS_CHOICES = (
        (0, 'NOMINAL'),
        (1, 'DEGRAGED')
    )

    POLARISATION_MODE_CHOICES = (
        (0, 'single'),
        (1, 'dual'),
        (2, 'twin'),
        (3, 'quad'),
        (4, 'UNDEFINED')
    )

    POLARISATION_CHANNELS_CHOICES = (
        (0, "HV"),
        (1, "HV, VH"),
        (2, "VH"),
        (3, "VV"),
        (4, "HH, VV"),
        (5, "HH, VH"),
        (6, "HH, HV"),
        (7, "VH, VV"),
        (8, "VH, HV"),
        (9, "VV, HV"),
        (10, "VV, VH"),
        (11, "HH"),
        (12, "HH, HV, VH, VV"),
        (13, "UNDEFINED"),
    )

    ANTENNA_LOOK_DIRECTION_CHOICES = (
        (0, 'LEFT'),
        (1, 'RIGHT')
    )

    product = models.OneToOneField(Product, related_name='product_metadata')

    parent_identifier = models.CharField(max_length=256, **optional_indexed)

    production_status = models.PositiveSmallIntegerField(choices=PRODUCTION_STATUS_CHOICES, **optional_indexed)
    acquisition_type = models.PositiveSmallIntegerField(choices=ACQUISITION_TYPE_CHOICES, **optional_indexed)

    orbit_number = models.ForeignKey(OrbitNumber, **common_value_args)
    orbit_direction = models.PositiveSmallIntegerField(choices=ORBIT_DIRECTION_CHOICES, **optional_indexed)

    track = models.ForeignKey(Track, **common_value_args)
    frame = models.ForeignKey(Frame, **common_value_args)
    swath_identifier = models.ForeignKey(SwathIdentifier, **common_value_args)

    product_version = models.ForeignKey(ProductVersion, **common_value_args)
    product_quality_status = models.PositiveSmallIntegerField(choices=PRODUCT_QUALITY_STATUS_CHOICES, **optional_indexed)
    product_quality_degradation_tag = models.ForeignKey(ProductQualityDegredationTag, **common_value_args)
    processor_name = models.ForeignKey(ProcessorName, **common_value_args)
    processing_center = models.ForeignKey(ProcessingCenter, **common_value_args)
    creation_date = models.DateTimeField(**optional_indexed) # insertion into catalog
    modification_date = models.DateTimeField(**optional_indexed) # last modification in catalog
    processing_date = models.DateTimeField(**optional_indexed)
    sensor_mode = models.ForeignKey(SensorMode, **common_value_args)
    archiving_center = models.ForeignKey(ArchivingCenter, **common_value_args)
    processing_mode = models.ForeignKey(ProcessingMode, **common_value_args)

    # acquisition type metadata
    availability_time = models.DateTimeField(**optional_indexed)
    acquisition_station = models.ForeignKey(AcquisitionStation, **common_value_args)
    acquisition_sub_type = models.ForeignKey(AcquisitionSubType, **common_value_args)
    start_time_from_ascending_node = models.IntegerField(**optional_indexed)
    completion_time_from_ascending_node = models.IntegerField(**optional_indexed)
    illumination_azimuth_angle = models.FloatField(**optional_indexed)
    illumination_zenith_angle = models.FloatField(**optional_indexed)
    illumination_elevation_angle = models.FloatField(**optional_indexed)
    polarisation_mode = models.PositiveSmallIntegerField(choices=POLARISATION_MODE_CHOICES, **optional_indexed)
    polarization_channels = models.PositiveSmallIntegerField(choices=POLARISATION_CHANNELS_CHOICES, **optional_indexed)
    antenna_look_direction = models.PositiveSmallIntegerField(choices=ANTENNA_LOOK_DIRECTION_CHOICES, **optional_indexed)
    minimum_incidence_angle = models.FloatField(**optional_indexed)
    maximum_incidence_angle = models.FloatField(**optional_indexed)
    # for SAR acquisitions
    doppler_frequency = models.FloatField(**optional_indexed)
    incidence_angle_variation = models.FloatField(**optional_indexed)
    # for OPT/ALT
    cloud_cover = models.FloatField(**optional_indexed)
    snow_cover = models.FloatField(**optional_indexed)
    lowest_location = models.FloatField(**optional_indexed)
    highest_location = models.FloatField(**optional_indexed)


class CoverageMetadata(models.Model):
    coverage = models.OneToOneField(Coverage, related_name="coverage_metadata")


# ==============================================================================
# Functions interacting with models. Done here, to keep the model definitions
# as short and concise as possible
# ==============================================================================


class ManagementError(Exception):
    pass


def cast_eo_object(eo_object):
    """ Casts an EOObject to its actual type.
    """
    if isinstance(eo_object, EOObject):
        try:
            return eo_object.collection
        except:
            try:
                return eo_object.mosaic
            except:
                try:
                    return eo_object.product
                except:
                    try:
                        return eo_object.coverage
                    except:
                        pass

    return eo_object


def collection_insert_eo_object(collection, eo_object):
    """ Inserts an EOObject (either a Product or Coverage) into a collection.
        When an EOObject is passed, it is downcast to its actual type. An error
        is raised when an object of the wrong type is passed.
        The collections footprint and time-stamps are adjusted when necessary.
    """
    collection_type = collection.collection_type
    eo_object = cast_eo_object(eo_object)
    if not isinstance(eo_object, (Product, Coverage)):
        raise ManagementError(
            'Cannot insert object of type %r' % type(eo_object).__name__
        )

    if isinstance(eo_object, Product):
        product_type = eo_object.product_type
        allowed = True
        if collection_type and product_type:
            allowed = collection_type.allowed_product_types.filter(
                pk=product_type.pk
            ).exists()

        elif collection_type:
            allowed = False

        if not allowed:
            raise ManagementError(
                'Cannot insert Product as the product type %r is not allowed in '
                'this collection' % product_type.name
            )

        collection.products.add(eo_object)

    elif isinstance(eo_object, Coverage):
        coverage_type = eo_object.coverage_type
        allowed = True
        if collection_type:
            allowed = collection_type.allowed_coverage_types.filter(
                pk=coverage_type.pk
            ).exists()

        if not allowed:
            raise ManagementError(
                'Cannot insert Coverage as the coverage type %r is not allowed '
                'in this collection' % coverage_type.name
            )

        if collection.grid and collection.grid != eo_object.grid:
            raise ManagementError(
                'Cannot insert Coverage as the coverage grid is not '
                'compatible with this collection'
            )

        collection.coverages.add(eo_object)

    if eo_object.footprint:
        if collection.footprint:
            collection.footprint = collection.footprint.union(
                eo_object.footprint
            )
        else:
            collection.footprint = eo_object.footprint

    if eo_object.begin_time:
        collection.begin_time = (
            eo_object.begin_time if not collection.begin_time
            else min(eo_object.begin_time, collection.begin_time)
        )

    if eo_object.end_time:
        collection.end_time = (
            eo_object.end_time if not collection.end_time
            else max(eo_object.end_time, collection.end_time)
        )

    collection.full_clean()
    collection.save()


def collection_exclude_eo_object(collection, eo_object):
    """ Exclude an EOObject (either Product or Coverage) from the collection.
    """
    eo_object = cast_eo_object(eo_object)

    if not isinstance(eo_object, (Product, Coverage)):
        raise ManagementError(
            'Cannot exclude object of type %r' % type(eo_object).__name__
        )

    if isinstance(eo_object, Product):
        collection.products.remove(eo_object)

    elif isinstance(eo_object, Coverage):
        collection.coverage.remove(eo_object)

    collection_collect_metadata(collection,
        eo_object.footprint is not None,
        eo_object.begin_time and eo_object.begin_time == collection.begin_time,
        eo_object.end_time and eo_object.end_time == collection.end_time,
        False
    )


def collection_collect_metadata(collection, collect_footprint=True,
                                collect_begin_time=True, collect_end_time=True,
                                product_summary=False, coverage_summary=False):
    """ Collect metadata
    """

    if collect_footprint or collect_begin_time or collect_end_time:
        aggregates = {}

        if collect_footprint:
            aggregates["footprint"] = Union("footprint")
        if collect_begin_time:
            aggregates["begin_time"] = Min("begin_time")
        if collect_end_time:
            aggregates["end_time"] = Max("end_time")

        values = EOObject.objects.filter(
            Q(coverage__collections=collection) |
            Q(product__collections=collection)
        ).aggregate(**aggregates)

        if collect_footprint:
            collection.footprint = values["footprint"]
        if collect_begin_time:
            collection.begin_time = values["begin_time"]
        if collect_end_time:
            collection.end_time = values["end_time"]

    if product_summary or coverage_summary:
        collection_metadata, _ = CollectionMetadata.objects.get_or_create(
            collection=collection
        )

        if product_summary:
            collection_metadata.product_metadata_summary = json.dumps(
                _collection_metadata(
                    collection, ProductMetadata, 'product'
                ), indent=4, sort_keys=True
            )

        if coverage_summary:
            collection_metadata.coverage_metadata_summary = json.dumps(
                _collection_metadata(
                    collection, CoverageMetadata, 'coverage'
                ), indent=4, sort_keys=True
            )

        collection_metadata.save()


def _collection_metadata(collection, metadata_model, path):
    summary_metadata = {}
    fields = metadata_model._meta.get_fields()

    def is_common_value(field):
        if isinstance(field, models.ForeignKey):
            return issubclass(field.related_model, AbstractCommonValue)
        return False

    # "Value fields": float, ints, dates, etc; displaying a single value
    value_fields = [
        field for field in fields
        if isinstance(field, (
            models.FloatField, models.IntegerField, models.DateTimeField
        )) and not field.choices
    ]

    # choice fields
    choice_fields = [
        field for field in fields if field.choices
    ]

    # "common value" fields
    common_value_fields = [
        field for field in fields
        if is_common_value(field)
    ]

    base_query = metadata_model.objects.filter(
        **{"%s__collections__in" % path: [collection]}
    )

    # get a list of all related common values
    for field in common_value_fields:
        summary_metadata[field.name] = list(
            field.related_model.objects.filter(
                **{"metadatas__%s__collections" % path: collection}
            ).values_list('value', flat=True).distinct()
        )

    # get a list of all related choice fields
    for field in choice_fields:
        summary_metadata[field.name] = [
            dict(field.choices)[raw_value]
            for raw_value in base_query.filter(
                **{"%s__isnull" % field.name: False}
            ).values_list(
                field.name, flat=True
            ).distinct()
        ]

    # get min/max
    aggregates = {}
    for field in value_fields:
        aggregates.update({
            "%s_min" % field.name: Min(field.name),
            "%s_max" % field.name: Max(field.name),
        })
    values = base_query.aggregate(**aggregates)

    for field in value_fields:
        min_ = values["%s_min" % field.name]
        max_ = values["%s_max" % field.name]

        if isinstance(min_, datetime):
            min_ = isoformat(min_)
        if isinstance(max_, datetime):
            max_ = isoformat(max_)

        summary_metadata[field.name] = {
            "min": min_,
            "max": max_,
        }

    return summary_metadata


def mosaic_insert_coverage(mosaic, coverage):
    """ Insert a coverage into a mosaic.
    """

    mosaic = cast_eo_object(mosaic)
    coverage = cast_eo_object(coverage)

    assert isinstance(mosaic, Mosaic)
    assert isinstance(coverage, Coverage)

    grid = mosaic.grid

    if mosaic.coverage_type != coverage.coverage_type:
        raise ManagementError(
            'Cannot insert Coverage %s as its coverage type does not match '
            'the Mosaics coverage type.' % coverage
        )
    elif grid and grid != coverage.grid:
        raise ManagementError(
            'Cannot insert Coverage %s as its grid does not match '
            'the Mosaics grid.' % coverage
        )

    mosaic.coverages.add(coverage)

    # compute EO metadata
    mosaic.begin_time = (
        min(mosaic.begin_time, coverage.begin_time)
        if mosaic.begin_time else coverage.begin_time
    )
    mosaic.end_time = (
        max(mosaic.end_time, coverage.end_time)
        if mosaic.end_time else coverage.end_time
    )
    mosaic.footprint = (
        mosaic.footprint.union(coverage.footprint)
        if mosaic.footprint else coverage.footprint
    )

    if grid:
        # compute new origins and size
        for i in range(1, 5):
            if getattr(grid, 'axis_%d_type' % i) is None:
                break

            # if origin and size were null, use the ones from the coverage
            if getattr(mosaic, 'axis_%d_origin' % i) is None:
                setattr(mosaic, 'axis_%d_origin' % i,
                    getattr(coverage, 'axis_%d_origin' % i)
                )
                setattr(mosaic, 'axis_%d_size' % i,
                    getattr(coverage, 'axis_%d_size' % i)
                )

            else:
                offset = float(getattr(grid, 'axis_%d_offset' % i))
                o_c = float(getattr(coverage, 'axis_%d_origin' % i))
                o_m = float(getattr(mosaic, 'axis_%d_origin' % i))

                # calculate new origin
                if offset < 0:
                    setattr(mosaic, 'axis_%d_origin' % i, max(o_c, o_m))
                else:
                    setattr(mosaic, 'axis_%d_origin' % i, min(o_c, o_m))

                # calculate new size

                # TODO: this is flawed. Use all coverages within the mosaic

                if o_c > o_m:
                    add_size = float(getattr(coverage, 'axis_%d_size' % i))
                else:
                    add_size = float(getattr(mosaic, 'axis_%d_size' % i))

                setattr(
                    mosaic, 'axis_%d_size' % i,
                    (max(o_c, o_m) - min(o_c, o_m)) / offset + add_size
                )

    mosaic.full_clean()
    mosaic.save()


def product_add_coverage(product, coverage):
    """ Add a Coverage to a product.
        When an EOObject is passed, it is downcast to its actual type. An error
        is raised when an object of the wrong type is passed.
        The collections footprint and time-stamps are adjusted when necessary.
    """
    coverage = cast_eo_object(coverage)
    if not isinstance(coverage, Coverage):
        raise ManagementError(
            'Cannot insert object of type %r' % type(coverage).__name__
        )

    product_type = product.product_type
    coverage_type = coverage.coverage_type

    allowed = True
    if product_type:
        allowed = product_type.allowed_coverage_types.filter(
            pk=coverage_type.pk
        ).exists()

    if not allowed:
        raise ManagementError(
            'Cannot insert Coverage as the coverage type %r is not allowed '
            'in this product' % coverage_type.name
        )

    product.coverages.add(coverage)

# ==============================================================================
# Validators
# ==============================================================================


def validate_grid(grid):
    """ Validation function for grids.
    """

    higher_dim = False
    for i in range(4, 0, -1):
        axis_type = getattr(grid, 'axis_%d_type' % i, None)
        axis_name = getattr(grid, 'axis_%d_name' % i, None)
        axis_offset = getattr(grid, 'axis_%d_offset' % i, None)

        attrs = (axis_type, axis_name, axis_offset)

        has_dim = any(attrs)

        # check that when this axis is not set, no higher axis is set
        if not has_dim and higher_dim:
            raise ValidationError(
                'Axis %d not set, but higher axis %d is set.' % (i, higher_dim)
            )

        # check that all of 'name', 'type', and 'offset' is set
        if has_dim and not all(attrs):
            raise ValidationError(
                "For each axis, 'name', 'type', and 'offset' must be set."
            )

        higher_dim = i if has_dim else False


def validate_browse_type(browse_type):
    """ Validate the expressions of the browse type to only reference fields
        available for that browse type.
    """
    expressions = [
        browse_type.red_or_grey_expression,
        browse_type.green_expression,
        browse_type.blue_expression,
        browse_type.alpha_expression,
    ]

    fields = set()
    for expression in expressions:
        try:
            fields |= set(extract_fields(browse_type.red_or_grey_expression))
        except BandExpressionError:
            pass

    all_fields = set(
        FieldType.objects.filter(
            coverage_type__allowed_product_types__browse_types=browse_type,
        ).values_list('identifier', flat=True)
    )

    missing_fields = fields - all_fields
    if missing_fields:
        raise ValidationError(
            "Expressions are referencing unknow field%s: %s. Available field%s: "
            "%s." % (
                "s" if len(missing_fields) > 1 else "",
                ", ".join(("'%s'" % field) for field in missing_fields),
                "s" if len(all_fields) > 1 else "",
                ", ".join(("'%s'" % field) for field in all_fields),
            )
        )

# ==============================================================================
# Utilities
# ==============================================================================


def product_get_metadata(product):
    try:
        product_metadata = product.product_metadata
    except ProductMetadata.DoesNotExist:
        return []

    def get_value(product_metadata, field):
        raw_value = getattr(product_metadata, field.name)
        if isinstance(field, models.ForeignKey):
            return raw_value.value
        elif field.choices:
            return dict(field.choices)[raw_value]
        return raw_value

    return [
        (field.name, get_value(product_metadata, field))
        for field in ProductMetadata._meta.fields
        if field.name not in ('id', 'product') and
        getattr(product_metadata, field.name)
    ]
