#-----------------------------------------------------------------------
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

from datetime import datetime
from StringIO import StringIO
from textwrap import dedent

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from eoxserver.core import env
from eoxserver.resources.coverages.models import *
from eoxserver.resources.coverages.metadata.formats import (
    native, eoom, dimap_general
)


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
        self.range_type = create(RangeType,
            name="RGB"
        )

        self.rectified_1 = create(RectifiedDataset,
            identifier="rectified-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-111.6210939999999994 26.8588260000000005, -113.0273439999999994 -4.0786740000000004, -80.6835939999999994 -9.7036739999999995, -68.0273439999999994 15.6088260000000005, -111.6210939999999994 26.8588260000000005)))"),
            begin_time="2013-06-11T14:55:23Z", end_time="2013-06-11T14:55:23Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            range_type=self.range_type
        )

        self.rectified_2 = create(RectifiedDataset,
            identifier="rectified-2",
            footprint=GEOSGeometry("MULTIPOLYGON (((-28.0371090000000009 19.4760129999999982, -32.9589840000000009 -0.9146120000000000, -2.8125000000000000 -3.8150019999999998, 4.2187500000000000 19.1244510000000005, -28.0371090000000009 19.4760129999999982)))"),
            begin_time="2013-06-10T18:52:34Z", end_time="2013-06-10T18:52:32Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            range_type=self.range_type
        )

        self.rectified_3 = create(RectifiedDataset,
            identifier="rectified-3",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time="2013-06-10T18:55:54Z", end_time="2013-06-10T18:55:54Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            range_type=self.range_type
        )

        self.referenceable = create(ReferenceableDataset,
            identifier="referenceable-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time="2013-06-10T18:55:54Z", end_time="2013-06-10T18:55:54Z",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            range_type=self.range_type
        )

        self.mosaic = RectifiedStitchedMosaic(
            identifier="mosaic-1",
            min_x=10, min_y=10, max_x=20, max_y=20, srid=4326, 
            size_x=100, size_y=100,
            range_type=self.range_type
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


class MetadataFormatTests(TestCase):
    def test_native_reader(self):
        xml = """
        <Metadata>
            <EOID>some_unique_id</EOID>
            <BeginTime>2013-08-27T10:00:00Z</BeginTime>
            <EndTime>2013-08-27T10:00:10Z</EndTime>
            <Footprint>
                <Polygon>
                    <Exterior>0 0 20 0 20 10 0 10 0 0</Exterior>
                    <!--<Interior></Interior>-->
                </Polygon>
                <Polygon>
                    <Exterior>10 10 40 10 40 30 10 30 10 10</Exterior>
                    <!--<Interior></Interior>-->
                </Polygon>

            </Footprint>
        </Metadata>
        """
        reader = native.NativeFormat(env)
        self.assertTrue(reader.test(xml))
        values = reader.read(xml)

        self.assertEqual({
            "identifier": "some_unique_id", 
            "begin_time": datetime(2013, 8, 27, 10, 0, 0, tzinfo=utc),
            "end_time": datetime(2013, 8, 27, 10, 0, 10, tzinfo=utc),
            "footprint": MultiPolygon(
                Polygon.from_bbox((0, 0, 10, 20)),
                Polygon.from_bbox((10, 10, 30, 40))
            )
        }, values)

    def test_native_writer(self):
        values = {
            "identifier": "some_unique_id", 
            "begin_time": datetime(2013, 8, 27, 10, 0, 0, tzinfo=utc),
            "end_time": datetime(2013, 8, 27, 10, 0, 10, tzinfo=utc),
            "footprint": MultiPolygon(
                Polygon.from_bbox((0, 0, 10, 20)),
                Polygon.from_bbox((10, 10, 30, 40))
            )
        }
        writer = native.NativeFormat(env)

        f = StringIO()
        writer.write(values, f, pretty=True)
        self.assertEqual(dedent("""\
            <Metadata>
              <EOID>some_unique_id</EOID>
              <BeginTime>2013-08-27T10:00:00Z</BeginTime>
              <EndTime>2013-08-27T10:00:10Z</EndTime>
              <Footprint>
                <Polygon>
                  <Exterior>0.000000 0.000000 20.000000 0.000000 20.000000 10.000000 0.000000 10.000000 0.000000 0.000000</Exterior>
                </Polygon>
                <Polygon>
                  <Exterior>10.000000 10.000000 40.000000 10.000000 40.000000 30.000000 10.000000 30.000000 10.000000 10.000000</Exterior>
                </Polygon>
              </Footprint>
            </Metadata>
            """), dedent(f.getvalue()))

    def test_eoom_reader(self):
        xml = """<?xml version="1.0" encoding="utf-8"?>
        <?xml-stylesheet type="text/xsl" href="schematron_result_for_eop.xsl"?>
        <eop:EarthObservation xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.opengis.net/opt/2.0 ../xsd/opt.xsd" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:eop="http://www.opengis.net/eop/2.0" xmlns:swe="http://www.opengis.net/swe/1.0" xmlns:om="http://www.opengis.net/om/2.0" gml:id="eop_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
          <om:phenomenonTime>
            <gml:TimePeriod gml:id="tp_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
              <gml:beginPosition>2006-08-16T09:09:29Z</gml:beginPosition>
              <gml:endPosition>2006-08-16T09:12:46Z</gml:endPosition>
            </gml:TimePeriod>
          </om:phenomenonTime>
          <om:resultTime>
            <gml:TimeInstant gml:id="archivingdate_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
              <gml:timePosition>2006-08-16T11:03:08Z</gml:timePosition>
            </gml:TimeInstant>
          </om:resultTime>
          <om:procedure>
            <eop:EarthObservationEquipment gml:id="equ_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
              <eop:platform>
                <eop:Platform>
                  <eop:shortName>ENVISAT</eop:shortName>
                </eop:Platform>
              </eop:platform>
              <eop:instrument>
                <eop:Instrument>
                  <eop:shortName>MERIS</eop:shortName>
                </eop:Instrument>
              </eop:instrument>
              <eop:sensor>
                <eop:Sensor>
                  <eop:sensorType>OPTICAL</eop:sensorType>
                </eop:Sensor>
              </eop:sensor>
            </eop:EarthObservationEquipment>
          </om:procedure>
          <om:observedProperty xlink:href="#params1" />
          <om:featureOfInterest>
            <eop:Footprint gml:id="footprint_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
              <eop:multiExtentOf>
                <gml:MultiSurface gml:id="multisurface_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed" srsName="EPSG:4326">
                  <gml:surfaceMember>
                    <gml:Polygon gml:id="polygon_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
                      <gml:exterior>
                        <gml:LinearRing>
                          <gml:posList>20 10 40 10 40 30 20 30 20 10</gml:posList>
                        </gml:LinearRing>
                      </gml:exterior>
                    </gml:Polygon>
                  </gml:surfaceMember>
                  <gml:surfaceMember>
                    <gml:Polygon gml:id="polygon_MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed">
                      <gml:exterior>
                        <gml:LinearRing>
                          <gml:posList>60 50 80 50 80 70 60 70 60 50</gml:posList>
                        </gml:LinearRing>
                      </gml:exterior>
                    </gml:Polygon>
                  </gml:surfaceMember>
                </gml:MultiSurface>
              </eop:multiExtentOf>
            </eop:Footprint>
          </om:featureOfInterest>
          <om:result />
          <eop:metaDataProperty>
            <eop:EarthObservationMetaData>
              <eop:identifier>MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed</eop:identifier>
              <eop:acquisitionType>NOMINAL</eop:acquisitionType>
              <eop:productType>MER_FRS_1P</eop:productType>
              <eop:status>ARCHIVED</eop:status>
              <eop:downlinkedTo>
                <eop:DownlinkInformation>
                  <eop:acquisitionStation>PDHS-E</eop:acquisitionStation>
                </eop:DownlinkInformation>
              </eop:downlinkedTo>
              <eop:processing>
                <eop:ProcessingInformation>
                  <eop:processingCenter>PDHS-E</eop:processingCenter>
                </eop:ProcessingInformation>
              </eop:processing>
            </eop:EarthObservationMetaData>
          </eop:metaDataProperty>
        </eop:EarthObservation>
        """
        
        reader = eoom.EOOMFormatReader(env)
        self.assertTrue(reader.test(xml))
        values = reader.read(xml)

        expected = {
            "identifier": "MER_FRS_1PNPDE20060816_090929_000001972050_00222_23322_0058_uint16_reduced_compressed",
            "begin_time": datetime(2006, 8, 16, 9, 9, 29, tzinfo=utc),
            "end_time": datetime(2006, 8, 16, 9, 12, 46, tzinfo=utc),
            "footprint": MultiPolygon(
                Polygon.from_bbox((10, 20, 30, 40)),
                Polygon.from_bbox((50, 60, 70, 80))
            )
        }
        self.assertEqual(expected, values)


    def test_dimap_reader(self):
        xml = """

        """
        # TODO: find example DIMAP
        


