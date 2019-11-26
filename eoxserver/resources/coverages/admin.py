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

from django.contrib.gis import admin
try:
    from django.core.urlresolvers import reverse, NoReverseMatch
except ImportError:
    from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe
from django.conf import settings

from eoxserver.resources.coverages import models


# ==============================================================================
# Inline "Type" model admins
# ==============================================================================


class FieldTypeInline(admin.StackedInline):
    model = models.FieldType
    filter_horizontal = ['nil_values']
    extra = 0

    def get_queryset(self, *args, **kwargs):
        queryset = super(FieldTypeInline, self).get_queryset(*args, **kwargs)
        return queryset.order_by("index")


class MaskTypeInline(admin.TabularInline):
    model = models.MaskType
    extra = 0


class BrowseTypeInline(admin.StackedInline):
    model = models.BrowseType
    extra = 0

    fieldsets = (
        (None, {
            'fields': ('product_type', 'name')
        }),
        ("Red or grey band", {
            'classes': ('collapse', 'collapsed'),
            'fields': (
                'red_or_grey_expression', 'red_or_grey_nodata_value',
                ('red_or_grey_range_min', 'red_or_grey_range_max'),
            )
        }),
        ("Green band", {
            'classes': ('collapse', 'collapsed'),
            'fields': (
                'green_expression', 'green_nodata_value',
                ('green_range_min', 'green_range_max'),
            )
        }),
        ("Blue band", {
            'classes': ('collapse', 'collapsed'),
            'fields': (
                'blue_expression', 'blue_nodata_value',
                ('blue_range_min', 'blue_range_max'),
            )
        }),
        ("Alpha band", {
            'classes': ('collapse', 'collapsed'),
            'fields': (
                'alpha_expression', 'alpha_nodata_value',
                ('alpha_range_min', 'alpha_range_max'),
            )
        })
    )


# ==============================================================================
# Inline admins
# ==============================================================================

class MaskInline(admin.StackedInline):
    model = models.Mask
    extra = 0


class BrowseInline(admin.StackedInline):
    model = models.Browse
    extra = 0


class ProductDataItemInline(admin.StackedInline):
    model = models.ProductDataItem
    extra = 0


class MetaDataItemInline(admin.StackedInline):
    model = models.MetaDataItem
    extra = 0

    def download_link(self, obj):
        try:
            return mark_safe('<a href="{}">Download</a>'.format(
                reverse('metadata', kwargs=dict(
                        identifier=obj.eo_object.identifier,
                        semantic=dict(
                            models.MetaDataItem.SEMANTIC_CHOICES
                        )[obj.semantic]
                    )
                )
            ))
        except (NoReverseMatch, KeyError):
            return mark_safe('<i>Metadata URL not configured.</i>')
    download_link.short_description = 'Download Link'

    readonly_fields = ['download_link']


class ArrayDataItemInline(admin.StackedInline):
    model = models.ArrayDataItem
    extra = 0


class CoverageMetadataInline(admin.StackedInline):
    model = models.CoverageMetadata
    extra = 0


class ProductMetadataInline(admin.StackedInline):
    model = models.ProductMetadata
    extra = 0


class CollectionMetadataInline(admin.StackedInline):
    model = models.CollectionMetadata
    extra = 0


# ==============================================================================
# Abstract admins
# ==============================================================================

class EOObjectAdmin(admin.GeoModelAdmin):
    date_hierarchy = 'inserted'

    @property
    def wms_name(self):
        return getattr(settings, 'EOXS_ADMIN_WMS_NAME', 'EOX Maps')

    @property
    def wms_url(self):
        return getattr(settings, 'EOXS_ADMIN_WMS_URL', '//tiles.maps.eox.at/wms/')

    @property
    def wms_layer(self):
        return getattr(settings, 'EOXS_ADMIN_WMS_LAYER', 'terrain-light')

    @property
    def default_lon(self):
        return getattr(settings, 'EOXS_ADMIN_DEFAULT_LON', 16)

    @property
    def default_lat(self):
        return getattr(settings, 'EOXS_ADMIN_DEFAULT_LAT', 48)

    @property
    def default_zoom(self):
        return getattr(settings, 'EOXS_ADMIN_DEFAULT_ZOOM', 4)

# ==============================================================================
# "Type" model admins
# ==============================================================================


class CoverageTypeAdmin(admin.ModelAdmin):
    inlines = [FieldTypeInline]

admin.site.register(models.CoverageType, CoverageTypeAdmin)


class ProductTypeAdmin(admin.ModelAdmin):
    inlines = [BrowseTypeInline, MaskTypeInline]
    filter_horizontal = ['allowed_coverage_types']

admin.site.register(models.ProductType, ProductTypeAdmin)


class CollectionTypeAdmin(admin.ModelAdmin):
    filter_horizontal = ['allowed_product_types', 'allowed_coverage_types']

admin.site.register(models.CollectionType, CollectionTypeAdmin)


class MaskTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.MaskType, MaskTypeAdmin)


class GridAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Grid, GridAdmin)

# ==============================================================================
# Collection, Product and Coverage admins
# ==============================================================================


class CoverageAdmin(EOObjectAdmin):
    inlines = [CoverageMetadataInline, MetaDataItemInline, ArrayDataItemInline]

admin.site.register(models.Coverage, CoverageAdmin)


class ProductAdmin(EOObjectAdmin):
    inlines = [
        MaskInline, BrowseInline, ProductDataItemInline, MetaDataItemInline, ProductMetadataInline
    ]

admin.site.register(models.Product, ProductAdmin)


class MosaicAdmin(EOObjectAdmin):
    inlines = []

admin.site.register(models.Mosaic, MosaicAdmin)


class CollectionAdmin(EOObjectAdmin):
    inlines = [CollectionMetadataInline]

    actions = ['summary']

    # action to refresh the summary info on a collection
    def summary(self, request, queryset):
        for collection in queryset:
            models.collection_collect_metadata(
                collection, product_summary=True, coverage_summary=True
            )

    summary.short_description = (
        "Update the summary information for each collection"
    )


admin.site.register(models.Collection, CollectionAdmin)


class IndexHiddenAdmin(admin.ModelAdmin):
    """ Admin class that hides on the apps admin index page.
        """
    def get_model_perms(self, request):
        return {}

admin.site.register(models.OrbitNumber, IndexHiddenAdmin)
admin.site.register(models.Track, IndexHiddenAdmin)
admin.site.register(models.Frame, IndexHiddenAdmin)
admin.site.register(models.SwathIdentifier, IndexHiddenAdmin)
admin.site.register(models.ProductVersion, IndexHiddenAdmin)
admin.site.register(models.ProductQualityDegredationTag, IndexHiddenAdmin)
admin.site.register(models.ProcessorName, IndexHiddenAdmin)
admin.site.register(models.ProcessingCenter, IndexHiddenAdmin)
admin.site.register(models.SensorMode, IndexHiddenAdmin)
admin.site.register(models.ArchivingCenter, IndexHiddenAdmin)
admin.site.register(models.ProcessingMode, IndexHiddenAdmin)
admin.site.register(models.AcquisitionStation, IndexHiddenAdmin)
admin.site.register(models.AcquisitionSubType, IndexHiddenAdmin)
