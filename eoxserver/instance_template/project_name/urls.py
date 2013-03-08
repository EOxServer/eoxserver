#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2012 EOX IT Services GmbH
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

"""
URLs config for EOxServer's {{ project_name }} instance.

"""
from django.conf.urls import patterns, include, url

# Enable the admin:
from django.contrib import admin
admin.autodiscover()
# Enable the databrowse:
#from django.contrib import databrowse

# Enable the ATP auxiliary views:
from eoxserver.resources.processes import views as procViews

urlpatterns = patterns('',
    (r'^$', 'eoxserver.views.index'),
    (r'^ows', 'eoxserver.services.views.ows'),
    (r'^logview', 'eoxserver.logging.views.logview'),
    (r'^client/$', 'eoxserver.webclient.views.index'),
    (r'^client/(.*)', 'eoxserver.webclient.views.webclient'),

    # Enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    # Enable the databrowse:
    #(r'^databrowse/(.*)', databrowse.site.root),

    # Uncomment following lines to enable the ATP views:
    #(r'^process/status$', procViews.status ),
    #(r'^process/status/(?P<requestType>[^/]{,64})/(?P<requestID>[^/]{,64})$', procViews.status ),
    #(r'^process/task$', procViews.task ),
    (r'^process/response/(?P<requestType>[^/]{,64})/(?P<requestID>[^/]{,64})', procViews.response ),
)
