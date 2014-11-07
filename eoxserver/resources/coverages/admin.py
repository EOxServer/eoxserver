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

from django.core.exceptions import ValidationError
from django.contrib.gis import forms
from django.contrib.gis import admin
from django.contrib import messages

from eoxserver.contrib import gdal
from eoxserver.resources.coverages import models
from eoxserver.backends.admin import LocationForm


#===============================================================================
# List display fields
#===============================================================================

def num_coverages(collection):
    return len(filter(models.iscoverage, collection.eo_objects.all()))

num_coverages.short_description = "Coverages contained in this collection"


def num_collections(collection):
    return len(filter(models.iscollection, collection.eo_objects.all()))

num_collections.short_description = "Collections contained in this collection"


#===============================================================================
# Choices
#===============================================================================


def get_projection_format_choices():
    # TODO: replace with dynamic lookup via plugins? or stick with gdal supported stuff?
    return (
        ("WKT", "WKT"),
        ("XML", "XML"),
        ("URL", "URL"),
    )


def get_gdal_data_type_choices():
    return gdal.GDT_TO_NAME.items()


def get_gdal_color_interpretation_choices():
    return gdal.GCI_TO_NAME.items()


#===============================================================================
# ModelForms
#===============================================================================


class NilValueSetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NilValueSetForm, self).__init__(*args, **kwargs)
        self.fields['data_type'] = forms.ChoiceField(
            choices=get_gdal_data_type_choices()
        )


class BandInlineForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BandInlineForm, self).__init__(*args, **kwargs)
        self.fields['data_type'] = forms.ChoiceField(
            choices=get_gdal_data_type_choices()
        )
        self.fields['color_interpretation'] = forms.ChoiceField(
            choices=get_gdal_color_interpretation_choices()
        )


class ProjectionForm(forms.ModelForm):
    """ Form for `Projections`. Overrides the `format` formfield and adds
        choices dynamically.
    """

    def __init__(self, *args, **kwargs):
        super(ProjectionForm, self).__init__(*args, **kwargs)
        self.fields['format'] = forms.ChoiceField(
            choices=get_projection_format_choices()
        )


class CoverageForm(LocationForm):
    pass


#===============================================================================
# Abstract admins
#===============================================================================


class EOObjectAdmin(admin.GeoModelAdmin):
    wms_name = 'EOX Maps'
    wms_url = '//tiles.maps.eox.at/wms/'
    wms_layer = 'terrain'
    default_lon = 16
    default_lat = 48


class CoverageAdmin(EOObjectAdmin):

    form = CoverageForm

    fieldsets = (
        (None, {
            'fields': ('identifier', )
        }),
        ('Metadata', {
            'fields': ('range_type',
                       ('size_x', 'size_y'),
                       ('min_x', 'min_y'),
                       ('max_x', 'max_y'),
                       ('srid', 'projection'),
                       ('begin_time', 'end_time'),
                       'footprint'),
            'description': 'Geospatial metadata'
        }),
    )


class CollectionAdmin(EOObjectAdmin):

    list_display = ("identifier", num_coverages, num_collections)

    def save_related(self, request, form, formsets, change):
        try:
            super(CollectionAdmin, self).save_related(
                request, form, formsets, change
            )
        except ValidationError, e:
            for m in e.messages:
                self.message_user(request, str(m), messages.ERROR)


    def synchronize(self, request, queryset):
        for model in queryset:
            self.message_user(
                request, "Successfully fake-synchronized %s." % str(model),
                messages.INFO
            )

    synchronize.short_description = "Synchronizes the collections with its data sources."

    actions = EOObjectAdmin.actions + ["synchronize"]


class AbstractInline(admin.TabularInline):
    extra = 1


#===============================================================================
# Inline admins
#===============================================================================

class NilValueInline(AbstractInline):
    model = models.NilValue


class BandInline(AbstractInline):
    form = BandInlineForm # TODO: not working as expected...
    model = models.Band
    extra = 0

    def get_queryset(self):
        queryset = super(BandInline, self).get_queryset()
        return queryset.order_by("index")


    #def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # TODO: get only nilvalue sets for the same data type
        #if db_field.name == "nil_value_set":
        #    kwargs["queryset"] = models.NilValueSet.objects.filter(data_type=)


class CollectionInline(AbstractInline):
    model = getattr(models.Collection.eo_objects, "through")
    fk_name = "eo_object"


class EOObjectInline(AbstractInline):
    model = getattr(models.Collection.eo_objects, "through")
    fk_name = "collection"


class DataSourceInline(AbstractInline):
    model = models.DataSource
    form = LocationForm
    extra = 0


class DataItemInline(AbstractInline):
    model = models.backends.DataItem


#===============================================================================
# Model admins
#===============================================================================


class ProjectionAdmin(admin.ModelAdmin):
    model = models.Projection
    form = ProjectionForm

admin.site.register(models.Projection, ProjectionAdmin)


class NilValueSetAdmin(admin.ModelAdmin):
    model = models.RangeType
    form = NilValueSetForm
    inlines = (NilValueInline,)

admin.site.register(models.NilValueSet, NilValueSetAdmin)


class RangeTypeAdmin(admin.ModelAdmin):
    model = models.RangeType
    inlines = (BandInline,)

admin.site.register(models.RangeType, RangeTypeAdmin)


class RectifiedDatasetAdmin(CoverageAdmin):
    model = models.RectifiedDataset
    inlines = (DataItemInline, CollectionInline)

admin.site.register(models.RectifiedDataset, RectifiedDatasetAdmin)


class ReferenceableDatasetAdmin(CoverageAdmin):
    model = models.ReferenceableDataset
    inlines = (DataItemInline, CollectionInline)

admin.site.register(models.ReferenceableDataset, ReferenceableDatasetAdmin)


class RectifiedStitchedMosaicAdmin(CoverageAdmin, CollectionAdmin):
    model = models.RectifiedStitchedMosaic
    inlines = (DataItemInline, CollectionInline, EOObjectInline)

    def restitch(self, request, queryset):
        for model in queryset:
            self.message_user(
                request, "Successfully fake-stitched %s." % str(model),
                messages.INFO
            )

    restitch.short_description = "Restitch the rectified stitched mosaic."

    actions = CollectionAdmin.actions + ["restitch"]

admin.site.register(models.RectifiedStitchedMosaic, RectifiedStitchedMosaicAdmin)


class DatasetSeriesAdmin(CollectionAdmin):
    model = models.DatasetSeries

    fieldsets = (
        (None, {
            'fields': ('identifier',)
        }),
        ('Metadata', {
            'fields': (('begin_time', 'end_time'), 'footprint')
        }),
    )

    inlines = (DataSourceInline, EOObjectInline, CollectionInline)

admin.site.register(models.DatasetSeries, DatasetSeriesAdmin)
