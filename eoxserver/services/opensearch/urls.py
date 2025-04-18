# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2015 EOX IT Services GmbH
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


try:
    from django.conf.urls import include, url as re_path
except ImportError:
    from django.urls import include, re_path

from eoxserver.services.config import apply_cache_header
from eoxserver.services.opensearch.views import description, search


search_cached = apply_cache_header(search)

app_name = 'opensearch'
urlpatterns = [
    re_path(r'^$', description, name='description'),
    re_path(r'^(?P<format_name>[^/]+)/$', search_cached, name='search'),
    re_path(r'^collections/(?P<collection_id>[^/]+)/', include(([
        re_path(r'^$', description, name='description'),
        re_path(
            r'^(?P<format_name>[^/]+)/$', search_cached,
            name='search'
        )
    ], 'collection')))
]
