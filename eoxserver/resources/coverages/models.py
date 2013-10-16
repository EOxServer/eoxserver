#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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

import logging
from itertools import chain

from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from django.contrib.gis.geos import MultiPolygon, Polygon

from django.db.models import Min, Max
from django.contrib.gis.db.models import Union

from eoxserver.core import models as base
from eoxserver.contrib import gdal, osr
from eoxserver.backends import models as backends
from eoxserver.resources.coverages.util import detect_circular_reference


logger = logging.getLogger(__name__)

#===============================================================================
# Helpers
#===============================================================================

def iscoverage(eo_object):
    """ Helper to check whether an EOObject is a coverage. """
    return issubclass(eo_object.real_type, Coverage)


def iscollection(eo_object):
    """ Helper to check whether an EOObject is a collection. """
    return issubclass(eo_object.real_type, Collection)


def collect_eo_metadata(qs, insert=None, exclude=None, bbox=False):
    """ Helper function to collect EO metadata from all EOObjects in a queryset, 
    plus additionals from a list and exclude others from a different list. If 
    bbox is `True` then the returned polygon will only be a minimal bounding box
    of the collected footprints.
    """

    values = qs.exclude(
        pk__in=[eo_object.pk for eo_object in exclude or ()]
    ).aggregate(
        begin_time=Min("begin_time"), end_time=Max("end_time"),
        footprint=Union("footprint")
    )

    begin_time, end_time, footprint = (
        values["begin_time"], values["end_time"], values["footprint"]
    )

    for eo_object in insert or ():
        if begin_time is None:
            begin_time = eo_object.begin_time
        elif eo_object.begin_time is not None:
            begin_time = min(begin_time, eo_object.begin_time)

        if end_time is None:
            end_time = eo_object.end_time
        elif eo_object.end_time is not None:
            end_time = max(end_time, eo_object.end_time)

        if footprint is None:
            footprint = eo_object.footprint
        elif eo_object.footprint is not None:
            footprint = footprint.union(eo_object.footprint)

    if not isinstance(footprint, MultiPolygon) and footprint is not None:
        footprint = MultiPolygon(footprint)

    if bbox and footprint is not None:
        footprint = MultiPolygon(Polygon.from_bbox(footprint.extent))

    return begin_time, end_time, footprint


#===============================================================================
# Metadata classes
#===============================================================================

class Projection(models.Model):
    name = models.CharField(max_length=64, unique=True)
    format = models.CharField(max_length=16)

    definition = models.TextField()

    @property
    def spatial_reference(self):
        sr = osr.SpatialReference()

        # TODO: parse definition
        
        return sr

    def __unicode__(self):
        return self.name


class Extent(models.Model):
    min_x = models.FloatField()
    min_y = models.FloatField()
    max_x = models.FloatField()
    max_y = models.FloatField()
    srid = models.PositiveIntegerField(blank=True, null=True)
    projection = models.ForeignKey(Projection, blank=True, null=True)

    @property
    def spatial_reference(self):
        if self.srid is not None:
            sr = osr.SpatialReference()
            sr.ImportFromEPSG(self.srid)
            return sr
        else:
            return self.projection.spatial_reference
    
    @property
    def extent(self):
        """ Returns the extent as a 4-tuple. """
        return self.min_x, self.min_y, self.max_x, self.max_y

    @extent.setter
    def extent(self, value):
        """ Set the extent as a tuple. """
        self.min_x, self.min_y, self.max_x, self.max_y = value

    def clean(self):
        # make sure that neither both nor none of SRID or projections is set
        if self.projection is None and self.srid is None:
            raise ValidationError("No projection or srid given.")
        elif self.projection is not None and self.srid is not None:
            raise ValidationError(
                "Fields 'projection' and 'srid' are mutually exclusive."
            )

    class Meta:
        abstract = True


class EOMetadata(models.Model):
    begin_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    footprint = models.MultiPolygonField(null=True, blank=True)
    
    objects = models.GeoManager()

    @property
    def extent_wgs84(self):
        if self.footprint is None: return None
        return self.footprint.extent

    @property
    def time_extent(self):
        return self.begin_time, self.end_time

    class Meta:
        abstract = True


class AdditionalEOMetadata(backends.DataItem):
    #semantic = models.CharField(max_length=32, null=True, blank=True)
    #coverage = models.ForeignKey("Coverage", related_name="additional_eo_metadata_set")
    pass


class DataSource(backends.Dataset):
    pattern = models.CharField(max_length=32, null=False, blank=False)
    collection = models.ForeignKey("Collection")


#===============================================================================
# Base class EOObject
#===============================================================================

# TODO: encapsulate "casting" mechanism

class EOObject(base.Castable, EOMetadata):
    identifier = models.CharField(max_length=256, unique=True, null=False, blank=False)

    objects = models.GeoManager()

    def __init__(self, *args, **kwargs):
        super(EOObject, self).__init__(*args, **kwargs)
        self._original_begin_time = self.begin_time
        self._original_end_time = self.end_time
        self._original_footprint = self.footprint

    def save(self, *args, **kwargs):
        super(EOObject, self).save(*args, **kwargs)

        # propagate changes of the EO Metadata up in the collection hierarchy
        if (self._original_begin_time != self.begin_time
            or self._original_end_time != self.end_time
            or self._original_footprint != self.footprint):

            for collection in self.collections.all():
                collection.update_eo_metadata()

        # set the new values for subsequent calls to `save()`
        self._original_begin_time = self.begin_time
        self._original_end_time = self.end_time
        self._original_footprint = self.footprint



    def __unicode__(self):
        return "%s (%s)" % (self.identifier, self.real_type._meta.verbose_name)


    class Meta:
        verbose_name = "EO Object"
        verbose_name_plural = "EO Objects"



#===============================================================================
# RangeType structure
#===============================================================================


class NilValueSet(models.Model):
    name = models.CharField(max_length=64)
    data_type = models.PositiveIntegerField()

    def __init__(self, *args, **kwargs):
        super(NilValueSet, self).__init__(*args, **kwargs)
        self._cached_nil_values = None

    @property
    def values(self):
        return [nil_value.value for nil_value in self]

    def __unicode__(self):
        return "%s (%s)" % (self.name, gdal.GetDataTypeName(self.data_type))

    @property
    def cached_nil_values(self):
        if self._cached_nil_values is None:
            self._cached_nil_values = list(self.nil_values.all())
        return self._cached_nil_values

    def __iter__(self):
        return iter(self.cached_nil_values)

    def __len__(self):
        return len(self.cached_nil_values)

    def __getitem__(self, index):
        return self.cached_nil_values[index]

    class Meta:
        verbose_name = "Nil Value Set"


class NilValue(models.Model):
    value_string = models.CharField(max_length=64)
    reason = models.CharField(max_length=64, null=False, blank=False)
    
    nil_value_set = models.ForeignKey(NilValueSet, related_name="nil_values")

    def __unicode__(self):
        return "%s (%s)" % (self.reason, self.value_string)

    @property
    def value(self):
        """ Get the parsed python value from the saved value string.
        """
        dt = self.nil_value_set.data_type
        is_complex = False

        if dt in (gdal.GDT_INTEGRAL_TYPES):
            value =  int(self.value_string)
        elif dt in gdal.GDT_FLOAT_TYPES:
            value =  float(self.value_string)
        elif dt in gdal.GDT_COMPLEX_TYPES:
            value =  complex(self.value_string)
            is_complex = True
        else:
            value = None

        limits = gdal.GDT_NUMERIC_LIMITS.get(dt)

        if limits and value is not None:
            def within(v, low, high):
                return (v >= low and v <= high)

            error = ValueError(
                "Stored value is out of the limits for the data type"
            )
            if not is_complex and not within(value, *limits) :
                raise error
            elif is_complex:
                if (not within(value.real, limits[0].real, limits[1].real)
                    or not within(value.real, limits[0].real, limits[1].real)):
                    raise error
        return value

    def clean(self):
        """ Check that the value can be parsed.
        """
        try:
            _ = self.value
        except Exception, e:
            raise ValidationError(str(e))

    class Meta:
        verbose_name = "Nil Value"


class RangeType(models.Model):
    name = models.CharField(max_length=32, null=False, blank=False, unique=True)


    def __init__(self, *args, **kwargs):
        super(RangeType, self).__init__(*args, **kwargs)
        self._cached_bands = None

    def __unicode__(self):
        return self.name

    @property
    def cached_bands(self):
        if self._cached_bands is None:
            self._cached_bands = list(self.bands.all())
        return self._cached_bands

    def __iter__(self):
        return iter(self.cached_bands)

    def __len__(self):
        return len(self.cached_bands)

    def __getitem__(self, index):
        return self.cached_bands[index]

    class Meta:
        verbose_name = "Range Type"


class Band(models.Model):
    index = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=32, null=False, blank=False)
    identifier = models.CharField(max_length=32, null=False, blank=False)
    description = models.CharField(max_length=32, null=True, blank=True)
    definition = models.CharField(max_length=128, null=True, blank=True)
    uom = models.CharField(max_length=32, null=False, blank=False)
    
    # GDAL specific
    data_type = models.PositiveIntegerField()
    color_interpretation = models.PositiveIntegerField(null=True, blank=True)

    range_type = models.ForeignKey(RangeType, related_name="bands", null=False, blank=False)
    nil_value_set = models.ForeignKey(NilValueSet, null=True, blank=True)


    def __unicode__(self):
        return self.name

    def clean(self):
        nil_value_set = self.nil_value_set
        if nil_value_set and nil_value_set.data_type != self.data_type:
            raise ValidationError(
                "The data type of the band is not equal to the data type of "
                "its nil value set."
            )

    class Meta:
        ordering = ('index',)
        unique_together = (('index', 'range_type'), ('identifier', 'range_type'))


    def __unicode__(self):
        return "%s (%s)" % (self.name, gdal.GetDataTypeName(self.data_type))

    @property
    def allowed_values(self):
        return gdal.GDT_NUMERIC_LIMITS[self.data_type]

    @property
    def significant_figures(self):
        return gdal.GDT_SIGNIFICANT_FIGURES[self.data_type]


#===============================================================================
# Base classes for Coverages and Collections
#===============================================================================


class Coverage(EOObject, Extent, backends.Dataset):
    """ Common base class for all coverage types.
    """
    size_x = models.FloatField()
    size_y = models.FloatField()
    
    range_type = models.ForeignKey(RangeType)

    @property
    def size(self):
        return self.size_x, self.size_y

    @size.setter
    def size(self, value):
        self.size_x, self.size_y = value
    
    objects = models.GeoManager()
    

class Collection(EOObject):
    eo_objects = models.ManyToManyField(EOObject, through="EOObjectToCollectionThrough", related_name="collections")

    objects = models.GeoManager()

    def insert(self, eo_object, through=None):
        # TODO: a collection shall not contain itself!
        if self.pk == eo_object.pk:
            raise ValidationError("A collection cannot contain itself.")

        if through is None:
            # was not invoked by the through model, so create it first. 
            # insert will be invoked again in the `through.save()` method.
            logger.debug("Creating relation model for %s and %s." % (self, eo_object))
            through = EOObjectToCollectionThrough(eo_object=eo_object, collection=self)
            through.full_clean()
            through.save()
            return

        logger.debug("Inserting %s into %s." % (eo_object, self))

        # cast self to actual collection type
        self.cast().perform_insertion(eo_object, through)


    def perform_insertion(self, eo_object, through=None):
        """Interface method for collection insertions. If the insertion is not 
        possible, raise an exception.
        EO metadata collection needs to be done here as-well!
        """

        raise ValidationError("Collection %s cannot insert %s" % (str(self), str(eo_object)))


    def remove(self, eo_object, through=None):
        if through is None:
            EOObjectToCollectionThrough.objects.get(eo_object=eo_object, collection=self).delete()
            return

        logger.debug("Removing %s from %s." % (eo_object, self))
        
        # call actual remove method on actual collection type
        self.cast().perform_removal(eo_object)


    def perform_removal(self, eo_object):
        """ Interface method for collection removals. Update of EO-metadata needs
        to be performed here. Abortion of removal is not possible (atm).
        """
        raise NotImplementedError


    def update_eo_metadata(self):
        logger.debug("Updating EO Metadata for %s." % self)
        self.begin_time, self.end_time, self.footprint = collect_eo_metadata(self.eo_objects.all())
        self.full_clean()
        self.save()

    # containment methods

    def contains(self, eo_object, recursive=False):
        """ Check if an EO object is contained in a collection or subcollection,
        if `recursive` is set to `True`.
        """

        if not isinstance(eo_object, EOObject):
            raise ValueError("Expected EOObject.")

        if self.eo_objects.filter(pk=eo_object.pk).exists():
            return True

        if recursive:
            for collection in self.eo_objects.filter(collection__isnull=False):
                collection = collection.cast()
                if collection.contains(eo_object, recursive):
                    return True

        return False


    def __contains__(self, eo_object):
        """ Shorthand for non-recursive `contains()` method. """
        return self.contains(eo_object)

    def __iter__(self):
        return iter(self.eo_objects.all())

    def iter_cast(self, recursive=False):
        for eo_object in self.eo_objects.all():
            eo_object = eo_object.cast()
            yield eo_object
            if recursive and iscollection(eo_object):
                for item in eo_object.iter_cast(recursive):
                    yield item

    def __len__(self):
        return self.eo_objects.count()


class EOObjectToCollectionThrough(models.Model):
    """Relation of objects to collections. 
    Warning: do *not* use bulk methods of query sets of this collection, as it 
    will not invoke the correct `insert` and `remove` methods on the collection.
    """

    eo_object = models.ForeignKey(EOObject)
    collection = models.ForeignKey(Collection, related_name="coverages_set")

    objects = models.GeoManager()


    def __init__(self, *args, **kwargs):
        super(EOObjectToCollectionThrough, self).__init__(*args, **kwargs)
        try:
            self._original_eo_object = self.eo_object
        except: 
            self._original_eo_object = None

        try:
            self._original_collection = self.collection
        except:
            self._original_collection = None


    def save(self, *args, **kwargs):
        if (self._original_eo_object is not None 
            and self._original_collection is not None
            and (self._original_eo_object != self.eo_object
                 or self._original_collection != self.collection)):
            logger.debug("Relation has been altered!")
            self._original_collection.remove(self._original_eo_object, self)

        def getter(eo_object):
            return eo_object.collections.all()

        if detect_circular_reference(self.eo_object, self.collection, getter):
            raise ValidationError("Circular reference detected.")

        # perform the insertion
        # TODO: this is a bit buggy, as the insertion cannot be aborted this way
        # but if the insertion is *before* the save, then EO metadata collecting
        # still handles previously removed ones.
        self.collection.insert(self.eo_object, self)

        super(EOObjectToCollectionThrough, self).save(*args, **kwargs)

        self._original_eo_object = self.eo_object
        self._original_collection = self.collection


    def delete(self, *args, **kwargs):
        # TODO: pre-remove method? (maybe to cancel remove?)
        logger.debug("Deleting relation model between for %s and %s." % (self.collection, self.eo_object))
        result =  super(EOObjectToCollectionThrough, self).delete(*args, **kwargs)
        self.collection.remove(self.eo_object, self)
        return result


    class Meta:
        unique_together = (("eo_object", "collection"),)
        verbose_name = "EO Object to Collection Relation"
        verbose_name_plural = "EO Object to Collection Relations"


#===============================================================================
# Actual Coverage and Collections
#===============================================================================


class RectifiedDataset(Coverage):
    
    objects = models.GeoManager()
    
    class Meta:
        verbose_name = "Rectified Dataset"
        verbose_name_plural = "Rectified Datasets"


class ReferenceableDataset(Coverage):
    
    objects = models.GeoManager()
    
    class Meta:
        verbose_name = "Referenceable Dataset"
        verbose_name_plural = "Referenceable Datasets"


class RectifiedStitchedMosaic(Coverage, Collection):
    
    objects = models.GeoManager()
    
    class Meta:
        verbose_name = "Rectified Stitched Mosaic"
        verbose_name_plural = "Rectified Stitched Mosaics"

    def perform_insertion(self, eo_object, through=None):
        if eo_object.real_type != RectifiedDataset:
            raise ValidationError("In a %s only %s can be inserted." % (
                RectifiedStitchedMosaic._meta.verbose_name,
                RectifiedDataset._meta.verbose_name_plural
            ))

        # TODO: check that the rectified dataset is on the same "grid" as the 
        # rectified stitched mosaic

        rectified_dataset = eo_object.cast()
        if self.srid != rectified_dataset.srid:
            raise ValidationError(
                "Dataset '%s' has not the same Grid as the Rectified Stitched "
                "Mosaic '%s'." % (rectified_dataset, self.identifier)
            )

        self.begin_time, self.end_time, self.footprint = collect_eo_metadata(
            self.eo_objects.all(), insert=[eo_object]
        )
        self.full_clean()
        self.save()
        return

    def perform_removal(self, eo_object):
        self.begin_time, self.end_time, self.footprint = collect_eo_metadata(
            self.eo_objects.all(), exclude=[eo_object]
        )
        self.full_clean()
        self.save()
        return


class DatasetSeries(Collection):
    
    objects = models.GeoManager()

    class Meta:
        verbose_name = "Dataset Series"
        verbose_name_plural = "Dataset Series"


    def perform_insertion(self, eo_object, through=None):
        self.begin_time, self.end_time, self.footprint = collect_eo_metadata(
            self.eo_objects.all(), insert=[eo_object], bbox=True
        )
        self.full_clean()
        self.save()
        return

    def perform_removal(self, eo_object):
        self.begin_time, self.end_time, self.footprint = collect_eo_metadata(
            self.eo_objects.all(), exclude=[eo_object], bbox=True
        )
        self.full_clean()
        self.save()
        return
