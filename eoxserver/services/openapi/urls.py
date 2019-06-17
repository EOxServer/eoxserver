# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from django.conf.urls import url, include

from eoxserver.services.openapi import views


urlpatterns = ([
    url(r'^collections/$', views.collections, name='collections'),
    url(r'^collections/(?P<collection_id>[^/]+)/', include([
        url(r'^$', views.collection, name='collection'),
        url(r'^coverages/$', views.coverages, name='coverages'),
        url(r'^coverages/(?P<coverage_id>[^/]+)/', include([
            url(r'^$', views.coverage, name='coverage'),
            url(r'^domainset$', views.domainset, name='domainset'),
            url(r'^rangetype$', views.rangetype, name='rangetype'),
            url(r'^metadata$', views.metadata, name='metadata'),
            url(r'^rangeset$', views.rangeset, name='rangeset'),
        ], namespace='coverage')),
    ], namespace='collection')),
], 'openapi')
