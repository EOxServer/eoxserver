#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

from eoxserver.backends.models import (
    Location, FTPStorage, RasdamanStorage, LocalPath, 
    RemotePath, RasdamanLocation, CacheFile, 
) 

from django.contrib import admin

#===============================================================================
# Generic Storage Admin (Abstract!)
#===============================================================================

class StorageAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.storage_type = self.model.STORAGE_TYPE
        obj.save()

#===============================================================================
# Local Path
#===============================================================================

class LocalPathAdmin(admin.ModelAdmin):
    model = LocalPath
    
    list_display = ("location_type", "path",)
    list_editable = ("path",)

admin.site.register(LocalPath, LocalPathAdmin)

#===============================================================================
# FTP Storage Admin
#===============================================================================

class RemotePathInline(admin.TabularInline):
    model = RemotePath
    extra = 1
class FTPStorageAdmin(StorageAdmin):
    inlines = (RemotePathInline, )

class RemotePathAdmin(admin.ModelAdmin):
    model = RemotePath
    
    list_display = ("location_type", "path",)
    list_editable = ("path",)

admin.site.register(FTPStorage, FTPStorageAdmin)
admin.site.register(RemotePath, RemotePathAdmin)

#===============================================================================
# Rasdaman Storage Admin
#===============================================================================

class RasdamanLocationInline(admin.TabularInline):
    model = RasdamanLocation
    extra = 1
class RasdamanStorageAdmin(StorageAdmin):
    inlines = (RasdamanLocationInline,)

class RasdamanLocationAdmin(admin.ModelAdmin):
    model = RasdamanLocation
    
    list_display = ("location_type", "collection", "oid")
    list_editable = ("collection", "oid")
    
admin.site.register(RasdamanStorage, RasdamanStorageAdmin)
admin.site.register(RasdamanLocation, RasdamanLocationAdmin)

#===============================================================================
# Cache File Admin
#===============================================================================

class CacheFileAdmin(admin.ModelAdmin):
    pass

admin.site.register(CacheFile, CacheFileAdmin)
