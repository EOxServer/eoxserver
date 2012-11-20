#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

import os.path
import logging

from django.contrib.gis import admin
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.admin.util import unquote
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q

from eoxserver.backends.models import (
    Location, LocalPath, RemotePath, RasdamanLocation
)
from eoxserver.resources.coverages.models import (
    EOMetadataRecord, DataSource, TileIndex,
    LayerMetadataRecord, LineageRecord, NilValueRecord,
    RectifiedDatasetRecord, ReferenceableDatasetRecord, BandRecord,
    RangeType2Band, RangeTypeRecord, RectifiedStitchedMosaicRecord,
    PlainCoverageRecord, DatasetSeriesRecord, ExtentRecord, DataPackage,
    LocalDataPackage, RemoteDataPackage, RasdamanDataPackage
)

from eoxserver.core.exceptions import InternalError
from eoxserver.core.system import System
from eoxserver.core.admin import ConfirmationAdmin
from eoxserver.core.util.timetools import UTCOffsetTimeZoneInfo


logger = logging.getLogger(__name__)
System.init()

# NilValue
class NilValueInline(admin.TabularInline):
    model = BandRecord.nil_values.__getattribute__("through")
    extra = 1
class NilValueAdmin(admin.ModelAdmin):
    inlines = (NilValueInline, )
admin.site.register(NilValueRecord, NilValueAdmin)

# RangeType
class RangeType2BandInline(admin.TabularInline):
    model = RangeType2Band
    extra = 1
class RangeTypeAdmin(admin.ModelAdmin):
    inlines = (RangeType2BandInline, )
class BandRecordAdmin(admin.ModelAdmin):
    inlines = (RangeType2BandInline, NilValueInline)
    exclude = ('nil_values', )
admin.site.register(RangeTypeRecord, RangeTypeAdmin)
admin.site.register(BandRecord, BandRecordAdmin)

# SingleFile Coverage
class PlainCoverageLayerMetadataInline(admin.TabularInline):
    model = PlainCoverageRecord.layer_metadata.__getattribute__("through")
    extra = 1
class PlainCoverageAdmin(admin.ModelAdmin):
    #list_display = ('coverage_id', 'filename', 'range_type')
    #list_editable = ('filename', 'range_type')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (PlainCoverageLayerMetadataInline, )
    exclude = ('layer_metadata',)
admin.site.register(PlainCoverageRecord, PlainCoverageAdmin)


class StitchedMosaic2DatasetInline(admin.TabularInline):
    model = RectifiedStitchedMosaicRecord.rect_datasets.__getattribute__("through")
    verbose_name = "Stitched Mosaic to Dataset Relation"
    verbose_name_plural = "Stitched Mosaic to Dataset Relations"
    extra = 1
    can_delete = False
    
    # TODO: this is causing an exception
    '''def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.automatic:
            return self.readonly_fields + (
                'rectifiedstitchedmosaicrecord', #'rectifieddatasetrecord'
            )
        return super(StitchedMosaic2DatasetInline, self).get_readonly_fields(request, obj)'''
    
class DatasetSeries2DatasetInline(admin.TabularInline):
    model = DatasetSeriesRecord.rect_datasets.__getattribute__("through")
    verbose_name = "Dataset Series to Dataset Relation"
    verbose_name_plural = "Dataset Series to Dataset Relations"
    extra = 1
    
    #template ="admin/tabular.html"
    
    #readonly_fields = ('datasetseriesrecord', )
    
    can_delete = False
    
    # TODO: this is causing an exception
    #def get_readonly_fields(self, request, obj=None):
        #return super(DatasetSeries2DatasetInline, self).get_readonly_fields(request, obj)
        #if obj is not None and obj.automatic:
        #    return self.readonly_fields + ('datasetseriesrecord', )
        #
        #    return self.readonly_fields + (
        #        'datasetseriesrecord', #'rectifieddatasetrecord'
        #    )
        #raise
        #return self.readonly_fields#

class DataPackageInline(admin.StackedInline):
    model = DataPackage
    
class LineageInline(admin.StackedInline):
    model = LineageRecord

class LayerMetadata2DatasetInline(admin.StackedInline):
    model = RectifiedDatasetRecord.layer_metadata.__getattribute__("through")
    extra = 1
    can_delete = True

class RectifiedDatasetAdmin(ConfirmationAdmin):
    #list_display = ('coverage_id', 'eo_id', 'data_package', 'range_type', 'extent')
    fields = ('automatic', 'visible', 'coverage_id', 'eo_id', 'range_type', 'extent', 'eo_metadata', 'data_package', 'data_source', 'lineage')
    list_display = ('coverage_id', 'eo_id', 'range_type', 'extent', 'visible')
    #list_editable = ('data_package', 'range_type', 'extent')
    list_editable = ('range_type', 'extent', 'visible')
    list_filter = ('range_type', )
    
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (StitchedMosaic2DatasetInline, DatasetSeries2DatasetInline, LayerMetadata2DatasetInline)
    
    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EODatasetMixIn is
    # called.
    actions = ['really_delete_selected', ]
    def get_actions(self, request):
        actions = super(RectifiedDatasetAdmin, self).get_actions(request)
        if 'delete_selected' in actions: del actions['delete_selected']
        return actions
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        if queryset.count() == 1:
            message_bit = "1 Dataset was"
        else:
            message_bit = "%s Datasets were" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)
    really_delete_selected.short_description = "Delete selected Dataset entries"

    def change_view(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)
        diff = self.get_changes(request, object_id)
        old_automatic, new_automatic = diff.get('automatic', (False, False))
        
        if (old_automatic and new_automatic) or obj.automatic:
            messages.warning(request, "This rectified dataset cannot be changed "
                             "because it is marked as 'automatic'.")
            
        return super(RectifiedDatasetAdmin, self).change_view(request, object_id, *args, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        """
        If the instance is automatic, this method will return a 
        list of disabled fields.
        These cannot be changed by the user, unless he disables
        the `automatic` field.
        """
        if obj is not None and obj.automatic:
            return self.readonly_fields + (
                'coverage_id', 'eo_id', 'eo_metadata',
                'lineage', 'data_package', 'extent',
                'layer_metadata', 
            )
            
        return self.readonly_fields
    
    def require_confirmation(self, diff):
        try:
            old_automatic, new_automatic = diff['automatic']
            if not old_automatic and new_automatic:
                return "You are marking the rectified dataset as automatic. All manual changes will be reset."
        except KeyError:
            pass
        return False  
        
admin.site.register(RectifiedDatasetRecord, RectifiedDatasetAdmin)

class ReferenceableDatasetAdmin(ConfirmationAdmin):
    #list_display = ('coverage_id', 'eo_id', 'data_package', 'range_type', 'size_x', 'size_y')
    fields = ('automatic', 'visible', 'coverage_id', 'eo_id', 'range_type', 'extent', 'eo_metadata', 'data_package', 'lineage')
    list_display = ('coverage_id', 'eo_id', 'range_type', 'extent', 'visible')
    #list_editable = ('data_package', 'range_type', 'extent')
    list_editable = ('range_type', 'extent', 'visible')
    list_filter = ('range_type', )
    
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
# TODO: Separate inline or rewrite existing one:    inlines = (DatasetSeries2DatasetInline, )

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EODatasetMixIn is
    # called.
    actions = ['really_delete_selected', ]
    def get_actions(self, request):
        actions = super(ReferenceableDatasetAdmin, self).get_actions(request)
        if 'delete_selected' in actions: del actions['delete_selected']
        return actions
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        if queryset.count() == 1:
            message_bit = "1 Dataset was"
        else:
            message_bit = "%s Datasets were" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)
    really_delete_selected.short_description = "Delete selected Dataset entries"

    def change_view(self, request, object_id, *args, **kwargs):
        obj = self.get_object(request, object_id)
        diff = self.get_changes(request, object_id)
        old_automatic, new_automatic = diff.get('automatic', (False, False))
        
        if (old_automatic and new_automatic) or obj.automatic:
            messages.warning(request, "This referenceable dataset cannot be changed "
                             "because it is marked as 'automatic'.")
            
        return super(ReferenceableDatasetAdmin, self).change_view(request, object_id, *args, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        """
        If the instance is automatic, this method will return a 
        list of disabled fields.
        These cannot be changed by the user, unless he disables
        the `automatic` field.
        """
        if obj is not None and obj.automatic:
            return self.readonly_fields + (
                'coverage_id', 'eo_id', 'eo_metadata',
                'lineage', 'data_package', 'extent', 'layer_metadata' )
            
        return self.readonly_fields
    
    def require_confirmation(self, diff):
        try:
            old_automatic, new_automatic = diff['automatic']
            if not old_automatic and new_automatic:
                return "You are marking the referenceable dataset as automatic. All manual changes will be reset."
        except KeyError:
            pass
        return False  

admin.site.register(ReferenceableDatasetRecord, ReferenceableDatasetAdmin)

class AbstractContainerAdmin(admin.ModelAdmin):
    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    coverage_manager_intf_id = ""
    container_wrapper_factory_id = ""
    
    def get_manager(self):
        System.init()
        
        return System.getRegistry().findAndBind(
            intf_id="resources.coverages.interfaces.Manager",
            params={
                "resources.coverages.interfaces.res_type": self.coverage_manager_intf_id
            }
        )
    
    def get_wrapper(self, pk):
        raise NotImplementedError()

    def get_actions(self, request):
        actions = super(AbstractContainerAdmin, self).get_actions(request)
        if 'delete_selected' in actions: del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        
        count = queryset.count()
        self.message_user(request, "%d %s were successfully deleted." % (
               count,
               self.model.Meta.verbose_name if count == 1 else self.model._meta.verbose_name_plural
           )
        )
    really_delete_selected.short_description = "Delete selected entries"
    
    
    def save_model(self, request, obj, form, change):
        super(AbstractContainerAdmin, self).save_model(request, obj, form, change)
        self.obj_to_sync = obj
    
    def try_synchronize(self):
        try:
            obj_to_sync = getattr(self, "obj_to_sync")
            System.init()
            mgr = self.get_manager()
            obj_id = self.get_obj_id(obj_to_sync)
            with transaction.commit_on_success():
                mgr.synchronize(obj_id)
        except AttributeError:
            pass
        except obj_to_sync.DoesNotExist:
            pass
    
    def add_view(self, request, *args, **kwargs):
        try:
            ret = super(AbstractContainerAdmin, self).add_view(request, *args, **kwargs)
            self.try_synchronize()
            return ret
        except:
            messages.error(request, "Could not create %s" % self.model._meta.verbose_name)
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, *args, **kwargs):
        try:
            ret = super(AbstractContainerAdmin, self).change_view(request, object_id, *args, **kwargs)
            self.try_synchronize()
            return ret
        except:
            messages.error(request, "Could not change %s" % self.model._meta.verbose_name)
            raise
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, *args, **kwargs):
        try:
            ret = super(AbstractContainerAdmin, self).changelist_view(request, *args, **kwargs)
            self.try_synchronize()
            return ret
        except:
            messages.error(request, "Could not change %s" % self.model._meta.verbose_name)
            raise
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, *args, **kwargs):
        try:
            ret = super(AbstractContainerAdmin, self).delete_view(request, *args, **kwargs)
            # TODO: need synchronization here?
            return ret
        except:
            messages.error(request, "Could not delete %s" % self.model._meta.verbose_name)
            return HttpResponseRedirect("..")
    
class DatasetSeries2StichedMosaicInline(admin.TabularInline):
    model = DatasetSeriesRecord.rect_stitched_mosaics.__getattribute__("through")
    verbose_name = "Dataset Series to Stitched Mosaic Relation"
    verbose_name_plural = "Dataset Series to Stitched Mosaic Relations"
    can_delete = False
    extra = 1
class RectifiedStitchedMosaicAdmin(AbstractContainerAdmin):
    list_display = ('eo_id', 'eo_metadata', )
    list_editable = ('eo_metadata', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    filter_horizontal = ('rect_datasets', )
    inlines = (DatasetSeries2StichedMosaicInline, )
    
    coverage_manager_intf_id = "eo.rect_stitched_mosaic"
    
    # Increase the width of the select boxes of the horizontal filter.
    class Media:
        css = {
            'all': ('/'+settings.MEDIA_URL+'/admin/widgets.css',)
        }
     
    def get_obj_id(self, obj):
        return obj.coverage_id
        
admin.site.register(RectifiedStitchedMosaicRecord, RectifiedStitchedMosaicAdmin)

"""class DataDirInline(admin.TabularInline):
    model = DataDirRecord
    extra = 1
    
    def save_model(self, request, obj, form, change):
        raise # TODO"""

class LayerMetadata2DatasetSeriesInline(admin.StackedInline):
    model = DatasetSeriesRecord.layer_metadata.__getattribute__("through")
    extra = 1
    can_delete = True

class DatasetSeriesAdmin(AbstractContainerAdmin):
    inlines = (LayerMetadata2DatasetSeriesInline,)
    list_display = ('eo_id', 'eo_metadata', )
    list_editable = ('eo_metadata', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    fieldsets = (
        (None, {
            'fields': ('eo_id', 'eo_metadata', 'data_sources' ),
            'description': 'Demo DatasetSeries description.',
        }),
        ('Advanced coverage handling', {
            'classes': ('collapse',),
            'fields': ('rect_stitched_mosaics', 'rect_datasets', 'ref_datasets')
        }),
    )
    filter_horizontal = ('rect_stitched_mosaics', 'rect_datasets', 'ref_datasets')
    
    coverage_manager_intf_id = "eo.dataset_series"

    # Increase the width of the select boxes of the horizontal filter.
    class Media:
        css = {
            'all': ('/'+settings.MEDIA_URL+'/admin/widgets.css',)
        }
        
    def get_obj_id(self, obj):
        return obj.eo_id

admin.site.register(DatasetSeriesRecord, DatasetSeriesAdmin)


class EOMetadataAdmin(admin.GeoModelAdmin):
    wms_url = "http://vmap0.tiles.osgeo.org/wms/vmap0" # TODO: make this configurable
    
    def save_model(self, request, obj, form, change):
        # steps:
        # 1. retrieve EO GML from obj
        # 2. validate against other input values (begin_time, end_time, footprint)
        # 3. validate against schema
        
        self.metadata_object = obj
        
        tzi = UTCOffsetTimeZoneInfo()
        tzi.setOffsets("+", 0, 0)
        
        if obj.timestamp_begin.tzinfo is None:
            dt = obj.timestamp_begin.replace(tzinfo=UTCOffsetTimeZoneInfo())
            obj.timestamp_begin = dt.astimezone(UTCOffsetTimeZoneInfo())
            
        if obj.timestamp_end.tzinfo is None:
            dt = obj.timestamp_end.replace(tzinfo=UTCOffsetTimeZoneInfo())
            obj.timestamp_end = dt.astimezone(UTCOffsetTimeZoneInfo())
        
        super(EOMetadataAdmin, self).save_model(request, obj, form, change)
        
        if obj.timestamp_begin.tzinfo is None:
            raise
        """
        if len(self.metadata_object.eo_gml) > 0:
            # not sure about this:
            # get right metadata interface
            # look for metadata given in gml
            # TODO currently error because no filename given 
            iu = EOxSMetadataInterfaceFactory.getMetadataInterface(None, "eogml") #we got no filename, do we?
            # TODO what if metadata is already set?
            self.metadata_object.footprint = interface.getFootprint()
        """
    
    def save_formset(self, request, form, formset, change):
        """raise
        if formset.model == EOMetadataRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = EOMetadataSynchronizer(self.metadata_object)
            
            try:
                if change:
                    synchronizer.update()
                else:
                    synchronizer.create()
            except:
                logger.error("Error when synchronizing.")
                #transaction.rollback()
                messages.error(request, "Error when synchronizing with file system.")
                #return
                raise
            
            for dataset in changed_datasets:
                if not dataset.automatic:
                    dataset.save()
        else:
            super(EOMetadataAdmin, self).save_formset(request, form, formset, change)
        """
        # SK: don't think we need to override this method, as it should
        # not be called; see also the explanation in the save_formset()
        # method of RectifiedStitchedMosaicAdmin,
        # DatasetSeriesAdmin
        
        super(EOMetadataAdmin, self).save_formset(request, form, formset, change)
    
    def change_view(self, request, object_id, *args, **kwarg):
        obj = self.get_object(request, unquote(object_id))
        try:
            if obj.rectifieddatasetrecord_set.automatic:
                messages.warning(request, "This EO Metadata record cannot be changed because "
                                 "the associated dataset is marked as 'automatic'.")
        except ObjectDoesNotExist:
            pass
        return super(EOMetadataAdmin, self).change_view(request, object_id, *args, **kwarg)
    
    def get_readonly_fields(self, request, obj=None):
        try:
            if obj is not None and obj.rectifieddatasetrecord_set.automatic:
                return self.readonly_fields + (
                    'timestamp_begin', 'timestamp_end',
                    'footprint', 'eo_gml', 'objects'
                )
        except ObjectDoesNotExist:
            pass
        return self.readonly_fields
    
admin.site.register(EOMetadataRecord, EOMetadataAdmin)

class LayerMetadataAdmin(admin.ModelAdmin):
    inlines = (PlainCoverageLayerMetadataInline, )
admin.site.register(LayerMetadataRecord, LayerMetadataAdmin)

admin.site.register(LineageRecord)
admin.site.register(ExtentRecord)
admin.site.register(TileIndex)

class DataSourceAdmin(admin.ModelAdmin):
    model = DataSource
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """ exclude all locations from the query that
        are used within DataPackages.
        """
        
        if db_field.name == 'location':
            kwargs['queryset'] = Location.objects.filter(
                localpath__data_file_packages=None, localpath__metadata_file_packages=None,
                remotepath__data_file_packages=None, remotepath__metadata_file_packages=None,
                rasdamanlocation__data_packages=None, localpath__rasdaman_metadata_file_packages=None
            )
        return super(DataSourceAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(DataSource, DataSourceAdmin)

#===============================================================================
# Data Packages for Datasets
#===============================================================================

class AbstractDataPackageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.data_package_type = self.model.DATA_PACKAGE_TYPE
        obj.save()

class LocalDataPackageAdmin(AbstractDataPackageAdmin):
    model = LocalDataPackage
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in ('data_location', 'metadata_location'): 
            kwargs['queryset'] = LocalPath.objects.filter(
                data_sources=None
            )
        return super(AbstractDataPackageAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class RemoteDataPackageAdmin(AbstractDataPackageAdmin):
    model = RemoteDataPackage

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name in ('data_location', 'metadata_location'): 
            kwargs['queryset'] = RemotePath.objects.filter(
                data_sources=None
            )
        return super(AbstractDataPackageAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

class RasdamanDataPackageAdmin(AbstractDataPackageAdmin):
    model = RasdamanDataPackage
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'data_location': 
            kwargs['queryset'] = RasdamanLocation.objects.filter(
                data_sources=None
            )
        elif db_field.name == 'metadata_location':
            kwargs['queryset'] = LocalPath.objects.filter(
                data_sources=None
            )
        return super(AbstractDataPackageAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(LocalDataPackage, LocalDataPackageAdmin)
admin.site.register(RemoteDataPackage, RemoteDataPackageAdmin)
admin.site.register(RasdamanDataPackage, RasdamanDataPackageAdmin)
