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

from django.contrib.gis import admin
from django.contrib.contenttypes import generic
from django.contrib import messages
from django.db import transaction
from django.conf import settings
from django.http import HttpResponseRedirect

from eoxserver.server.models import *
from eoxserver.server.synchronize import EOxSRectifiedDatasetSeriesSynchronizer, EOxSRectifiedStitchedMosaicSynchronizer
from eoxserver.lib.metadata import EOxSMetadataInterfaceFactory
import os.path
import logging

logging.basicConfig(
    filename=os.path.join(settings.PROJECT_DIR, 'logs', 'eoxserver.log'),
    level=logging.DEBUG,
    format="[%(asctime)s][%(levelname)s] %(message)s"
)

# EOxSGrid
class EOxSAxisInline(admin.TabularInline):
    model = EOxSAxisRecord
    extra = 1
class EOxSRectifiedGridAdmin(admin.ModelAdmin):
    inlines = (EOxSAxisInline, )
admin.site.register(EOxSRectifiedGridRecord, EOxSRectifiedGridAdmin)

# EOxS NilValue
class EOxSNilValueInline(admin.TabularInline):
    model = EOxSChannelRecord.nil_values.through
    extra = 1
class EOxSNilValueAdmin(admin.ModelAdmin):
    inlines = (EOxSNilValueInline, )
admin.site.register(EOxSNilValueRecord, EOxSNilValueAdmin)

# EOxS RangeType
class EOxSRangeType2ChannelInline(admin.TabularInline):
    model = EOxSRangeType2Channel
    extra = 1
class EOxSRangeTypeAdmin(admin.ModelAdmin):
    inlines = (EOxSRangeType2ChannelInline, )
class EOxSChannelRecordAdmin(admin.ModelAdmin):
    inlines = (EOxSRangeType2ChannelInline, EOxSNilValueInline)
    exclude = ('nil_values', )
admin.site.register(EOxSRangeType, EOxSRangeTypeAdmin)
admin.site.register(EOxSChannelRecord, EOxSChannelRecordAdmin)
#admin.site.register(EOxSRangeType2Channel)

# EOxS SingleFile Coverage
class EOxSSingleFileLayerMetadataInline(admin.TabularInline):
    model = EOxSSingleFileCoverageRecord.layer_metadata.through
    extra = 1
class EOxSCoverageSingleFileAdmin(admin.ModelAdmin):
    #list_display = ('coverage_id', 'filename', 'range_type')
    #list_editable = ('filename', 'range_type')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
    inlines = (EOxSSingleFileLayerMetadataInline, )
    exclude = ('layer_metadata',)
admin.site.register(EOxSSingleFileCoverageRecord, EOxSCoverageSingleFileAdmin)

class EOxSRectifiedDatasetAdmin(admin.ModelAdmin):
    list_display = ('coverage_id', 'eo_id', 'file', 'range_type', 'grid', 'contained_in')
    list_editable = ('file', 'range_type', 'grid')
    list_filter = ('range_type', )
    ordering = ('coverage_id', )
    search_fields = ('coverage_id', )
#    inlines = (EOxSSingleFileLayerMetadataInline, )
#    exclude = ('layer_metadata',)

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOxSEOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    def get_actions(self, request):
        actions = super(EOxSRectifiedDatasetAdmin, self).get_actions(request)
        del actions['delete_selected']
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

admin.site.register(EOxSRectifiedDatasetRecord, EOxSRectifiedDatasetAdmin)

class EOxSMosaicDataDirInline(admin.TabularInline):
    model = EOxSMosaicDataDirRecord
    extra = 1
class EOxSRectifiedDatasetInline(generic.GenericTabularInline):
    model = EOxSRectifiedDatasetRecord
    extra = 1
class EOxSRectifiedStitchedMosaicAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    inlines = (EOxSMosaicDataDirInline, EOxSRectifiedDatasetInline)

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOxSEOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]

    def get_actions(self, request):
        actions = super(EOxSRectifiedStitchedMosaicAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s StitchedMosaics were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"

    def save_model(self, request, obj, form, change):
        self.mosaic = obj
        super(EOxSRectifiedStitchedMosaicAdmin, self).save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        if formset.model == EOxSRectifiedDatasetRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = EOxSRectifiedStitchedMosaicSynchronizer(self.mosaic)
            
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
            super(EOxSRectifiedStitchedMosaicAdmin, self).save_formset(request, form, formset, change)
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(EOxSRectifiedStitchedMosaicAdmin, self).add_view(request, form_url, extra_context)
        except:
            messages.error(request, "Could not create StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(EOxSRectifiedStitchedMosaicAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(EOxSRectifiedStitchedMosaicAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change StitchedMosaic")
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(EOxSRectifiedStitchedMosaicAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete StitchedMosaic")
            return HttpResponseRedirect("..")
            
admin.site.register(EOxSRectifiedStitchedMosaicRecord, EOxSRectifiedStitchedMosaicAdmin)

class EOxSDataDirInline(admin.TabularInline):
    model = EOxSDataDirRecord
    extra = 1
class EOxSRectifiedDatasetSeriesAdmin(admin.ModelAdmin):
    list_display = ('eo_id', 'eo_metadata', 'image_pattern')
    list_editable = ('eo_metadata', 'image_pattern')
    list_filter = ('image_pattern', )
    ordering = ('eo_id', )
    search_fields = ('eo_id', )
    inlines = (EOxSDataDirInline, EOxSRectifiedDatasetInline)

    # We need to override the bulk delete function of the admin to make
    # sure the overrode delete() method of EOxSEOCoverageRecord is
    # called.
    actions = ['really_delete_selected', ]
    
    def get_actions(self, request):
        actions = super(EOxSRectifiedDatasetSeriesAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions
        
    def really_delete_selected(self, request, queryset):
        for obj in queryset:
            obj.delete()
        self.message_user(request, "%s DatasetSeries were successfully deleted." % queryset.count())
    really_delete_selected.short_description = "Delete selected entries"
    
    def save_model(self, request, obj, form, change):
        self.dataset_series = obj
        super(EOxSRectifiedDatasetSeriesAdmin, self).save_model(request, obj, form, change)
        
    def save_formset(self, request, form, formset, change):
        # the reason why the synchronization method is placed here
        # instead of the save_model() method is that this is the last step
        # in saving the data filled in in the admin view.
        # At the time the save_model() method is called, the data dir
        # is not yet saved and thus not available. We need the data dirs
        # however for synchronization.
        
        if formset.model == EOxSRectifiedDatasetRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = EOxSRectifiedDatasetSeriesSynchronizer(self.dataset_series)
            
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
            super(EOxSRectifiedDatasetSeriesAdmin, self).save_formset(request, form, formset, change)
        
    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super(EOxSRectifiedDatasetSeriesAdmin, self).add_view(request, form_url, extra_context)
        except:
            messages.error(request, "Could not create DatasetSeries")
            return HttpResponseRedirect("..")
    
    def change_view(self, request, object_id, extra_context=None):
        try:
            return super(EOxSRectifiedDatasetSeriesAdmin, self).change_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect("..")
    
    def changelist_view(self, request, extra_context=None):
        try:
            return super(EOxSRectifiedDatasetSeriesAdmin, self).changelist_view(request, extra_context)
        except:
            messages.error(request, "Could not change DatasetSeries")
            return HttpResponseRedirect("..")
    
    def delete_view(self, request, object_id, extra_context=None):
        try:
            return super(EOxSRectifiedDatasetSeriesAdmin, self).delete_view(request, object_id, extra_context)
        except:
            messages.error(request, "Could not delete DatasetSeries")
            return HttpResponseRedirect("..")

admin.site.register(EOxSRectifiedDatasetSeriesRecord, EOxSRectifiedDatasetSeriesAdmin)


class EOxSEOMetadataAdmin(admin.GeoModelAdmin):
    def save_model(self, request, obj, form, change):
        # steps:
        # 1. retrieve EO GML from obj
        # 2. validate against other input values (begin_time, end_time, footprint)
        # 3. validate against schema
        
        self.metadata_object = obj
        super(EOxSEOMetadataAdmin, self).save_model(request, obj, form, change)
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
        if formset.model == EOxSEOMetadataRecord:
            changed_datasets = formset.save(commit=False)
            
            synchronizer = EOxSEOxSEOMetadataSynchronizer(self.metadata_object)
            
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
            super(EOxSEOMetadataAdmin, self).save_formset(request, form, formset, change)
        """
        # SK: don't think we need to override this method, as it should
        # not be called; see also the explanation in the save_formset()
        # method of EOxSRectifiedStitchedMosaicAdmin,
        # EOxSRectifiedDatasetSeriesAdmin
        
        super(EOxSEOMetadataAdmin, self).save_formset(request, form, formset, change)
    
admin.site.register(EOxSEOMetadataRecord, EOxSEOMetadataAdmin)

class EOxSLayerMetadataAdmin(admin.ModelAdmin):
    inlines = (EOxSSingleFileLayerMetadataInline, )
admin.site.register(EOxSLayerMetadataRecord, EOxSLayerMetadataAdmin)

admin.site.register(EOxSFileRecord)
admin.site.register(EOxSLineageRecord)
