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


import re
from datetime import datetime
from os.path import splitext

from django.utils.timezone import utc


class GDALDatasetEnvisatMetadataFormatReader(object):
    """ Metadata format reader for specific ENVISAT products.
    """

    def test_ds(self, ds):
        """ Check whether or not the dataset seems to be an ENVISAT image and
            has the correct metadata tags.
        """
        md_dict = ds.GetMetadata_Dict()
        for key in ("MPH_PRODUCT", "MPH_SENSING_START", "MPH_SENSING_STOP"):
            if key not in md_dict:
                return False
        if ds.GetGCPCount() == 0:
            return False

        return True

    def read_ds(self, ds):
        """ Return the ENVISAT specific metadata items.
        """
        return {
            "identifier": splitext(ds.GetMetadataItem("MPH_PRODUCT"))[0],
            "begin_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_START")),
            "end_time": parse_datetime(ds.GetMetadataItem("MPH_SENSING_STOP"))
        }


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


def parse_datetime(timestamp):
    """ Datetime parsing function for special Envisat datetime format.
    """
    
    
    match = re.match(
        r"(\d{2})-([A-Z]{3})-(\d{4}) (\d{2}):(\d{2}):(\d{2}).*", timestamp
    )
    day = int(match.group(1))
    month = MONTHS[match.group(2)]
    year = int(match.group(3))
    hour = int(match.group(4))
    minute = int(match.group(5))
    second = int(match.group(6))
    
    return datetime(year, month, day, hour, minute, second, tzinfo=utc)
