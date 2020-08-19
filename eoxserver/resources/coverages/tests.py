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

import sys
from datetime import datetime
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
from textwrap import dedent
from unittest import skipIf

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import GEOSGeometry, Polygon, MultiPolygon
from django.utils.dateparse import parse_datetime
from django.utils.timezone import utc

from eoxserver.core import env
from eoxserver.resources.coverages.models import *
from eoxserver.resources.coverages.util import collect_eo_metadata
from eoxserver.resources.coverages.metadata.coverage_formats import (
    native, eoom, dimap_general
)


def create(Class, **kwargs):
    obj = Class(**kwargs)
    obj.full_clean()
    obj.save()
    return obj


def refresh(*objects):
    refr = lambda obj: type(obj).objects.get(identifier=obj.identifier)
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


class GeometryMixIn(object):
    def assertGeometryEqual(self, ga, gb, tolerance=0.05, max_area=0.00001):
        try:
            if ga.equals(gb):
                return
            if ga.difference(gb).empty:
                return
            if ga.equals_exact(gb, tolerance):
                return
            if ga.difference(gb).area < max_area:
                return
        except Exception:
            pass

        self.fail(
            ga.equals_exact(gb, tolerance),
            "%r != %r" % (ga.wkt, gb.wkt)
        )

class ModelTests(GeometryMixIn, TestCase):
    def setUp(self):
        self.coverage_type = create(CoverageType,
            name="RGB"
        )
        self.rectified_grid = Grid.objects.create(
          name="rectified_grid",
          coordinate_reference_system="EPSG:4326",
          axis_1_name="x",
          axis_1_type=0,
          axis_1_offset="5",
          axis_2_name="y",
          axis_2_type=0,
          axis_2_offset="5"
        )
        self.referenced_grid= Grid.objects.create(
          name="referenced_grid",
          coordinate_reference_system="EPSG:4326",
          axis_1_name="x",
          axis_1_type=0,
          axis_2_name="y",
          axis_2_type=0

        )
        self.rectified_1 = create(Coverage,
            identifier="rectified-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-111.6210939999999994 26.8588260000000005, -113.0273439999999994 -4.0786740000000004, -80.6835939999999994 -9.7036739999999995, -68.0273439999999994 15.6088260000000005, -111.6210939999999994 26.8588260000000005)))"),
            begin_time=parse_datetime("2013-06-11T14:55:23Z"),
            end_time=parse_datetime("2013-06-11T14:55:23Z"),
            grid=self.rectified_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=self.coverage_type
        )

        self.rectified_2 = create(Coverage,
            identifier="rectified-2",
            footprint=GEOSGeometry("MULTIPOLYGON (((-28.0371090000000009 19.4760129999999982, -32.9589840000000009 -0.9146120000000000, -2.8125000000000000 -3.8150019999999998, 4.2187500000000000 19.1244510000000005, -28.0371090000000009 19.4760129999999982)))"),
            begin_time=parse_datetime("2013-06-10T18:52:34Z"),
            end_time=parse_datetime("2013-06-10T18:52:32Z"),
            grid=self.rectified_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=self.coverage_type
        )

        self.rectified_3 = create(Coverage,
            identifier="rectified-3",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time=parse_datetime("2013-06-10T18:55:54Z"),
            end_time=parse_datetime("2013-06-10T18:55:54Z"),
            grid=self.rectified_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=self.coverage_type
        )

        self.referenceable = create(Coverage,
            identifier="referenceable-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-85.5175780000000003 14.2904660000000003, -116.2792969999999997 -8.3853150000000003, -63.7207030000000003 -19.4595340000000014, -58.7988280000000003 7.2592160000000003, -85.5175780000000003 14.2904660000000003)))"),
            begin_time=parse_datetime("2013-06-10T18:55:54Z"),
            end_time=parse_datetime("2013-06-10T18:55:54Z"),
            grid=self.referenced_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=self.coverage_type
        )

        self.mosaic = create(Mosaic,
            identifier="mosaic-1",
            grid=self.rectified_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=self.coverage_type
        )

        # TODO: bug, requires identifier to be set manually again
        self.mosaic.identifier = "mosaic-1"
        self.mosaic.full_clean()
        self.mosaic.save()

        #=======================================================================
        # Collections
        #=======================================================================

        self.series_1 = create(Collection,
            identifier="series-1"
        )

        self.series_2 = create(Collection,
            identifier="series-2"
        )

    def tearDown(self):
        pass

    def test_insertion(self):
        rectified_1, rectified_2, rectified_3 = (
            self.rectified_1, self.rectified_2, self.rectified_3
        )
        mosaic, series_1, series_2 = self.mosaic, self.series_1, self.series_2

        mosaic_insert_coverage(mosaic, rectified_1)
        mosaic_insert_coverage(mosaic, rectified_2)
        mosaic_insert_coverage(mosaic, rectified_3)
        mosaic_list = mosaic.coverages.all()

        self.assertIn(rectified_1, mosaic_list)
        self.assertIn(rectified_2, mosaic_list)
        self.assertIn(rectified_3, mosaic_list)


        collection_insert_eo_object(series_1, rectified_1)
        collection_insert_eo_object(series_1, rectified_2)
        collection_insert_eo_object(series_1, rectified_3)

        series_1_list= series_1.coverages.all()

        self.assertIn(rectified_1, series_1_list)
        self.assertIn(rectified_2, series_1_list)
        self.assertIn(rectified_3, series_1_list)

        collection_insert_eo_object(series_2, rectified_1)
        collection_insert_eo_object(series_2, rectified_2)
        collection_insert_eo_object(series_2, rectified_3)

        series_2_list = series_2.coverages.all()

        self.assertIn(rectified_1, series_2_list)
        self.assertIn(rectified_2, series_2_list)
        self.assertIn(rectified_3, series_2_list)

        self.assertEqual(len(mosaic_list), 3)
        self.assertEqual(len(series_1_list), 3)
        self.assertEqual(len(series_2_list), 3)

        mosaic = Mosaic.objects.get(identifier="mosaic-1")
        mosaic, series_1, series_2 = refresh(mosaic, series_1, series_2)

        # TODO: further check metadata
        self.assertTrue(series_1.begin_time is not None)

        begin_time, end_time, all_rectified_footprints = collect_eo_metadata(
            Coverage.objects.all()
        )
        time_extent = begin_time, end_time

        extent_footprint = MultiPolygon(
            Polygon.from_bbox(all_rectified_footprints.extent)
        )

        self.assertGeometryEqual(series_1.footprint, all_rectified_footprints)
        self.assertGeometryEqual(series_2.footprint, all_rectified_footprints)
        self.assertGeometryEqual(mosaic.footprint, all_rectified_footprints)

        series_1_time_extent = series_1.begin_time, series_1.end_time
        series_2_time_extent = series_2.begin_time, series_2.end_time
        mosaic_time_extent = mosaic.begin_time, mosaic.end_time

        self.assertEqual(series_1_time_extent, time_extent)
        self.assertEqual(series_2_time_extent, time_extent)
        self.assertEqual(mosaic_time_extent, time_extent)

        for eo_obj in series_1_list:
            pass

    def test_insertion_cascaded(self):
        rectified_1, mosaic, series_1, series_2 = (
            self.rectified_1, self.mosaic, self.series_1, self.series_2
        )
        mosaic_insert_coverage(mosaic, rectified_1)
        collection_insert_eo_object(series_1, rectified_1)
        collection_insert_eo_object(series_2, rectified_1)

        series_1 = refresh(series_1)

        series_1_list= series_1.coverages.all()
        series_2_list= series_2.coverages.all()
        mosaic_list= mosaic.coverages.all()

        self.assertIn(rectified_1, series_2_list)
        self.assertIn(rectified_1, series_1_list)

        self.assertIn(rectified_1, mosaic_list)

        # for obj in series_2.iter_cast(True):
        #     pass

    def test_insertion_failed(self):
        referenceable, mosaic = self.referenceable, self.mosaic

        with self.assertRaises(ManagementError):
            mosaic_insert_coverage(mosaic, referenceable)

        mosaic = refresh(mosaic)
        mosaic_list= mosaic.coverages.all()
        self.assertNotIn(referenceable, mosaic_list)

    def test_insertion_and_removal(self):
        rectified_1, rectified_2, series_1 = (
            self.rectified_1, self.rectified_2, self.series_1
        )
        collection_insert_eo_object(series_1, rectified_1)
        collection_insert_eo_object(series_1, rectified_2)

        series_1 = refresh(series_1)


        collection_exclude_eo_object(series_1, rectified_2)

        series_1 = refresh(series_1)

        rectified_1_time_extent = rectified_1.begin_time, rectified_1.end_time
        series_1_time_extent = series_1.begin_time, series_1.end_time
        self.assertEqual(rectified_1_time_extent, series_1_time_extent)
        self.assertGeometryEqual(rectified_1.footprint,series_1.footprint)

    def test_propagate_eo_metadata_change(self):
        rectified_1, series_1 = self.rectified_1, self.series_1


        new_begin_time = parse_datetime("2010-06-11T14:55:23Z")
        new_end_time = parse_datetime("2010-06-11T14:55:23Z")

        rectified_1.begin_time = new_begin_time
        rectified_1.end_time = new_end_time
        rectified_1.full_clean()
        rectified_1.save()
        collection_insert_eo_object(series_1, rectified_1)

        series_1 = refresh(series_1)

        self.assertEqual(series_1.begin_time, new_begin_time)
        self.assertEqual(series_1.end_time, new_end_time)



class MetadataFormatTests(GeometryMixIn, TestCase):
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
            ),
            "format": "native"
        }, values)

    @skipIf(sys.version_info.major == 3, 'segfault in Django')
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
            ),
            'format': 'eogml',
            'metadata': {
              'acquisition_station': 'PDHS-E',
              'acquisition_sub_type': None,
              'antenna_look_direction': None,
              'availability_time': datetime(2006, 8, 16, 11, 3, 8, tzinfo=utc),
              'cloud_cover': None,
              'completion_time_from_ascending_node': None,
              'doppler_frequency': None,
              'highest_location': None,
              'illumination_azimuth_angle': None,
              'illumination_elevation_angle': None,
              'illumination_zenith_angle': None,
              'incidence_angle_variation': None,
              'lowest_location': None,
              'maximum_incidence_angle': None,
              'minimum_incidence_angle': None,
              'across_track_incidence_angle': None,
              'along_track_incidence_angle': None,
              'modification_date': None,
              'polarisation_mode': None,
              'polarization_channels': None,
              'snow_cover': None,
              'start_time_from_ascending_node': None}
        }
        self.maxDiff = None
        # self.assertEqual(expected, values)
        values_time_extent = values["begin_time"], values["end_time"]
        expected_time_extent = expected["begin_time"], expected["end_time"]
        self.assertEqual(expected_time_extent, values_time_extent)
        self.assertEqual(expected["identifier"], values["identifier"])
        self.assertEqual(expected["metadata"], values["metadata"])
        self.assertGeometryEqual(expected["footprint"], values["footprint"])

    def test_dimap_reader(self):
        xml = """

        """
        # TODO: find example DIMAP


class CastingTest(TestCase):
    def test_cast(self):
        coverage_type = create(CoverageType,
            name="RGB"
        )
        rectified_grid = Grid.objects.create(
          name="rectified_grid",
          coordinate_reference_system="EPSG:4326",
          axis_1_name="x",
          axis_1_type=0,
          axis_1_offset="5",
          axis_2_name="y",
          axis_2_type=0,
          axis_2_offset="5"
        )
        create(Coverage,
            identifier="rectified-1",
            footprint=GEOSGeometry("MULTIPOLYGON (((-111.6210939999999994 26.8588260000000005, -113.0273439999999994 -4.0786740000000004, -80.6835939999999994 -9.7036739999999995, -68.0273439999999994 15.6088260000000005, -111.6210939999999994 26.8588260000000005)))"),
            begin_time=parse_datetime("2013-06-11T14:55:23Z"),
            end_time=parse_datetime("2013-06-11T14:55:23Z"),
            grid=rectified_grid,
            axis_1_size=100,
            axis_2_size=100,
            coverage_type=coverage_type
        )

        eo_object = EOObject.objects.get(identifier="rectified-1")
        cast_object = cast_eo_object(eo_object)

        self.assertEqual(type(cast_object), Coverage)
