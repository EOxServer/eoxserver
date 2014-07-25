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
from parameters import (AllowedAny, AllowedEnum, AllowedRange,
                        AllowedRangeCollection, LiteralData)

from parameters import (BaseType, Boolean, Integer, Double, String,
                        Duration, Date, Time, DateTime)

#------------------------------------------------------------------------------

class BaseTestMixin:
    def test(self):
        for val in self.accepted:
            self.assertTrue(self.domain.check(val))
            self.assertTrue(val is self.domain.verify(val))
        for val in self.rejected:
            self.assertFalse(self.domain.check(val))
            def test():
                self.domain.verify(val)
            self.assertRaises(ValueError,test)

#------------------------------------------------------------------------------

class TestAllowedAny(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedAny()
        self.accepted = [1.0, 10, dt.datetime.now(), dt.timedelta(days=10,seconds=100)]
        self.rejected = []

#------------------------------------------------------------------------------

class TestAllowedEnumFloat(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedEnum([0.0,0.5,1.0])
        self.accepted = [1.0, 0]
        self.rejected = [-1]

class TestAllowedEnumFloat2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedEnum([0.0,0.5,1.0],dtype=Double)
        self.accepted = [1.0, 0]
        self.rejected = [-1]

class TestAllowedEnumFloat3(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedEnum([0.0,0.5,1.0],dtype=float)
        self.accepted = [1.0, 0]
        self.rejected = [-1]

class TestAllowedEnumInt(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedEnum([0,2,3],dtype=Integer)
        self.accepted = [2, 0]
        self.rejected = [1]

class TestAllowedEnumInt2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedEnum([0,2,3],dtype=int)
        self.accepted = [2, 0]
        self.rejected = [1]

class TestAllowedEnumString(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        enum = ['John','James','Joffrey','Jacob','Jerry']
        self.domain = AllowedEnum(enum,dtype=String)
        self.accepted = ['John','Jacob','Jerry']
        self.rejected = ['Alex','']

class TestAllowedEnumString2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        enum = ['John','James','Joffrey','Jacob','Jerry']
        self.domain = AllowedEnum(enum,dtype=str)
        self.accepted = ['John','Jacob','Jerry']
        self.rejected = ['Alex','']

class TestAllowedEnumString3(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        enum = ['John','James','Joffrey','Jacob','Jerry']
        self.domain = AllowedEnum(enum,dtype=unicode)
        self.accepted = ['John','Jacob','Jerry']
        self.rejected = ['Alex','']

class TestAllowedEnumDate(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['2014-01-01', '2014-02-01', '2014-03-01']
        self.domain = AllowedEnum(vlist, dtype=Date)
        self.accepted = [ vlist[1], Date.parse(vlist[0]) ]
        self.rejected = [ Date.parse('2014-01-02') ] 

class TestAllowedEnumDate2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['2014-01-01', '2014-02-01', '2014-03-01']
        self.domain = AllowedEnum(vlist, dtype=dt.date)
        self.accepted = [ vlist[1], Date.parse(vlist[0]) ]
        self.rejected = [ Date.parse('2014-01-02') ] 

class TestAllowedEnumTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['05:30', '08:20', '16:18']
        self.domain = AllowedEnum(vlist, dtype=Time)
        self.accepted = [ vlist[1], Time.parse(vlist[0]) ]
        self.rejected = [ Time.parse('19:20') ]

class TestAllowedEnumTime2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['05:30', '08:20', '16:18']
        self.domain = AllowedEnum(vlist, dtype=dt.time)
        self.accepted = [ vlist[1], Time.parse(vlist[0]) ]
        self.rejected = [ Time.parse('19:20') ]

class TestAllowedEnumDateTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['2014-01-01T09:30:21Z', '2014-02-01T18:20:15Z', '2014-03-01T12:15:02Z' ]
        self.domain = AllowedEnum(vlist, dtype=DateTime)
        self.accepted = [ vlist[1], DateTime.parse(vlist[0]) ]
        self.rejected = [ DateTime.parse('2014-01-01T12:30:00Z') ] 

class TestAllowedEnumDateTime2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['2014-01-01T09:30:21Z', '2014-02-01T18:20:15Z', '2014-03-01T12:15:02Z' ]
        self.domain = AllowedEnum(vlist, dtype=dt.datetime)
        self.accepted = [ vlist[1], DateTime.parse(vlist[0]) ]
        self.rejected = [ DateTime.parse('2014-01-01T12:30:00Z') ] 

class TestAllowedEnumDuration(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['P1Y', 'P26DT1M', 'P25M16S']
        self.domain = AllowedEnum(vlist, dtype=Duration)
        self.accepted = [ vlist[1], Duration.parse(vlist[0]) ]
        self.rejected = [ Duration.parse('P7D15H8M') ]

class TestAllowedEnumDuration(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        vlist = ['P1Y', 'P26DT1M', 'P25M16S']
        self.domain = AllowedEnum(vlist, dtype=dt.timedelta)
        self.accepted = [ vlist[1], Duration.parse(vlist[0]) ]
        self.rejected = [ Duration.parse('P7D15H8M') ]

#------------------------------------------------------------------------------

class TestAllowedRangeFloat(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0)
        self.accepted = [0.5, 0.0, 1.0]
        self.rejected = [-1.0, 2.0]

class TestAllowedRangeFloat2(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,dtype=Double)
        self.accepted = [0.5, 0.0, 1.0]
        self.rejected = [-1.0, 2.0]

class TestAllowedRangeFloat3(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,dtype=float)
        self.accepted = [0.5, 0.0, 1.0]
        self.rejected = [-1.0, 2.0]

class TestAllowedRangeUnboundMin(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(None,1.0)
        self.accepted = ['-inf',-1.0, 0.5, 0.0, 1.0]
        self.rejected = [2.0]

class TestAllowedRangeUnboundMax(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,None)
        self.accepted = ['+inf',0.5, 0.0, 1.0, 2.0]
        self.rejected = [-1.0]

class TestAllowedRangeFloatClosed(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,'closed')
        self.accepted = [0.5, 0.0, 1.0]
        self.rejected = [-1.0, 2.0]

class TestAllowedRangeFloatOpen(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,'open')
        self.accepted = [0.5]
        self.rejected = [0.0, 1.0, -1.0, 2.0]

class TestAllowedRangeFloatOpenClosed(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,'open-closed')
        self.accepted = [0.5,1.0]
        self.rejected = [0.0,-1.0, 2.0]

class TestAllowedRangeFloatClosedOpen(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,'closed-open')
        self.accepted = [0.5,0.0]
        self.rejected = [1.0,-1.0, 2.0]

class TestAllowedRangeInt(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0,10,dtype=Integer)
        self.accepted = [0, 5, 10]
        self.rejected = [-1, 12]

class TestAllowedRangeIntClosed(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0,10,'open',dtype=Integer)
        self.accepted = [5]
        self.rejected = [0, 10, -1, 12]

class TestAllowedRangeDateClosed(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('2014-02-01', '2014-03-01', 'closed', dtype=Date)
        self.accepted = [ '2014-02-15', '2014-02-01', Date.parse('2014-03-01')]
        self.rejected = [ Date.parse('2014-01-02') ] 

class TestAllowedRangeDateOpen(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('2014-02-01', '2014-03-01', 'open', dtype=Date)
        self.accepted = [ '2014-02-15' ] 
        self.rejected = [ '2014-02-01', Date.parse('2014-03-01'), Date.parse('2014-01-02')] 

class TestAllowedRangeDateClosedOpen(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('10:00', '15:30', 'closed-open', dtype=Time)
        self.accepted = [ '10:00', '12:15']
        self.rejected = [ Time.parse('09:00'), '15:30' , '18:12' ] 

class TestAllowedRangeDateOpenClosed(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('10:00', '15:30', 'open-closed', dtype=Time)
        self.accepted = [ '12:15', '15:30' ]
        self.rejected = [ Time.parse('09:00'), '10:00', '18:12' ] 

class TestAllowedRangeDateTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('2014-02-01T09:30:21Z', '2014-03-01T18:20:15Z', dtype=DateTime)
        self.accepted = ['2014-02-01T09:30:21Z', '2014-02-15T00:00:00Z', '2014-03-01T18:20:15Z']
        self.rejected = ['2014-01-01T00:00:00Z', DateTime.parse('2014-04-01T00:00:00Z')]

class TestAllowedRangeDuration(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange('-P1DT1H', 'P1M0DT30M', dtype=Duration)
        self.accepted = [ Duration.parse('-P1DT1H'), 'P0D' , 'P1M0DT30M'] 
        self.rejected = [ Duration.parse('-P2D18H'), 'P1Y' ]

#------------------------------------------------------------------------------

class TestAllowedRangeDiscrFloat(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0.0,1.0,spacing='0.1')
        self.accepted = [0.5, 0.0, 1.0]
        self.rejected = [0.55,-1.0, 2.0]

class TestAllowedRangeDiscrInt(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        self.domain = AllowedRange(0,10,spacing='2',dtype=int)
        self.accepted = [4, 0, 10]
        self.rejected = [5,-1, 12]

class TestAllowedRangeDiscrDuration(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        v0 = dt.timedelta(0,3600,0)
        v1 = 'PT5H'
        dv = 'PT1H'
        cl ='open-closed'
        self.domain = AllowedRange(v0,v1,cl,spacing=dv,dtype=dt.timedelta)
        self.accepted = [Duration.parse('PT2H'),dt.timedelta(0,3*3600,0),
                        'PT4H', 'PT5H','PT2H0.000001S'] # tolerance: step*1e-9 
        self.rejected = ['PT30M','PT1H','PT2H30M',]

class TestAllowedRangeDiscrTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        v0 = dt.time(9,30,0,0)
        v1 = '16:30'
        dv = 'PT1H'
        cl ='closed'
        self.domain = AllowedRange(v0,v1,cl,spacing=dv,dtype=dt.time)
        self.accepted = ['09:30','10:30','15:30','16:30']
        self.rejected = ['09:00','10:00','16:25','16:35']

class TestAllowedRangeDiscrDate(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        v0 = dt.date(2014,1,1)
        v1 = '2014-01-21'
        dv = 'P5D'
        cl ='closed'
        self.domain = AllowedRange(v0,v1,cl,spacing=dv,dtype=dt.date)
        self.accepted = ['2014-01-01','2014-01-06','2014-01-16','2014-01-21']
        self.rejected = ['2013-12-31','2014-01-10','2014-01-31']

class TestAllowedRangeDiscrDateTime(unittest.TestCase, BaseTestMixin):
    def setUp(self):
        v0 = dt.datetime(2014,1,1,10,30,0,0,DateTime.UTC)
        v1 = '2014-01-10T10:30Z'
        dv = 'P1D'
        cl ='closed'
        self.domain = AllowedRange(v0,v1,cl,spacing=dv,dtype=dt.datetime)
        self.accepted = [ 
            '2014-01-01T10:30Z', '2014-01-02T10:30Z',
            '2014-01-05T10:30Z', '2014-01-07T10:30Z',
            '2014-01-09T10:30Z', '2014-01-10T10:30Z',
        ]
        self.rejected = [
            '2013-12-31T10:30Z', '2014-01-01T11:00Z',
            '2014-01-05T00:00Z', '2014-01-11T10:30Z',
        ]

##------------------------------------------------------------------------------

class TestAllowedRangeCollectionFloat(unittest.TestCase, BaseTestMixin):

    def setUp(self):
        self.domain = AllowedRangeCollection(
            AllowedRange(None,-5.0,'open'),
            AllowedRange(6.0,None,spacing=3.0),
            AllowedEnum(xrange(-4,0)),
            AllowedEnum(range(0,6,2)),
        )
        self.accepted = ['-inf',-100.,-3,2,6,300]
        self.rejected = ['nan','+inf',7,3,-0.5,-5]

#------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
