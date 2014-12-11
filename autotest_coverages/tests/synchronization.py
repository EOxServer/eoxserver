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

from os.path import join

from django.conf import settings
from django.test import TestCase

from eoxserver.backends import models as backends
from eoxserver.resources.coverages import models
from eoxserver.resources.coverages.synchronization import synchronize


BASE_FIXTURES = [
    "range_types.json", "meris_range_type.json",
    "asar_range_type.json",
]


class SynchronizeLocalTestCase(TestCase):
    fixtures = BASE_FIXTURES

    def setUp(self):
        self.collection = models.DatasetSeries.objects.create(
            identifier="TestCollection"
        )

        datasource = models.DataSource.objects.create(
            collection=self.collection
        )

        backends.DataItem.objects.create(
            dataset=datasource,
            semantic="source[bands]", location=join(
                settings.PROJECT_DIR, "data", "meris",
                "mosaic_MER_FRS_1P_reduced_RGB", "*.tif"
            )
        )

        backends.DataItem.objects.create(
            dataset=datasource,
            semantic="template[metadata]", location=join(
                settings.PROJECT_DIR, "data", "meris",
                "mosaic_MER_FRS_1P_reduced_RGB", "%(basename)s.tif"
            )
        )

    def test_synchronize(self):
        synchronize(self.collection)

    def tearDown(self):
        pass
