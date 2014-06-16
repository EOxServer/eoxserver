#-------------------------------------------------------------------------------
#
#  WPS Literal Data - allowed values - debuging unit-tests
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
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

import datetime as dt
import unittest
from parameters import (BaseType, Boolean, Integer, Double, String,
                        Duration, Date, Time, DateTime, CRSType)

#------------------------------------------------------------------------------

class BaseTestMixin(object):
    def testGeneral(self):
        self.assertTrue( self.name == self.dtype.name )
        self.assertTrue( self.dtype_diff is self.dtype.get_diff_dtype() )

    def testParseOK(self):
        for src, dst in self.parsed:
            res = self.dtype.parse(src)
            self.assertTrue( isinstance(res,type(dst)) )
            self.assertTrue( res == dst or (res!=res and dst!=dst) )

    def testEncodeOK(self):
        for src, dst in self.encoded:
            res = self.dtype.encode(src)
            self.assertTrue( isinstance(res,type(dst)) )
            self.assertTrue( res == dst )

    def testParseFail(self):
        for src in self.parsed_rejected:
            def test():
                self.dtype.parse(src)
            self.assertRaises(ValueError,test)

    def testEncodeFail(self):
        for src in self.encoded_rejected:
            def test():
                self.dtype.encode(src)
            self.assertRaises(ValueError,test)

#------------------------------------------------------------------------------

class TestDataTypeBool(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'boolean'
        self.dtype = Boolean
        self.dtype_diff = self.dtype
        self.encoded= [(True,u'true'), (1,u'true'), ('Anything',u'true'),
            (False,u'false'), (0,u'false'), (None,u'false'), ([],u'false')]
        self.encoded_rejected = []

        self.parsed= [('true',True), ('1',True), ('false',False), ('0',False),
            (True,True), (self,True), (False,False), (None,False), ([],False)]
        self.parsed_rejected = ['string',u'unicode']


class TestDataTypeInt(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'integer'
        self.dtype = Integer
        self.dtype_diff = self.dtype
        self.encoded= [ (1,u'1'), (-1,u'-1'), (False, u'0'), (True, u'1'),
            (0xFFFFFFFFFFFFFFFFFF,u'4722366482869645213695'),
            (-0xFFFFFFFFFFFFFFFFFF,u'-4722366482869645213695'), ]
        self.encoded_rejected = [float('NaN'), 'anything']

        self.parsed= [(u'+0',0), (u'-0',0), ('24',24), ('32145',32145), (-1,-1),
            (u'4722366482869645213695',0xFFFFFFFFFFFFFFFFFF),
            ('-4722366482869645213695',-4722366482869645213695L), ]
        self.parsed_rejected = ['nan',u'-inf',u'24anything','2.5']


class TestDataTypeFloat(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'double'
        self.dtype = Double
        self.dtype_diff = self.dtype
        self.encoded= [
            (1e250, u'1e+250'), (-1e-250, u'-1e-250'),
            (-12345678.9012345678, u'-12345678.9012346'),
            (0.6666666666666666, u'0.666666666666667'), (-0.0, u'-0'),
            (float('-inf'), u'-inf'), (float('nan'), u'nan'),
        ]
        self.encoded_rejected = ['anything']
        self.parsed= [ (u'1e250', 1e+250), ('-1e-250', -1e-250),
            ('16.25', 16.25), ('-inf',float('-inf')), ('nan',float('nan')),]
        self.parsed_rejected = [u'24anything']


class TestDataTypeString(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        sample_unicode = u'P\u0159\xedli\u0161\u017elu\u0165ou\u010dk\xfd k' \
                      u'\u016f\u0148 \xfap\u011bl\u010f\xe1belsk\xe9 \xf3dy.'
        sample_str_utf8 = sample_unicode.encode('utf-8')
        self.name = 'string'
        self.dtype = String
        self.dtype_diff = None
        self.encoded= [('TEST',u'TEST'), (sample_unicode,sample_unicode)]#, (sample_str_utf8,sample_unicode) ]
        self.encoded_rejected = []
        self.parsed= [(sample_unicode,sample_unicode)]#, (sample_str_utf8,sample_unicode) ]
        self.parsed_rejected = []


class TestDataTypeDuration(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'duration'
        self.dtype = Duration
        self.dtype_diff = self.dtype
        self.encoded= [
            (dt.timedelta(2,11911,654321),u'P2DT3H18M31.654321S'),
            (-dt.timedelta(2,11911,654321),u'-P2DT3H18M31.654321S'),
            (dt.timedelta(2,11911,0),u'P2DT3H18M31S'),
            (-dt.timedelta(2,11911,0),u'-P2DT3H18M31S'),
            (dt.timedelta(2,0,654321),u'P2DT0.654321S'),
            (dt.timedelta(2,0,654321),u'P2DT0.654321S'),
            (-dt.timedelta(561,0,0),u'-P561D'),
            (-dt.timedelta(561,0,0),u'-P561D'),
            (dt.timedelta(0,11911,654321),u'PT3H18M31.654321S'),
            (-dt.timedelta(0,11911,654321),u'-PT3H18M31.654321S'),
            (dt.timedelta(0,0,0),u'PT0S'),
            (-dt.timedelta(0,0,0),u'PT0S'),
        ]
        self.encoded_rejected = ['anything']
        self.parsed= [
            (u'P4Y3M2DT3H18M31.654321S', dt.timedelta(1552,11911,654321)),
            ('-P4Y3M2DT3H18M31.654321S', -dt.timedelta(1552,11911,654321)),
            (u'P1.6Y1.6M1.6DT1.6H1.6M0S', dt.timedelta(633,57696,0)),
            (u'-P1.6Y1.6M1.6DT1.6H1.6M0S', -dt.timedelta(633,57696,0)),
            (u'PT0S', dt.timedelta(0,0,0)),
            (u'P0Y', dt.timedelta(0,0,0)),
        ]
        self.parsed_rejected = [u'anything']


class TestDataTypeDate(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'date'
        self.dtype = Date
        self.dtype_diff = Duration
        self.encoded= [
            (dt.date(1830,6,7),u'1830-06-07'),
            (dt.date(2014,3,31),u'2014-03-31'),
        ]
        self.encoded_rejected = ['anything']
        self.parsed= [
            (dt.date(1830,6,7), dt.date(1830,6,7)),
            (u'1830-06-07',dt.date(1830,6,7)),
            ('2014-03-31',dt.date(2014,3,31)),
        ]
        self.parsed_rejected = [u'anything', u'2014-02-29', u'2014-13-01',
            u'2014-02-00', u'2014-00-01']


class TestDataTypeTime(unittest.TestCase, BaseTestMixin):
    # TODO: time-zones
    def setUp(self):
        self.name = 'time'
        self.dtype = Time
        self.dtype_diff = Duration
        self.encoded= [
            (dt.time(0,0,0,0), u'00:00:00'),
            (dt.time(12,30,30,500000), u'12:30:30.500000'),
            (dt.time(23,59,59,999999), u'23:59:59.999999'),
        ]
        self.encoded_rejected = ['anything']
        self.parsed= [
            (dt.time(12,30,30,500000),dt.time(12,30,30,500000)),
            ( u'00:00:00Z', dt.time(0,0,0,0)),
            ('12:30:30.5', dt.time(12,30,30,500000)),
            ('23:59:59.999999+01:30', dt.time(23,59,59,999999)),
        ]
        self.parsed_rejected = [u'anything',
            '24:00:00', '18:60:00', '18:30:60',
        ]


class TestDataTypeTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        UTC = DateTime.UTC
        TZOffset = DateTime.TZOffset
        self.name = 'dateTime'
        self.dtype = DateTime
        self.dtype_diff = Duration
        # NOTE: The eoxserver isoformat tool localizes the time-zone unaware
        #       time by adding the UTC timezone!
        self.encoded= [
            (dt.datetime(2014,6,1,12,30,14,123456,UTC), u'2014-06-01T12:30:14.123456Z'),
            (dt.datetime(2014,6,1,12,30,14,500000,TZOffset(90)),
                                        u'2014-06-01T12:30:14.500000+01:30'),
            (dt.datetime(2014,6,1,12,30,0,0,UTC), u'2014-06-01T12:30:00Z'),
            (dt.datetime(2014,6,1,12,30,0,0), u'2014-06-01T12:30:00Z'),
        ]
        self.encoded_rejected = ['anything']
        self.parsed= [
            (dt.datetime(2014,6,1,11,00,14,123456,UTC),dt.datetime(2014,6,1,11,00,14,123456,UTC)),
            (u'2014-06-01T12:30:14.123456',dt.datetime(2014,6,1,12,30,14,123456)),
            (u'2014-06-01T12:30:14.123456Z',dt.datetime(2014,6,1,12,30,14,123456,UTC)),
            (u'2014-06-01T12:30:14.123456+01:30',dt.datetime(2014,6,1,11,00,14,123456,UTC)),
            (u'2014-06-01 12:30:14',dt.datetime(2014,6,1,12,30,14,0)),
            (u'2014-06-01T00:00Z',dt.datetime(2014,6,1,0,0,0,0,UTC)),
        ]
        self.parsed_rejected = [u'anything',
            u'2014-06-01T12:30:60', u'2014-06-01T12:60:30',
            u'2014-06-01T24:00:00',
            u'2014-02-29T00:00', u'2014-13-01T00:00',
            u'2014-02-00T00:00', u'2014-00-01T00:00',
        ]

class TestDataTypeCRS(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.name = 'anyURI'
        self.dtype = CRSType 
        self.dtype_diff = None
        self.encoded= [(0,u'ImageCRS'), 
            (4326, u'http://www.opengis.net/def/crs/EPSG/0/4326'), ]
        self.encoded_rejected = [-1]
        self.parsed= [ ('ImageCRS',0), ('EPSG:4326',4326), 
            ('http://www.opengis.net/def/crs/EPSG/0/4326',4326), 
            ('urn:ogc:def:crs:epsg:6.2:4326',4326)]
        self.parsed_rejected = ["anything", "EPSG:0"]

#------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
