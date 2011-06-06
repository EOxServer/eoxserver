#!/usr/bin/env python
#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
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

from django.conf.urls.defaults import *

# Enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.contrib import databrowse
from django.views.static import serve
from django.conf import settings

#from eoxserver.server.models import *

#databrowse.site.register(EOxSCoverageEOCollectionRecord)
#databrowse.site.register(EOxSCoverageSingleFileRecord)
#databrowse.site.register(EOxSCoverageSingleFileNonGeoRecord)
#databrowse.site.register(EOxSRangeType)
#databrowse.site.register(EOxSRectifiedGridRecord)
#databrowse.site.register(EOxSChannelRecord)
#databrowse.site.register(EOxSDataDirRecord)
#databrowse.site.register(EOxSLayerMetadataRecord)
#databrowse.site.register(EOxSRangeType2Channel)

urlpatterns = patterns('',
    (r'^ows', 'eoxserver.services.views.ows'),
    # Example:
    # (r'^eoxserver/', include('eoxserver.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^databrowse/(.*)', databrowse.site.root),
    (r'^files/(?P<path>.*)$', serve, {'document_root': 'eoxserver'}) # TODO: do not use in production setting
)
