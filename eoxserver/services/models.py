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


from django.contrib.gis.db import models
from eoxserver.resources.coverages import models as coverage_models


class WMSRenderOptions(models.Model):
    """ Additional options for rendering coverages via WMS.
    """

    coverage = models.OneToOneField(coverage_models.Coverage)

    default_red = models.PositiveIntegerField(null=True, blank=True, default=None)
    default_green = models.PositiveIntegerField(null=True, blank=True, default=None)
    default_blue = models.PositiveIntegerField(null=True, blank=True, default=None)
    default_alpha = models.PositiveIntegerField(null=True, blank=True, default=None)

    resampling = models.CharField(null=True, blank=True, max_length=16)

    scale_auto = models.BooleanField(default=False)
    scale_min = models.PositiveIntegerField(null=True, blank=True)
    scale_max = models.PositiveIntegerField(null=True, blank=True)
