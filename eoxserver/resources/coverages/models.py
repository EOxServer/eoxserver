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

from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from model_utils.managers import InheritanceManager

from eoxserver.backends import models as backends


mandatory = dict(null=False, blank=False)
optional = dict(null=True, blank=True)
searchable = dict(null=True, blank=True, db_index=True)

optional_protected = dict(null=True, blank=True, on_delete=models.PROTECT)
mandatory_protected = dict(null=False, blank=False, on_delete=models.PROTECT)


# ==============================================================================
# "Type" models
# ==============================================================================


class FieldType(models.Model):
    coverage_type = models.ForeignKey('CoverageType', related_name='field_types', **mandatory)
    index = models.PositiveSmallIntegerField(**mandatory)
    identifier = models.CharField(max_length=512, **mandatory)
    description = models.TextField(**optional)
    definition = models.CharField(max_length=512, **optional)
    unit_of_measure = models.CharField(max_length=64, **mandatory)
    wavelength = models.FloatField(**optional)

    class Meta:
        ordering = ('index',)
        unique_together = (
            ('index', 'coverage_type'), ('identifier', 'coverage_type')
        )

    def __str__(self):
        return self.identifier


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
    name = models.CharField(max_length=512, **mandatory)
    product_type = models.ForeignKey('ProductType', related_name='mask_types', **mandatory)

    def __str__(self):
        return self.name


class CoverageType(models.Model):
    name = models.CharField(max_length=512, unique=True, **mandatory)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=512, unique=True, **mandatory)
    allowed_coverage_types = models.ManyToManyField(CoverageType, blank=True)

    def __str__(self):
        return self.name


class CollectionType(models.Model):
    name = models.CharField(max_length=512, unique=True, **mandatory)
    allowed_coverage_types = models.ManyToManyField(CoverageType, blank=True)
    allowed_product_types = models.ManyToManyField(ProductType, blank=True)

    def __str__(self):
        return self.name


class BrowseType(models.Model):
    product_type = models.ForeignKey(ProductType, **mandatory)
    name = models.CharField(max_length=256, **mandatory)

    red_or_grey_expression = models.CharField(max_length=512, **mandatory)
    green_expression = models.CharField(max_length=512, **optional)
    blue_expression = models.CharField(max_length=512, **optional)
    alpha_expression = models.CharField(max_length=512, **optional)

    def __str__(self):
        return self.name


# ==============================================================================
# Metadata models for each Collection, Product or Coverage
# ==============================================================================

class Grid(models.Model):
    AXIS_TYPES = [
        (0, 'spatial'),
        (1, 'elevation'),
        (2, 'temporal'),
        (3, 'other'),
    ]

    # allow named grids but also anonymous ones
    name = models.CharField(max_length=256, unique=True, null=True, blank=False)

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
    axis_1_offset = models.CharField(max_length=256, **mandatory)
    axis_2_offset = models.CharField(max_length=256, **optional)
    axis_3_offset = models.CharField(max_length=256, **optional)
    axis_4_offset = models.CharField(max_length=256, **optional)

    def __str__(self):
        pass

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

    class Meta:
        abstract = True


# ==============================================================================
# Actual item models: Collection, Product and Coverage
# ==============================================================================


@python_2_unicode_compatible
class EOObject(models.Model):
    """ Base class for Collections, Products and Coverages
    """
    identifier = models.CharField(max_length=256, unique=True, **mandatory)

    begin_time = models.DateTimeField(**optional)
    end_time = models.DateTimeField(**optional)
    footprint = models.GeometryField(**optional)

    objects = InheritanceManager()

    def __str__(self):
        return self.identifier


class Collection(EOObject):
    collection_type = models.ForeignKey(CollectionType, **optional_protected)

    grid = models.ForeignKey(Grid, **optional)


class Product(EOObject):
    product_type = models.ForeignKey(ProductType, **optional_protected)
    collections = models.ManyToManyField(Collection, related_name='products', blank=True)
    package = models.OneToOneField(backends.Storage, **optional_protected)


class Coverage(EOObject, GridFixture):
    coverage_type = models.ForeignKey(CoverageType, **optional_protected)

    collections = models.ManyToManyField(Collection, related_name='coverages', blank=True)
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


# ==============================================================================
# Additional Metadata Models for Collections, Products and Coverages
# ==============================================================================


class CollectionMetadata(models.Model):
    collection = models.OneToOneField(Collection, related_name='collection_metadata')
    # ...


class CollectionSummaryMetadata(models.Model):
    """ Store summary information about all Coverages/Products in the
        collection for quick display.
    """
    collection = models.OneToOneField(Collection, related_name='summary_metadata')
    # ...


class ProductMetadata(models.Model):
    product = models.OneToOneField(Product, related_name='product_metadata')
    # ...


    name = models.CharField(max_length=512, unique=True, **mandatory)


class CollectionMetadata(models.Model):
    collection = models.OneToOneField(Collection, related_name="metadata")
    
    product_type = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    doi = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    platform = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    platform_serial_identifier = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    instrument = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    sensor_type = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    composite_type = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    processing_level = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    orbit_type = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    spectral_range = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    wavelength = models.IntegerField(blank=True, null=True, db_index=True)
# hasSecurityConstraints = models.CharField(blank=True, null=True, index=True)
# dissemination = models.CharField(blank=True, null=True, index=True)

PRODUCTION_STATUS_CHOICES = (
                             ('0', 'ARCHIVED'),
                             ('1', 'ACQUIRED'),
                             ('2', 'CANCELLED')
                             )

ACQUISITION_TYPE_CHOICES = (
                            ('N', 'NOMINAL'),
                            ('C', 'CALIBRATION'),
                            ('O', 'OTHER')
                            )

ORBIT_DIRECTION_CHOICES = (
                           ('A', 'ASCENDING'),
                           ('D', 'DESCENDING')
                           )

PRODUCT_QUALITY_STATUS_CHOICES = (
                                  ('N', 'NOMINAL'),
                                  ('D', 'DEGRAGED')
                                  )

common_value_args = dict(
                         on_delete=models.SET_NULL, null=True, blank=True
                         )


class AbstractCommonValue(models.Model):
    value = models.CharField(max_length=256, unique=True)
    
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


class Product(models.Model):
    coverage = models.OneToOneField(Coverage, related_name="product_metadata")
    
    parent_identifier = models.CharField(max_length=256, null=True, blank=True)
    
    production_status = models.CharField(max_length=1, null=True, blank=True, choices=PRODUCTION_STATUS_CHOICES)
    acquisition_type = models.CharField(max_length=1, null=True, blank=True, choices=ACQUISITION_TYPE_CHOICES)
    
    orbit_number = models.ForeignKey(OrbitNumber, **common_value_args)
    orbit_direction = models.CharField(max_length=1, null=True, blank=True, choices=ORBIT_DIRECTION_CHOICES)
    
    track = models.ForeignKey(Track, **common_value_args)
    frame = models.ForeignKey(Frame, **common_value_args)
    swath_identifier = models.ForeignKey(SwathIdentifier, **common_value_args)
    
    product_version = models.ForeignKey(ProductVersion, **common_value_args)
    product_quality_status = models.CharField(max_length=1, null=True, blank=True, choices=PRODUCT_QUALITY_STATUS_CHOICES)
    product_quality_degradation_tag = models.ForeignKey(ProductQualityDegredationTag, **common_value_args)
    processor_name = models.ForeignKey(ProcessorName, **common_value_args)
    processing_center = models.ForeignKey(ProcessingCenter, **common_value_args)
    creation_date = models.DateTimeField(null=True, blank=True) # insertion into catalog
    modification_date = models.DateTimeField(null=True, blank=True) # last modification in catalog
    processing_date = models.DateTimeField(null=True, blank=True)
    sensor_mode = models.ForeignKey(SensorMode, **common_value_args)
    archiving_center = models.ForeignKey(ArchivingCenter, **common_value_args)
    processing_mode = models.ForeignKey(ProcessingMode, **common_value_args)


class CoverageMetadata(models.Model):
    coverage = models.OneToOneField(Coverage, related_name="metadata")
    
    availability_time = models.DateTimeField(null=True, blank=True)
    acquisition_station = models.ForeignKey(AcquisitionStation, **common_value_args)
    acquisition_sub_type = models.ForeignKey(AcquisitionSubType, **common_value_args)
    start_time_from_ascending_node = models.IntegerField(null=True, blank=True)
    completion_time_from_ascending_node = models.IntegerField(null=True, blank=True)
    illumination_azimuth_angle = models.FloatField(null=True, blank=True)
    illumination_zenith_angle = models.FloatField(null=True, blank=True)
    illumination_elevation_angle = models.FloatField(null=True, blank=True)

POLARISATION_MODE_CHOICES = (
                             ('S', 'single'),
                             ('D', 'dual'),
                             ('T', 'twin'),
                             ('Q', 'quad'),
                             ('U', 'UNDEFINED')
                             )

POLARISATION_CHANNELS_CHOICES = (
                                 ('a', "HV"),
                                 ('b', "HV, VH"),
                                 ('c', "VH"),
                                 ('d', "VV"),
                                 ('e', "HH, VV"),
                                 ('f', "HH, VH"),
                                 ('g', "HH, HV"),
                                 ('h', "VH, VV"),
                                 ('i', "VH, HV"),
                                 ('j', "VV, HV"),
                                 ('k', "VV, VH"),
                                 ('l', "HH"),
                                 ('m', "HH, HV, VH, VV"),
                                 ('u', "UNDEFINED"),
                                 )

ANTENNA_LOOK_DIRECTION_CHOICES = (
                                  ('L', 'LEFT'),
                                  ('R', 'RIGHT')
                                  )

class SARMetadata(CoverageMetadata):
    polarisation_mode = models.CharField(max_length=1, null=True, blank=True, choices=POLARISATION_MODE_CHOICES)
    polarization_channels = models.CharField(max_length=1, null=True, blank=True, choices=POLARISATION_CHANNELS_CHOICES)
    antenna_look_direction = models.CharField(max_length=1, null=True, blank=True, choices=ANTENNA_LOOK_DIRECTION_CHOICES)
    minimum_incidence_angle = models.FloatField(null=True, blank=True)
    maximum_incidence_angle = models.FloatField(null=True, blank=True)
    doppler_frequency = models.FloatField(null=True, blank=True)
    incidence_angle_variation = models.FloatField(null=True, blank=True)


class OPTMetadata(CoverageMetadata):
    cloud_cover = models.FloatField(null=True, blank=True)  # 0-100
    snow_cover = models.FloatField(null=True, blank=True)  # 0-100


class ALTMetadata(CoverageMetadata):
    cloud_cover = models.FloatField(null=True, blank=True)
    snow_cover = models.FloatField(null=True, blank=True)
    lowest_location = models.FloatField(null=True, blank=True)
    highest_location = models.FloatField(null=True, blank=True)


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
        return eo_object.collection or eo_object.product or eo_object.coverage
    return eo_object


def collection_insert_eo_object(collection, eo_object):
    """ Inserts an EOObject (either a Product or Coverage) into a collection.
        When an EOObject is passed, it is downcast to its actual type. An error
        is raised when an object of the wrong type is passed.
        The collections footprint and time-stamps are adjusted when necessary.
    """
    eo_object = cast_eo_object(eo_object)
    if not isinstance(eo_object, (Product, Coverage)):
        raise ManagementError(
            'Cannot insert object of type %r' % type(eo_object).__name__
        )

    if isinstance(eo_object, Product):
        product_type = eo_object.product_type
        allowed = collection.collection_type.allowed_product_types.filter(
            pk=product_type.pk
        ).exists()

        if not allowed:
            raise ManagementError(
                'Cannot insert Product as the product type %r is not allowed in '
                'this collection' % product_type.name
            )

        collection.products.add(eo_object)

    elif isinstance(eo_object, Coverage):
        coverage_type = eo_object.coveraget_type
        allowed = collection.collection_type.allowed_coverage_types.filter(
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

    try:
        summary_metadata = collection.summary_metadata
        # TODO: collect summary metadata as-well
        summary_metadata
    except CollectionSummaryMetadata.DoesNotExist:
        pass

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
        # TODO remove
        pass
    elif isinstance(eo_object, Coverage):
        # TODO: remove
        pass

    if eo_object.footprint:
        # TODO: recalc footprint
        pass

    if eo_object.begin_time:
        # TODO: recalc begin_time
        pass

    if eo_object.end_time:
        # TODO: recalc end_time
        pass


def product_add_coverage(product, coverage):
    """ Inserts a Coverage into a collection.
        When an EOObject is passed, it is downcast to its actual type. An error
        is raised when an object of the wrong type is passed.
        The collections footprint and time-stamps are adjusted when necessary.
    """
    coverage = cast_eo_object(coverage)
    if not isinstance(coverage, Coverage):
        raise ManagementError(
            'Cannot insert object of type %r' % type(coverage).__name__
        )

    coverage_type = coverage.coveraget_type
    allowed = product.product_type.allowed_coverage_types.filter(
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
