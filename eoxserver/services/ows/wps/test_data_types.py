# ------------------------------------------------------------------------------
#
#  WPS Literal Data - data-types - unit-tests
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------
# pylint: disable=missing-docstring, line-too-long

from unittest import TestCase, main
from datetime import time, date, datetime, timedelta
from eoxserver.services.ows.wps.parameters import (
    Boolean, Integer, Double, String,
    Duration, Date, Time, DateTime, DateTimeTZAware, CRSType,
)

# -----------------------------------------------------------------------------


class BaseTestMixin(object):
    # pylint: disable=invalid-name
    def testGeneral(self):
        self.assertTrue(self.name == self.dtype.name)
        self.assertTrue(self.dtype_diff is self.dtype.get_diff_dtype())

    def testParseOK(self):
        for src, dst in self.parsed:
            try:
                res = self.dtype.parse(src)
            except:
                print ("\n%s: input: %r" % (type(self).__name__, src))
                raise

            try:
                self.assertTrue(isinstance(res, type(dst)))
                self.assertTrue(res == dst or (res != res and dst != dst))
            except:
                print ("\n%s: %r != %r" % (type(self).__name__, res, dst))
                raise

    def testEncodeOK(self):
        for src, dst in self.encoded:
            try:
                res = self.dtype.encode(src)
            except:
                print ("\n%s: input: %r" % (type(self).__name__, src))
                raise
            try:
                self.assertTrue(isinstance(res, type(dst)))
                self.assertTrue(res == dst)
            except:
                print ("\n%s: %r != %r" % (type(self).__name__, res, dst))
                raise

    def testParseFail(self):
        for src in self.parsed_rejected:
            try:
                self.assertRaises(ValueError, self.dtype.parse, src)
            except:
                raise Exception(src)

    def testEncodeFail(self):
        for src in self.encoded_rejected:
            self.assertRaises(ValueError, self.dtype.encode, src)


class TimeZoneTestMixin(object):
    # pylint: disable=invalid-name, too-few-public-methods
    def testParseTimeZone(self):
        for src, dst in self.parsed:
            try:
                res = self.dtype.parse(src)
            except:
                print ("\n input: %r" % src)
                raise
            try:
                if dst.tzinfo is None:
                    self.assertTrue(res.tzinfo is None)
                else:
                    self.assertTrue(res.tzinfo is not None)
                    self.assertTrue(res.utcoffset() == dst.utcoffset())
            except:
                print ("\n%r != %r" % (res, dst))
                raise

# -----------------------------------------------------------------------------

class TestDataTypeBool(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'boolean'
        self.dtype = Boolean
        self.dtype_diff = self.dtype
        self.encoded = [
            (True, 'true'),
            (1, 'true'),
            ('Anything', 'true'),
            (False, 'false'),
            (0, 'false'),
            (None, 'false'),
            ([], 'false'),
        ]
        self.encoded_rejected = []
        self.parsed = [
            ('true', True),
            ('1', True),
            ('false', False),
            ('0', False),
            (True, True),
            (self, True),
            (False, False),
            (None, False),
            ([], False),
        ]
        self.parsed_rejected = [
            'string',
            'unicode',
        ]


class TestDataTypeInt(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'integer'
        self.dtype = Integer
        self.dtype_diff = self.dtype
        self.encoded = [
            (1, '1'),
            (-1, '-1'),
            (False, '0'),
            (True, '1'),
            (0xFFFFFFFFFFFFFFFFFF, '4722366482869645213695'),
            (-0xFFFFFFFFFFFFFFFFFF, '-4722366482869645213695'),
        ]
        self.encoded_rejected = [
            float('NaN'),
            'anything',
        ]

        self.parsed = [
            ('+0', 0),
            ('-0', 0),
            ('24', 24),
            ('32145', 32145),
            (-1, -1),
            ('4722366482869645213695', 0xFFFFFFFFFFFFFFFFFF),
            ('-4722366482869645213695', -4722366482869645213695),
        ]
        self.parsed_rejected = [
            'nan',
            '-inf',
            '24anything',
            '2.5'
        ]


class TestDataTypeFloat(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'double'
        self.dtype = Double
        self.dtype_diff = self.dtype
        self.encoded = [
            (1e250, '1e+250'),
            (-1e-250, '-1e-250'),
            (-12345678.9012345678, '-12345678.9012346'),
            (0.6666666666666666, '0.666666666666667'),
            (-0.0, '-0'),
            (float('-inf'), '-inf'),
            (float('nan'), 'nan'),
        ]
        self.encoded_rejected = [
            'anything',
        ]
        self.parsed = [
            ('1e250', 1e+250),
            ('-1e-250', -1e-250),
            ('16.25', 16.25),
            ('-inf', float('-inf')),
            ('nan', float('nan')),
        ]
        self.parsed_rejected = [
            '24anything',
        ]


class TestDataTypeString(TestCase, BaseTestMixin):
    def setUp(self):
        sample_unicode = 'P\u0159\xedli\u0161\u017elu\u0165ou\u010dk\xfd k' \
                      '\u016f\u0148 \xfap\u011bl\u010f\xe1belsk\xe9 \xf3dy.'
        self.name = 'string'
        self.dtype = String
        self.dtype_diff = None
        self.encoded = [
            ('TEST', 'TEST'),
            (sample_unicode, sample_unicode),
        ]
        self.encoded_rejected = []
        self.parsed = [
            (sample_unicode, sample_unicode),
        ]
        self.parsed_rejected = []


class TestDataTypeDuration(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'duration'
        self.dtype = Duration
        self.dtype_diff = self.dtype
        self.encoded = [
            (timedelta(2, 11911, 654321), 'P2DT3H18M31.654321S'),
            (-timedelta(2, 11911, 654321), '-P2DT3H18M31.654321S'),
            (timedelta(2, 11911, 0), 'P2DT3H18M31S'),
            (-timedelta(2, 11911, 0), '-P2DT3H18M31S'),
            (timedelta(2, 0, 654321), 'P2DT0.654321S'),
            (timedelta(2, 0, 654321), 'P2DT0.654321S'),
            (-timedelta(561, 0, 0), '-P561D'),
            (-timedelta(561, 0, 0), '-P561D'),
            (timedelta(0, 11911, 654321), 'PT3H18M31.654321S'),
            (-timedelta(0, 11911, 654321), '-PT3H18M31.654321S'),
            (timedelta(0, 0, 0), 'PT0S'),
            (-timedelta(0, 0, 0), 'PT0S'),
        ]
        self.encoded_rejected = [
            'anything',
        ]
        self.parsed = [
            ('P4Y3M2DT3H18M31.654321S', timedelta(1552, 11911, 654321)),
            ('-P4Y3M2DT3H18M31.654321S', -timedelta(1552, 11911, 654321)),
            ('P1.6Y1.6M1.6DT1.6H1.6M0S', timedelta(633, 57696, 0)),
            ('-P1.6Y1.6M1.6DT1.6H1.6M0S', -timedelta(633, 57696, 0)),
            ('PT0S', timedelta(0, 0, 0)),
            ('P0Y', timedelta(0, 0, 0)),
        ]
        self.parsed_rejected = [
            'anything',
            'P1S',
            'P1H',
            'PT1Y',
            'PT1D',
        ]


class TestDataTypeDate(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'date'
        self.dtype = Date
        self.dtype_diff = Duration
        self.encoded = [
            (date(1830, 6, 7), '1830-06-07'),
            (date(2014, 3, 31), '2014-03-31'),
        ]
        self.encoded_rejected = [
            'anything',
        ]
        self.parsed = [
            (date(1830, 6, 7), date(1830, 6, 7)),
            ('1830-06-07', date(1830, 6, 7)),
            ('2014-03-31', date(2014, 3, 31)),
        ]
        self.parsed_rejected = [
            'anything',
            '2014-02-29',
            '2014-13-01',
            '2014-02-00',
            '2014-00-01'
        ]


class TestDataTypeTime(TestCase, BaseTestMixin):
    # TODO: time-zones
    def setUp(self):
        self.name = 'time'
        self.dtype = Time
        self.dtype_diff = Duration
        self.encoded = [
            (time(0, 0, 0, 0), '00:00:00'),
            (time(12, 30, 30, 500000), '12:30:30.500000'),
            (time(23, 59, 59, 999999), '23:59:59.999999'),
        ]
        self.encoded_rejected = [
            'anything',
        ]
        self.parsed = [
            (time(12, 30, 30, 500000), time(12, 30, 30, 500000)),
            ('00:00:00Z', time(0, 0, 0, 0)),
            ('24:00:00Z', time(0, 0, 0, 0)),
            ('12:30:30.5', time(12, 30, 30, 500000)),
            ('23:59:59.999999+01:30', time(23, 59, 59, 999999)),
        ]
        self.parsed_rejected = [
            'anything',
            '24:00:00.000001',
            '18:60:00',
            '18:30:60',
        ]


class TestDataTypeDateTime(TestCase, BaseTestMixin, TimeZoneTestMixin):
    def setUp(self):
        self.name = 'dateTime'
        self.dtype = DateTime
        self.dtype_diff = Duration
        self.encoded = [
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC),
                '2014-06-01T12:30:14.123456Z'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 500000, DateTime.TZOffset(90)),
                '2014-06-01T12:30:14.500000+01:30'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 0, 0, DateTime.UTC),
                '2014-06-01T12:30:00Z'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 0, 0),
                '2014-06-01T12:30:00'
            ),
        ]
        self.encoded_rejected = [
            'anything'
        ]
        self.parsed = [
            (
                datetime(2014, 6, 1, 11, 00, 14, 123456),
                datetime(2014, 6, 1, 11, 00, 14, 123456)
            ),
            (
                datetime(2014, 6, 1, 11, 00, 14, 123456, DateTime.TZOffset(90)),
                datetime(2014, 6, 1, 11, 00, 14, 123456, DateTime.TZOffset(90))
            ),
            (
                datetime(2014, 6, 1, 11, 00, 14, 123456, DateTime.UTC),
                datetime(2014, 6, 1, 11, 00, 14, 123456, DateTime.UTC)),
            (
                '2014-06-01T12:30:14.123456',
                datetime(2014, 6, 1, 12, 30, 14, 123456)),
            (
                '2014-06-01T12:30:14.123456Z',
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC)
            ),
            (
                '2014-06-01T12:30:14.123456+01:30',
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(90))
            ),
            (
                '2014-06-01 12:30:14',
                datetime(2014, 6, 1, 12, 30, 14, 0)
            ),
            (
                '2014-06-01T00:00Z',
                datetime(2014, 6, 1, 0, 0, 0, 0, DateTime.UTC)
            ),
            (
                '2014-06-01T24:00Z',
                datetime(2014, 6, 2, 0, 0, 0, 0, DateTime.UTC)
            ),
        ]
        self.parsed_rejected = [
            'anything',
            '2014-06-01T12:30:60',
            '2014-06-01T12:60:30',
            '2014-06-01T24:00:00.000001',
            '2014-02-29T00:00',
            '2014-13-01T00:00',
            '2014-02-00T00:00',
            '2014-00-01T00:00',
        ]


class TestDataTypeDateTimeTZAware(TestCase, BaseTestMixin, TimeZoneTestMixin):
    def setUp(self):
        self.name = 'dateTime'
        self.dtype = DateTimeTZAware(DateTime.TZOffset(90))
        self.dtype_diff = Duration
        self.encoded = [
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456),
                '2014-06-01T12:30:14.123456+01:30'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90)),
                '2014-06-01T12:30:14.123456-01:30'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC),
                '2014-06-01T12:30:14.123456Z'
            ),
        ]
        self.encoded_rejected = []
        self.parsed = [
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90)),
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90))
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456),
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(90))
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC),
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC)
            ),
            (
                '2014-06-01T12:30:14.123456-01:30',
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90))
            ),
            (
                '2014-06-01 12:30:14',
                datetime(2014, 6, 1, 12, 30, 14, 0, DateTime.TZOffset(90))
            ),
            (
                '2014-06-01T00:00Z',
                datetime(2014, 6, 1, 0, 0, 0, 0, DateTime.UTC)
            ),
        ]
        self.parsed_rejected = []


class TestDataTypeDateTimeTZAwareWithTZConversion(TestCase, BaseTestMixin, TimeZoneTestMixin):
    def setUp(self):
        self.name = 'dateTime'
        self.dtype = DateTimeTZAware(DateTime.TZOffset(90), DateTime.TZOffset(-120))
        self.dtype_diff = Duration
        self.encoded = [
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456),
                '2014-06-01T09:00:14.123456-02:00'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90)),
                '2014-06-01T12:00:14.123456-02:00'
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC),
                '2014-06-01T10:30:14.123456-02:00'
            ),
        ]
        self.encoded_rejected = []
        self.parsed = [
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.TZOffset(-90)),
                datetime(2014, 6, 1, 12, 0, 14, 123456, DateTime.TZOffset(-120))
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456),
                datetime(2014, 6, 1, 9, 0, 14, 123456, DateTime.TZOffset(-120))
            ),
            (
                datetime(2014, 6, 1, 12, 30, 14, 123456, DateTime.UTC),
                datetime(2014, 6, 1, 10, 30, 14, 123456, DateTime.TZOffset(-120))
            ),
            (
                '2014-06-01T12:30:14.123456-01:30',
                datetime(2014, 6, 1, 12, 0, 14, 123456, DateTime.TZOffset(-120))
            ),
            (
                '2014-06-01 12:30:14',
                datetime(2014, 6, 1, 9, 0, 14, 0, DateTime.TZOffset(-120))
            ),
            (
                '2014-06-01T00:00Z',
                datetime(2014, 5, 31, 22, 0, 0, 0, DateTime.TZOffset(-120))
            ),
        ]
        self.parsed_rejected = []


class TestDataTypeCRS(TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'anyURI'
        self.dtype = CRSType
        self.dtype_diff = None
        self.encoded = [
            (0, 'ImageCRS'),
            (4326, 'http://www.opengis.net/def/crs/EPSG/0/4326'),
        ]
        self.encoded_rejected = [
            -1,
        ]
        self.parsed = [
            ('ImageCRS', 0),
            ('EPSG:4326', 4326),
            ('http://www.opengis.net/def/crs/EPSG/0/4326', 4326),
            ('urn:ogc:def:crs:epsg:6.2:4326', 4326)
        ]
        self.parsed_rejected = [
            "anything",
            "EPSG:0"
        ]

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
