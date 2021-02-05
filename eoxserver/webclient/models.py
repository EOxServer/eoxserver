#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from django.db import models

from eoxserver.resources.coverages import models as coverages


class Extra(models.Model):
    eo_object = models.OneToOneField(coverages.EOObject, related_name="webclient_extra", on_delete=models.CASCADE)

    display_name = models.CharField(max_length=64, blank=True, null=True)
    info = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=64, blank=True, null=True)
    default_visible = models.BooleanField(default=False)
    max_zoom = models.IntegerField(default=15)
    histogram_bin_count = models.IntegerField(default=28)
    histogram_threshold = models.IntegerField(default=600)
    search_limit = models.IntegerField(default=600)
    load_more = models.IntegerField(default=600)
