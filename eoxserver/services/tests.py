#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from textwrap import dedent

from django.test import TestCase, TransactionTestCase
from django.contrib.gis.geos import Polygon, MultiPolygon

from eoxserver.core.util import multiparttools as mp
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.subset import Subsets, Trim, Slice
from eoxserver.services.result import result_set_from_raw_data
from eoxserver.resources.coverages import models


class MultipartTest(TestCase):
    """ Test class for multipart parsing/splitting
    """

    example_multipart = dedent("""\
        MIME-Version: 1.0\r
        Content-Type: multipart/mixed; boundary=frontier\r
        \r
        This is a message with multiple parts in MIME format.\r
        --frontier
        Content-Type: text/plain\r
        \r
        This is the body of the message.\r
        --frontier
        Content-Type: application/octet-stream\r
        Content-Transfer-Encoding: base64\r
        \r
        PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==\r
        --frontier--
    """)

    def test_multipart_iteration(self):
        parsed = map(
            lambda i: (i[0], str(i[1])), mp.iterate(self.example_multipart)
        )

        self.assertEqual([
                ({"MIME-Version": "1.0", "Content-Type": "multipart/mixed; boundary=frontier"}, ""),
                ({"Content-Type": "text/plain"}, "This is the body of the message."),
                ({"Content-Type": "application/octet-stream", "Content-Transfer-Encoding": "base64"}, "PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==")
            ], parsed
        )


class ResultSetTestCase(TestCase):

    example_multipart = dedent("""\
        MIME-Version: 1.0\r
        Content-Type: multipart/mixed; boundary=frontier\r
        \r
        This is a message with multiple parts in MIME format.\r
        --frontier
        Content-Type: text/plain\r
        Content-Disposition: attachmet; filename="message.msg"\r
        Content-Id: message-part\r
        \r
        This is the body of the message.\r
        --frontier
        Content-Type: application/octet-stream\r
        Content-Transfer-Encoding: base64\r
        \r
        PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==\r
        --frontier--
    """)


    def test_result_set_from_raw(self):
        result_set = result_set_from_raw_data(self.example_multipart)
        self.assertTrue(len(result_set) == 2)

        first = result_set[0]
        second = result_set[1]

        self.assertEqual(str(first.data), "This is the body of the message.")
        self.assertEqual(first.content_type, "text/plain")
        self.assertEqual(first.filename, "message.msg")
        self.assertEqual(first.identifier, "message-part")
        self.assertEqual(str(second.data), "PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==")


class TemporalSubsetsTestCase(TransactionTestCase):
    def setUp(self):
        """ Set up a couple of test datasets to be distributed along the time
        axis as such:
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        """
        p = parse_iso8601

        range_type = models.RangeType.objects.create(name="RGB")
        self.datasets = [
            models.RectifiedDataset.objects.create(
                identifier="A",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:00Z"),
                end_time=p("2000-01-01T00:00:05Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="B",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:10Z"),
                end_time=p("2000-01-01T00:00:15Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="C",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:12Z"),
                end_time=p("2000-01-01T00:00:17Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="D",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:15Z"),
                end_time=p("2000-01-01T00:00:20Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="E",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:18Z"),
                end_time=p("2000-01-01T00:00:23Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="F",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:20Z"),
                end_time=p("2000-01-01T00:00:25Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="G",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:30Z"),
                end_time=p("2000-01-01T00:00:35Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            ),
            models.RectifiedDataset.objects.create(
                identifier="H",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:40Z"),
                end_time=p("2000-01-01T00:00:40Z"),
                srid=4326, min_x=0, min_y=0, max_x=5, max_y=5,
                size_x=100, size_y=100,
                range_type=range_type
            )
        ]

        self.config = get_eoxserver_config()
        self.original_interval_interpretation = self.config.get(
            "services.owscommon", "time_interval_interpretation"
        )

        self.set_interpretation("closed")

    def tearDown(self):
        self.set_interpretation()

    def set_interpretation(self, value=None):
        self.config.set(
            "services.owscommon", "time_interval_interpretation",
            value if value else self.original_interval_interpretation
        )

    def evaluate_subsets(self, subsets, containment, expected_ids):
        """ Evaluates the subset via QuerySet filter and via the matches()
            functionality.
        """
        qs = subsets.filter(
            models.EOObject.objects.all(), containment
        )

        # test the "filter()" function
        self.assertItemsEqual(
            expected_ids, qs.values_list("identifier", flat=True)
        )

        # test the "matches()" function
        self.assertItemsEqual(
            expected_ids, [
                ds.identifier for ds in self.datasets
                if subsets.matches(ds, containment)
            ]
        )

    def make_subsets(self, begin, end=None):
        if end is None:
            return Subsets([Slice("t", parse_iso8601(begin))])
        else:
            return Subsets([Trim(
                "t", parse_iso8601(begin), parse_iso8601(end)
            )])

    def test_all_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        ]-------------------------------[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:00Z", "2000-01-01T00:00:35Z"
            ),
            "overlaps", ("A", "B", "C", "D", "E", "F", "G")
        )

    def test_all_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        [-------------------------------]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:00Z", "2000-01-01T00:00:35Z"
            ),
            "overlaps", ("A", "B", "C", "D", "E", "F", "G")
        )

    def test_all_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        ]...............................[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:00Z", "2000-01-01T00:00:35Z"
            ),
            "contains", ("B", "C", "D", "E", "F")
        )

    def test_all_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        [...............................]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:00Z", "2000-01-01T00:00:35Z"
            ),
            "contains", ("A", "B", "C", "D", "E", "F", "G")
        )

    def test_middle_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
            ]-----------------------[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:05Z", "2000-01-01T00:00:30Z"
            ),
            "overlaps", ("B", "C", "D", "E", "F")
        )

    def test_middle_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
            [-----------------------]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:05Z", "2000-01-01T00:00:30Z"
            ),
            "overlaps", ("A", "B", "C", "D", "E", "F", "G")
        )

    def test_middle_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
            ].......................[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:05Z", "2000-01-01T00:00:30Z"
            ),
            "contains", ("B", "C", "D", "E", "F")
        )

    def test_middle_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
            [.......................]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:05Z", "2000-01-01T00:00:30Z"
            ),
            "contains", ("B", "C", "D", "E", "F")
        )

    def test_small_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                      ]---[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:15Z", "2000-01-01T00:00:20Z"
            ),
            "overlaps", ("C", "D", "E")
        )

    def test_small_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                      [---]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:15Z", "2000-01-01T00:00:20Z"
            ),
            "overlaps", ("B", "C", "D", "E", "F")
        )

    def test_small_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                      ]...[
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:15Z", "2000-01-01T00:00:20Z"
            ),
            "contains", ()
        )

    def test_small_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                      [...]
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:15Z", "2000-01-01T00:00:20Z"
            ),
            "contains", ("D",)
        )

    def test_point_1_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:30Z", "2000-01-01T00:00:30Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_1_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:30Z", "2000-01-01T00:00:30Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_1_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:30Z", "2000-01-01T00:00:30Z"
            ),
            "contains", ()
        )

    def test_point_1_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:30Z", "2000-01-01T00:00:30Z"
            ),
            "contains", ()
        )

    def test_point_2_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:32Z", "2000-01-01T00:00:32Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_2_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:32Z", "2000-01-01T00:00:32Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_2_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:32Z", "2000-01-01T00:00:32Z"
            ),
            "contains", ()
        )

    def test_point_2_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:35Z", "2000-01-01T00:00:35Z"
            ),
            "contains", ()
        )

    def test_point_3_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:35Z", "2000-01-01T00:00:35Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_3_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:35Z", "2000-01-01T00:00:35Z"
            ),
            "overlaps", ("G",)
        )

    def test_point_3_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:35Z", "2000-01-01T00:00:35Z"
            ),
            "contains", ()
        )

    def test_point_3_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:35Z", "2000-01-01T00:00:35Z"
            ),
            "contains", ()
        )

    def test_point_4_overlaps_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:40Z", "2000-01-01T00:00:40Z"
            ),
            "overlaps", ("H",)
        )

    def test_point_4_overlaps_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:40Z", "2000-01-01T00:00:40Z"
            ),
            "overlaps", ("H",)
        )

    def test_point_4_contains_open(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:40Z", "2000-01-01T00:00:40Z"
            ),
            "contains", ("H",)
        )

    def test_point_4_contains_closed(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.evaluate_subsets(
            self.make_subsets(
                "2000-01-01T00:00:40Z", "2000-01-01T00:00:40Z"
            ),
            "contains", ("H",)
        )

    def test_slice_1_overlaps(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.set_interpretation("open")
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:30Z"), "overlaps", ("G",)
        )

    def test_slice_1_contains(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                    |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:30Z"), "contains", ("G",)
        )

    def test_slice_2_overlaps(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:32Z"), "overlaps", ("G",)
        )

    def test_slice_2_contains(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                      |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:32Z"), "contains", ("G",)
        )

    def test_slice_3_overlaps(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:35Z"), "overlaps", ("G",)
        )

    def test_slice_3_contains(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                        |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:35Z"), "contains", ("G",)
        )

    def test_slice_4_overlaps(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:40Z"), "overlaps", ("H",)
        )

    def test_slice_4_contains(self):
        """
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
                                              |
        """
        self.evaluate_subsets(
            self.make_subsets("2000-01-01T00:00:40Z"), "contains", ("H",)
        )
