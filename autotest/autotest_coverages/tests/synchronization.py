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
from django.contrib.gis.geos import GEOSGeometry
from django.utils.dateparse import parse_datetime

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
                "mosaic_MER_FRS_1P_reduced_RGB", "%(root)s.xml"
            )
        )

        backends.DataItem.objects.create(
            dataset=datasource,
            semantic="template[metadata]", location=join(
                settings.PROJECT_DIR, "data", "meris",
                "mosaic_MER_FRS_1P_reduced_RGB", "range_type.conf"
            )
        )

    def test_synchronize_add(self):
        synchronize(self.collection)
        coverages = models.Coverage.objects.filter(
            identifier__in=[
                "mosaic_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_RGB_reduced",
                "mosaic_MER_FRS_1PNPDE20060822_092058_000001972050_00308_23408_0077_RGB_reduced",
                "mosaic_MER_FRS_1PNPDE20060830_100949_000001972050_00423_23523_0079_RGB_reduced"
            ]
        )
        if not len(coverages) == 3:
            self.fail("Expected coverages don't exist.")

        for coverage in coverages:
            self.assertIn(coverage, self.collection)

    def test_synchronize_remove(self):
        self.test_synchronize_add()
        # add a dataset with a non-existing location and assert that it is
        # removed
        dataset = models.RectifiedDataset(
            identifier="rectified-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-111.6210939999999994 26.8588260000000005, -113.0273439999999994 -4.0786740000000004, -80.6835939999999994 -9.7036739999999995, -68.0273439999999994 15.6088260000000005, -111.6210939999999994 26.8588260000000005)))"),
            begin_time=parse_datetime("2013-06-11T14:55:23Z"),
            end_time=parse_datetime("2013-06-11T14:55:23Z"),
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326,
            size_x=100, size_y=100,
            range_type=models.RangeType.objects.get(name="RGB")
        )
        dataset.full_clean()
        dataset.save()

        backends.DataItem.objects.create(
            dataset=dataset, semantic="bands", location="doesnotexist.tif"
        )

        backends.DataItem.objects.create(
            dataset=dataset, semantic="metadata", location="doesnotexist.xml"
        )
        self.collection.insert(dataset)

        synchronize(self.collection)
        with self.assertRaises(models.Coverage.DoesNotExist):
            models.Coverage.objects.get(
                identifier="rectified-1"
            )
