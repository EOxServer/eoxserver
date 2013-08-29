#-------------------------------------------------------------------------------
# $Id$
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


import re
from datetime import datetime

from eoxserver.core import Component, ExtensionPoint, implements
from eoxserver.contrib import gdal
from eoxserver.resources.coverages.metadata.interfaces import (
    GDALDatasetMetadataReaderInterface
)


class GDALDatasetEnvisatMetadataFormatReader(Component):
    implements(GDALDatasetMetadataReaderInterface)

    def test_ds(self, ds):
        md_dict = ds.GetMetadata_Dict()
        for key in ("MPH_PRODUCT", "MPH_SENSING_START", "MPH_SENSING_STOP"):
            if key not in md_dict:
                return False
        if ds.GetGCPCount() == 0:
            return False

        return True

    def read(self, ds):
        return {
            "identifier": splitext(ds.GetMetadataItem("MPH_PRODUCT"))[0],
            "begin_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_START")),
            "end_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_STOP"))
        }


def parse_datetime(self, timestamp):
    """ Datetime parsing function for special Envisat datetime format.
    """
    MONTHS = {
        "JAN": 1,
        "FEB": 2,
        "MAR": 3,
        "APR": 4,
        "MAY": 5,
        "JUN": 6,
        "JUL": 7,
        "AUG": 8,
        "SEP": 9,
        "OCT": 10,
        "NOV": 11,
        "DEC": 12
    }
    
    m = re.match(r"(\d{2})-([A-Z]{3})-(\d{4}) (\d{2}):(\d{2}):(\d{2}).*", timestamp)
    day = int(m.group(1))
    month = MONTHS[m.group(2)]
    year = int(m.group(3))
    hour = int(m.group(4))
    minute = int(m.group(5))
    second = int(m.group(6))
    
    return datetime(year, month, day, hour, minute, second)
