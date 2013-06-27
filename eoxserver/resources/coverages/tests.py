#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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


from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import GEOSGeometry
from django.utils.dateparse import parse_datetime

from eoxserver.resources.coverages.models import *


def create(Class, **kwargs):
    obj = Class(**kwargs)
    obj.full_clean()
    obj.save()
    return obj


def refresh(*objects):
    refr = lambda obj: type(obj).objects.get(pk=obj.pk)
    if len(objects) == 1:
        return refr(objects[0])
    return map(refr, objects)

def union(*footprints):
    u = None
    for footprint in footprints:
        if u is None:
            u = footprint
        else:
            u = footprint.union(u)
    return u


class ModelTests(TestCase):
    def setUp(self):
        self.rectified_1 = create(RectifiedDataset,
            identifier="rectified-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-111.6210939999999994 26.8588260000000005, -113.0273439999999994 -4.0786740000000004, -80.6835939999999994 -9.7036739999999995, -68.0273439999999994 15.6088260000000005, -111.6210939999999994 26.8588260000000005)))"),
            begin_time="2013-06-11T14:55:23Z", end_time="2013-06-11T14:55:23Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            location="path/to/dataset1.tif", format="GDAL/VRT", 
            #storage=ftp_storage
        )

        self.rectified_2 = create(RectifiedDataset,
            identifier="rectified-2",
            footprint=GEOSGeometry("MULTIPOLYGON (((-28.0371090000000009 19.4760129999999982, -32.9589840000000009 -0.9146120000000000, -2.8125000000000000 -3.8150019999999998, 4.2187500000000000 19.1244510000000005, -28.0371090000000009 19.4760129999999982)))"),
            begin_time="2013-06-10T18:52:34Z", end_time="2013-06-10T18:52:32Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            location="path/to/dataset2.tif", format="GDAL/VRT", 
            #storage=ftp_storage
        )

        self.rectified_3 = create(RectifiedDataset,
            identifier="rectified-3",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time="2013-06-10T18:55:54Z", end_time="2013-06-10T18:55:54Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            location="path/to/dataset3.tif", format="GDAL/VRT", 
            #storage=ftp_storage
        )

        self.referenceable = create(ReferenceableDataset,
            identifier="referenceable-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time="2013-06-10T18:55:54Z", end_time="2013-06-10T18:55:54Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            location="path/to/dataset3.tif", format="GDAL/VRT", 
            #storage=ftp_storage
        )

        self.mosaic = RectifiedStitchedMosaic(
            identifier="mosaic-1",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            location="path/to/tileindex", format="GDAL/VRT"
        )

        # TODO: bug, requires identifier to be set manually again
        self.mosaic.identifier = "mosaic-1"
        self.mosaic.full_clean()
        self.mosaic.save()
        
        #=======================================================================
        # Collections
        #=======================================================================

        self.series_1 = create(DatasetSeries,
            identifier="series-1"
        )


        self.series_2 = create(DatasetSeries,
            identifier="series-2"
        )


    def tearDown(self):
        pass


    def test_insertion(self):
        rectified_1, rectified_2, rectified_3 = self.rectified_1, self.rectified_2, self.rectified_3
        mosaic, series_1, series_2 = self.mosaic, self.series_1, self.series_2

        mosaic.insert(rectified_1)
        mosaic.insert(rectified_2)
        mosaic.insert(rectified_3)

        self.assertIn(rectified_1, mosaic)
        self.assertIn(rectified_2, mosaic)
        self.assertIn(rectified_3, mosaic)

        series_1.insert(rectified_1)
        series_1.insert(rectified_2)
        series_1.insert(rectified_3)
        series_1.insert(mosaic)

        self.assertIn(rectified_1, series_1)
        self.assertIn(rectified_2, series_1)
        self.assertIn(rectified_3, series_1)
        self.assertIn(mosaic, series_1)

        series_2.insert(rectified_1)
        series_2.insert(rectified_2)
        series_2.insert(rectified_3)
        series_2.insert(mosaic)

        self.assertIn(rectified_1, series_2)
        self.assertIn(rectified_2, series_2)
        self.assertIn(rectified_3, series_2)
        self.assertIn(mosaic, series_2)

        self.assertEqual(len(mosaic), 3)
        self.assertEqual(len(series_1), 4)
        self.assertEqual(len(series_1), 4)


        mosaic, series_1, series_2 = refresh(mosaic, series_1, series_2)

        # TODO: further check metadata
        self.assertTrue(series_1.begin_time is not None)

        begin_time, end_time, all_rectified_footprints = collect_eo_metadata(RectifiedDataset.objects.all())
        time_extent = begin_time, end_time

        self.assertTrue(series_1.footprint.equals(all_rectified_footprints))
        self.assertTrue(series_2.footprint.equals(all_rectified_footprints))
        self.assertTrue(mosaic.footprint.equals(all_rectified_footprints))

        self.assertEqual(series_1.time_extent, time_extent)
        self.assertEqual(series_2.time_extent, time_extent)
        self.assertEqual(mosaic.time_extent, time_extent)

        for eo_obj in series_1:
            pass


    def test_insertion_cascaded(self):
        rectified_1, mosaic, series_1, series_2 = self.rectified_1, self.mosaic, self.series_1, self.series_2

        mosaic.insert(rectified_1)
        series_1.insert(mosaic)
        series_2.insert(series_1)

        self.assertTrue(series_2.contains(rectified_1, recursive=True))
        self.assertFalse(series_2.contains(rectified_1))

        self.assertTrue(series_1.contains(rectified_1, recursive=True))
        self.assertFalse(series_1.contains(rectified_1))

        self.assertTrue(mosaic.contains(rectified_1, recursive=True))
        self.assertTrue(mosaic.contains(rectified_1))

        for obj in series_2.iter_cast(True):
            pass


    def test_insertion_failed(self):
        referenceable, mosaic = self.referenceable, self.mosaic

        with self.assertRaises(ValidationError):
            mosaic.insert(referenceable)

        mosaic = refresh(mosaic)
        self.assertNotIn(referenceable, mosaic)


    def test_insertion_and_removal(self):
        rectified_1, rectified_2, series_1 = self.rectified_1, self.rectified_2, self.series_1
        series_1.insert(rectified_1)
        series_1.insert(rectified_2)

        series_1 = refresh(series_1)

        series_1.remove(rectified_2)

        series_1 = refresh(series_1)

        self.assertEqual(rectified_1.time_extent, series_1.time_extent)
        self.assertEqual(rectified_1.footprint, series_1.footprint)

    
    def test_propagate_eo_metadata_change(self):
        rectified_1, series_1 = self.rectified_1, self.series_1

        series_1.insert(rectified_1)
        
        new_begin_time = parse_datetime("2010-06-11T14:55:23Z")
        new_end_time = parse_datetime("2010-06-11T14:55:23Z")

        rectified_1.begin_time = new_begin_time
        rectified_1.end_time = new_end_time
        rectified_1.full_clean()
        rectified_1.save()

        series_1 = refresh(series_1)

        self.assertEqual(series_1.begin_time, new_begin_time)
        self.assertEqual(series_1.end_time, new_end_time)


    def test_insert_in_self_fails(self):
        series_1 = self.series_1
        with self.assertRaises(ValidationError):
            series_1.insert(series_1)


    def test_circular_reference_fails(self):
        series_1, series_2 = self.series_1, self.series_2
        with self.assertRaises(ValidationError):
            series_1.insert(series_2)
            series_2.insert(series_1)
