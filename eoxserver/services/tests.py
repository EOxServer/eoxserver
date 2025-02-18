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

import http
from textwrap import dedent
import importlib
import sys


from django.conf import settings
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.utils.six import assertCountEqual, b
from django.urls import clear_url_caches

from eoxserver.core.util import multiparttools as mp
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.subset import Subsets, Trim, Slice
from eoxserver.services.result import result_set_from_raw_data
from eoxserver.resources.coverages import models
import eoxserver.services.config
import eoxserver.services.views



class BaseMultipartTest(TestCase):
    """ Test class for multipart parsing/splitting
    """

    @staticmethod
    def _headers_string_to_bytes(headers):
        return {
            key.encode("ascii"): value.encode("ascii")
            for key, value in headers.items()
        }

    test_data = mp.CRLF.join([
        b"MIME-Version: 1.0",
        b"Content-Type: multipart/mixed; boundary=frontier",
        b"",
        b"This is a message with multiple parts in MIME format.",
        b"--frontier",
        b"Content-Type: text/plain",
        b"",
        b"This is the body of the message.",
        b"--frontier",
        b"Content-Type: application/octet-stream",
        b"Content-Transfer-Encoding: base64",
        b"",
        b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
        b"--frontier--",
    ])

    expected_global_headers = {
        "MIME-Version": "1.0",
        "Content-Type": "multipart/mixed; boundary=frontier",
    }

    expected_parts = [
        (
            b"This is the body of the message.",
            {"Content-Type": "text/plain"},
        ),
        (
            b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
            {
                "Content-Type": "application/octet-stream",
                "Content-Transfer-Encoding": "base64",
            },
        )
    ]

    def test_gloabal_header_parsing(self):
        global_headers = mp.parse_headers(self.test_data)
        self.assertEqual(global_headers, self.expected_global_headers)

    def test_multipart_iteration(self):
        global_headers = mp.parse_headers(self.test_data)
        parts = list(mp.iterate_multipart_data(self.test_data, global_headers))
        self.assertEqual(parts, self.expected_parts)

    def test_multipart_iteration_old(self):
        parts = list(mp.iterate(self.test_data))
        expected_parts = [
            (self._headers_string_to_bytes(self.expected_global_headers), b""),
            *(
                (self._headers_string_to_bytes(headers), data)
                for data, headers in self.expected_parts
            )
        ]
        self.assertEqual(parts, expected_parts)


class BaseMultipartRelatedTest(BaseMultipartTest):
    """ Test class for multipart/related parsing/splitting
    """

    test_data = mp.CRLF.join([
        b"Content-Type: multipart/related; boundary=frontier",
        b"",
        b"This is a message with multiple parts in MIME format.",
        b"--frontier",
        b"Content-Type: text/plain",
        b"",
        b"This is the body of the message.",
        b"--frontier",
        b"Content-Id: 69a2a211-33c5-430f-a5c5-b4b284f86940",
        b"Content-Type: application/octet-stream",
        b"Content-Transfer-Encoding: base64",
        b"",
        b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
        b"--frontier",
        b"Content-Id: c13f681f-0547-49b6-b785-3de96f2abd95",
        b"Content-Type: application/octet-stream",
        b"",
        b"\xccX\xccI\xfe\x04\xb6\xb5\x8c\xb2\xd0\xf5\x0f\xf1H\xe6",
        b"--frontier--",
    ])

    expected_global_headers = {
        "Content-Type": "multipart/related; boundary=frontier",
    }

    expected_parts = [
        (
            b"This is the body of the message.",
            {"Content-Type": "text/plain"},
        ),
        (
            b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
            {
                "Content-Id": "69a2a211-33c5-430f-a5c5-b4b284f86940",
                "Content-Type": "application/octet-stream",
                "Content-Transfer-Encoding": "base64",
            },
        ),
        (
            b"\xccX\xccI\xfe\x04\xb6\xb5\x8c\xb2\xd0\xf5\x0f\xf1H\xe6",
            {
                "Content-Id": "c13f681f-0547-49b6-b785-3de96f2abd95",
                "Content-Type": "application/octet-stream",
            },
        )
    ]

    expected_root_part = expected_parts[0]
    expected_extra_parts = {
        "69a2a211-33c5-430f-a5c5-b4b284f86940": expected_parts[1],
        "c13f681f-0547-49b6-b785-3de96f2abd95": expected_parts[2],
    }

    def test_multipart_related_root_extraction(self):
        global_headers = mp.parse_headers(self.test_data)
        root_part = mp.get_multipart_related_root(self.test_data, global_headers)
        self.assertEqual(root_part, self.expected_root_part)

    def test_multipart_parsing(self):
        global_headers = mp.parse_headers(self.test_data)
        root_part, extra_parts = mp.parse_multipart_related(self.test_data, global_headers)
        self.assertEqual(root_part, self.expected_root_part)


class AdvancedMultipartRelatedTest(BaseMultipartRelatedTest):
    """ Test class for multipart/related parsing/splitting
    """

    test_data = mp.CRLF.join([
        b"Content-Type: multipart/related; type=\"text/plain\"; boundary=\"frontier\"; start=\"685a49b1-8c50-4a6a-a06e-b0ef742c706c\"",
        b"",
        b"This is a message with multiple parts in MIME format.",
        b"--frontier",
        b"Content-Id: 69a2a211-33c5-430f-a5c5-b4b284f86940",
        b"Content-Type: application/octet-stream",
        b"Content-Transfer-Encoding: base64",
        b"",
        b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
        b"--frontier",
        b"Content-Id: 685a49b1-8c50-4a6a-a06e-b0ef742c706c",
        b"Content-Type: text/plain",
        b"",
        b"This is the body of the message.",
        b"--frontier",
        b"Content-Id: c13f681f-0547-49b6-b785-3de96f2abd95",
        b"Content-Type: application/octet-stream",
        b"",
        b"\xccX\xccI\xfe\x04\xb6\xb5\x8c\xb2\xd0\xf5\x0f\xf1H\xe6",

        b"--frontier--",
    ])

    expected_global_headers = {
        "Content-Type": "multipart/related; type=\"text/plain\"; boundary=\"frontier\"; start=\"685a49b1-8c50-4a6a-a06e-b0ef742c706c\"",
    }

    expected_parts = [
        (
            b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
            {
                "Content-Id": "69a2a211-33c5-430f-a5c5-b4b284f86940",
                "Content-Type": "application/octet-stream",
                "Content-Transfer-Encoding": "base64",
            },
        ),
        (
            b"This is the body of the message.",
            {
                "Content-Id": "685a49b1-8c50-4a6a-a06e-b0ef742c706c",
                "Content-Type": "text/plain",
            },
        ),
        (
            b"\xccX\xccI\xfe\x04\xb6\xb5\x8c\xb2\xd0\xf5\x0f\xf1H\xe6",
            {
                "Content-Id": "c13f681f-0547-49b6-b785-3de96f2abd95",
                "Content-Type": "application/octet-stream",
            },
        )
    ]

    expected_root_part = expected_parts[1]
    expected_extra_parts = {
        "69a2a211-33c5-430f-a5c5-b4b284f86940": expected_parts[0],
        "c13f681f-0547-49b6-b785-3de96f2abd95": expected_parts[2],
    }


class ResultSetTestCase(TestCase):

    test_data = mp.CRLF.join([
        b"MIME-Version: 1.0",
        b"Content-Type: multipart/mixed; boundary=frontier",
        b"",
        b"This is a message with multiple parts in MIME format.",
        b"--frontier",
        b"Content-Type: text/plain",
        b"Content-Disposition: attachmet; filename=\"message.msg\"",
        b"Content-Id: message-part",
        b"",
        b"This is the body of the message.",
        b"--frontier",
        b"Content-Type: application/octet-stream",
        b"Content-Transfer-Encoding: base64",
        b"",
        b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
        b"--frontier--",
    ])

    expected_result_set = [
        {
            "data": b"This is the body of the message.",
            "type": b"text/plain",
            "identifier": b"message-part",
            "filename": b"message.msg",
        },
        {
            "data": b"PGh0bWw+CiAgPGhlYWQ+CiAgPC9oZWFkPgogIDxib2R5PgogICAgPHA+VGhpcyBpcyB0aGUgYm9keSBvZiB0aGUgbWVzc2FnZS48L3A+CiAgPC9ib2R5Pgo8L2h0bWw+Cg==",
            "type": b"application/octet-stream",
            "filename": None,
            "identifier": None,
        },
    ]

    def test_result_set_from_raw(self):
        result_set = result_set_from_raw_data(self.test_data)

        self.assertTrue(len(result_set) == 2)

        first, second  = result_set
        expected_first, expected_second = self.expected_result_set

        self.assertEqual(first.data, expected_first["data"])
        self.assertEqual(first.content_type, expected_first["type"])
        self.assertEqual(first.identifier, expected_first["identifier"])
        self.assertEqual(first.filename, expected_first["filename"])

        self.assertEqual(second.data, expected_second["data"])
        self.assertEqual(second.content_type, expected_second["type"])
        self.assertEqual(second.identifier, expected_second["identifier"])
        self.assertEqual(second.filename, expected_second["filename"])


class TemporalSubsetsTestCase(TransactionTestCase):
    def setUp(self):
        """ Set up a couple of test datasets to be distributed along the time
        axis as such:
        |-A-|     |-B-|-D-|-F-|     |-G-|     H
                    |-C-||-E-|
        """
        p = parse_iso8601

        grid = models.Grid.objects.create(
            coordinate_reference_system='EPSG:4326',
            axis_1_name='long',
            axis_2_name='lat',
            axis_1_type=0,
            axis_2_type=0,
            axis_1_offset=5/100,
            axis_2_offset=5/100,
        )

        coverage_type = models.CoverageType.objects.create(name="RGB")
        self.datasets = [
            models.Coverage.objects.create(
                identifier="A",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:00Z"),
                end_time=p("2000-01-01T00:00:05Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="B",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:10Z"),
                end_time=p("2000-01-01T00:00:15Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="C",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:12Z"),
                end_time=p("2000-01-01T00:00:17Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="D",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:15Z"),
                end_time=p("2000-01-01T00:00:20Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="E",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:18Z"),
                end_time=p("2000-01-01T00:00:23Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="F",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:20Z"),
                end_time=p("2000-01-01T00:00:25Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="G",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:30Z"),
                end_time=p("2000-01-01T00:00:35Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
            ),
            models.Coverage.objects.create(
                identifier="H",
                footprint=MultiPolygon(Polygon.from_bbox((0, 0, 5, 5))),
                begin_time=p("2000-01-01T00:00:40Z"),
                end_time=p("2000-01-01T00:00:40Z"),
                grid=grid,
                axis_1_size=100, axis_2_size=100,
                axis_1_origin=0, axis_2_origin=0,
                coverage_type=coverage_type
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
        qs = models.EOObject.objects.filter(**subsets.get_filters(containment))

        # test the "filter()" function
        self.assertCountEqual(
            expected_ids, qs.values_list("identifier", flat=True)
        )

        # test the "matches()" function
        self.assertCountEqual(
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

class CachingTest(TestCase):
    def _reload_ows_views(self):
        # NOTE: we have to do this dance because the setting
        #       is read at import time
        importlib.reload(eoxserver.services.views)
        importlib.reload(eoxserver.services.urls)
        importlib.reload(sys.modules[settings.ROOT_URLCONF])
        clear_url_caches()


    def test_ows_view_not_cached_by_default(self):
        response = Client().get("/ows", {"service": "WMS", "request": "GetCapabilities"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertNotIn('Cache-Control', response)

    def test_ows_view_cached_if_configured(self):
        with override_settings(EOXS_RENDERER_CACHE_TIME="3"):
            self._reload_ows_views()
            response = Client().get("/ows", {"service": "WMS", "request": "GetCapabilities"})

        self._reload_ows_views()

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response['Cache-Control'], "max-age=3")
