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

from django.contrib.gis import admin
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponseRedirect
from django.contrib.admin.util import unquote

from eoxserver.resources.coverages.models import (
    DataDirRecord, EOMetadataRecord, FileRecord,
    LayerMetadataRecord, LineageRecord, MosaicDataDirRecord, NilValueRecord,
    RectifiedDatasetRecord, BandRecord, RangeType2Band, RangeTypeRecord,
    RectifiedStitchedMosaicRecord, SingleFileCoverageRecord,
    DatasetSeriesRecord, ExtentRecord
)
from eoxserver.resources.coverages.synchronize import (
    DatasetSeriesSynchronizer,
    RectifiedStitchedMosaicSynchronizer,
    SynchronizationErrors
)
from eoxserver.core.exceptions import InternalError
from eoxserver.core.system import System
from eoxserver.core.admin import ConfirmationAdmin

import os.path
import logging

# TODO: harmonize with core.system
logging.basicConfig(
    filename=os.path.join(settings.PROJECT_DIR, 'logs', 'eoxserver.log'),
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)

# Grid
#~ class AxisInline(admin.TabularInline):
    #~ model = AxisRecord
    #~ extra = 1
#~ class RectifiedGridAdmin(admin.ModelAdmin):
    #~ inlines = (AxisInline, )
#~ admin.site.register(RectifiedGridRecord, RectifiedGridAdmin)

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
#admin.site.register(RangeType2Channel)

# SingleFile Coverage
class SingleFileLayerMetadataInline(admin.TabularInline):
    model = SingleFileCoverageRecord.layer_metadata.__getattribute__("through")
    extra = 1
class CoverageSingleFileAdmin(admin.ModelAdmin):
    #list_display = ('coverage_id', 'filename', 'range_type')
    #list_editable = ('filename', 'range_type')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (SingleFileLayerMetadataInline, )
    exclude = ('layer_metadata',)
admin.site.register(SingleFileCoverageRecord, CoverageSingleFileAdmin)


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
    
    can_delete = False
    
    # TODO: this is causing an exception
    '''def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.automatic:
            return self.readonly_fields + (
                'datasetseriesrecord', #'rectifieddatasetrecord'
            )
        return super(DatasetSeries2DatasetInline, self).get_readonly_fields(request, obj)'''

class RectifiedDatasetAdmin(ConfirmationAdmin):
    list_display = ('coverage_id', 'eo_id', 'file', 'range_type', 'extent')
    list_editable = ('file', 'range_type', 'extent')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (StitchedMosaic2DatasetInline, DatasetSeries2DatasetInline)
    
    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
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
    really_delete_selected.short_description = "Delete selected Dataset(s) entries"

    def change_view(self, request, object_id, extra_context=None):
        
        obj = self.get_object(request, unquote(object_id))
        new_obj = self.get_new_object(request, obj)
        if obj.automatic and new_obj.automatic:
            messages.warning(request, "This rectified dataset cannot be changed "
                             "because is marked as 'automatic'.")
        
        return super(RectifiedDatasetAdmin, self).change_view(request, object_id, extra_context)

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
                'lineage', 'file', 'extent',
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

class MosaicDataDirInline(admin.TabularInline):
    model = MosaicDataDirRecord
    verbose_name = "Stitched Mosaic Data Directory"
    verbose_name_plural = "Stitched Mosaic Data Directories"
    extra = 1
class DatasetSeries2StichedMosaicInline(admin.TabularInline):
    model = DatasetSeriesRecord.rect_stitched_mosaics.__getattribute__("through")
    verbose_name = "Dataset Series to Stitched Mosaic Relation"
    verbose_name_plural = "Dataset Series to Stitched Mosaic Relations"
    can_delete = False
    extra = 1
class RectifiedStitchedMosaicAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    filter_horizontal = ('rect_datasets', )
    inlines = (MosaicDataDirInline, DatasetSeries2StichedMosaicInline, )

    # Increase the width of the select boxes of the horizontal filter.
    class Media:
        css = {
            'all': ('/'+settings.MEDIA_URL+'/admin/widgets.css',)
        }

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]

    def get_actions(self, request):
        actions = super(RectifiedStitchedMosaicAdmin, self).get_actions(request)
        if 'delete_selected' in actions: del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s StitchedMosaics were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"

    def save_model(self, request, obj, form, change):
        self.mosaic = obj
        super(RectifiedStitchedMosaicAdmin, self).save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        super(RectifiedStitchedMosaicAdmin, self).save_formset(request, form, formset, change)
        System.init()
        synchronizer = RectifiedStitchedMosaicSynchronizer(self.mosaic)
        try:
            if change:
                synchronizer.update()
            else:
                synchronizer.create()
        except SynchronizationErrors, errors:
            for error in errors:
                messages.error(request, error)
            raise
        except Exception, e:
            messages.error(request, "An unexpected error (%s) occurred during synchronization."%e.__class__.__name__)
            raise
        
        for info in synchronizer.infos:
            messages.info(request, info)
        
        """if formset.model == RectifiedDatasetRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = RectifiedStitchedMosaicSynchronizer(self.mosaic)
            
            try:
                if change:
                    synchronizer.update()
                else:
                    synchronizer.create()
            except:
                logging.error("Error when synchronizing.")
                #transaction.rollback()
                messages.error(request, "Error when synchronizing with file system.")
                #return
                raise
            
            for dataset in changed_datasets:
                if not dataset.automatic:
                    dataset.save()
        else:
            super(RectifiedStitchedMosaicAdmin, self).save_formset(request, form, formset, change)"""
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).add_view(request, form_url, extra_context)
        except:
            messages.error(request, "Could not create StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(RectifiedStitchedMosaicAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete StitchedMosaic")
            return HttpResponseRedirect("..")
            
admin.site.register(RectifiedStitchedMosaicRecord, RectifiedStitchedMosaicAdmin)

class DataDirInline(admin.TabularInline):
    model = DataDirRecord
    extra = 1
    
    def save_model(self, request, obj, form, change):
        raise # TODO

class DatasetSeriesAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    inlines = (DataDirInline, )
    fieldsets = (
        (None, {
            'fields': ('eo_id', 'eo_metadata', 'image_pattern'),
            'description': 'Demo DatasetSeries description.',
        }),
        ('Advanced coverage handling', {
            'classes': ('collapse',),
            'fields': ('rect_stitched_mosaics', 'rect_datasets', 'ref_datasets')
        }),
    )
    filter_horizontal = ('rect_stitched_mosaics', 'rect_datasets', 'ref_datasets')

    # Increase the width of the select boxes of the horizontal filter.
    class Media:
        css = {
            'all': ('/'+settings.MEDIA_URL+'/admin/widgets.css',)
        }

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    
    """
        TODO here
    """
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "rect_datasets":
            pass
            #raise
            #data_dirs = DataDirRecord.objects.get(dataset_series=
            #TODO: get all data dirs
            # exclude all datasets from the query that are included in the dir
            #kwargs["queryset"] = RectifiedDatasetRecord.objects.get(file__path__istartswith="")
        return super(DatasetSeriesAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
    
    def get_actions(self, request):
        actions = super(DatasetSeriesAdmin, self).get_actions(request)
        if 'delete_selected' in actions: del actions['delete_selected']
        return actions
        
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s DatasetSeries were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"
    
    def save_model(self, request, obj, form, change):
        self.dataset_series = obj
        error = False
        
        
        #TODO
        """for data_dir in obj.data_dirs.all():
            try:
                files = findFiles(data_dir.dir, obj.image_pattern)
            except OSError, e:
                messages.error(request, "%s: %s"%(e.strerror, e.filename))
                continue
            
            for dataset in obj.rect_datasets.all():
                if dataset.file.path in files:
                    messages.error(request, "The dataset with the id %s is already included in the data directory %s"%(dataset.eo_id, data_dir.dir))
                    error = True"""
        
        #raise
        
        if not error:
            super(DatasetSeriesAdmin, self).save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        #if formset.model == DataDirRecord:
        
        super(DatasetSeriesAdmin, self).save_formset(request, form, formset, change)
        System.init()
        
        wrapper = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesWrapper")
        wrapper.setModel(self.dataset_series)
        wrapper.setMutable()
        
        synchronizer = DatasetSeriesSynchronizer(wrapper)
        try:
            if change:
                synchronizer.update()
            else:
                synchronizer.create()
        except SynchronizationErrors, errors:
            for error in errors:
                messages.error(request, error)
            raise
        except InternalError:
            raise
        except:
            messages.error(request, "An unexpected error occurred during synchronization")
            raise
        
        for info in synchronizer.infos:
            messages.info(request, info)
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(DatasetSeriesAdmin, self).add_view(request, form_url, extra_context)
        except:
            raise
            messages.error(request, "Could not create DatasetSeries")
            return HttpResponseRedirect(".")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(DatasetSeriesAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect(".")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(DatasetSeriesAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect(".")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(DatasetSeriesAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete DatasetSeries")
            return HttpResponseRedirect(".")

admin.site.register(DatasetSeriesRecord, DatasetSeriesAdmin)


class EOMetadataAdmin(admin.GeoModelAdmin):
    def save_model(self, request, obj, form, change):
        # steps:
        # 1. retrieve EO GML from obj
        # 2. validate against other input values (begin_time, end_time, footprint)
        # 3. validate against schema
        
        self.metadata_object = obj
        super(EOMetadataAdmin, self).save_model(request, obj, form, change)
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
                logging.error("Error when synchronizing.")
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
    
    def change_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, unquote(object_id))
        if obj.rectifieddatasetrecord_set.automatic:
            messages.warning(request, "This EO Metadata record cannot be changed because "
                             "the associated dataset is marked as 'automatic'.")
        return super(EOMetadataAdmin, self).change_view(request, object_id, extra_context)
    
    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.rectifieddatasetrecord_set.automatic:
            return self.readonly_fields + (
                'timestamp_begin', 'timestamp_end',
                'footprint', 'eo_gml', 'objects'
            )
        return self.readonly_fields
    
admin.site.register(EOMetadataRecord, EOMetadataAdmin)

class LayerMetadataAdmin(admin.ModelAdmin):
    inlines = (SingleFileLayerMetadataInline, )
admin.site.register(LayerMetadataRecord, LayerMetadataAdmin)

admin.site.register(FileRecord)
admin.site.register(LineageRecord)
admin.site.register(ExtentRecord)
