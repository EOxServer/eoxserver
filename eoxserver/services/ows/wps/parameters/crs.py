#-------------------------------------------------------------------------------
#
#  CRS data type.
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

from eoxserver.resources.coverages.crss import (
    asURL, fromURL, fromURN, fromShortCode, validateEPSGCode, parseEPSGCode,
)
from .data_types import BaseType
from django.utils.encoding import smart_str


class CRSType(BaseType):
    """ CRS data-type.
        CRS are represented by the EPSG codes + 0 meaning the ImageCRC.
    """
    name = "anyURI"
    dtype = int
    zero = None
    comparable = False

    @classmethod
    def parse(cls, raw_value):
        """ Cast or parse input to its proper representation."""
        if isinstance(raw_value, cls.dtype):
            if raw_value == 0 or validateEPSGCode(raw_value):
                return raw_value
        else:
            if raw_value == "ImageCRS":
                return 0
            else:
                value = parseEPSGCode(
                    raw_value, (fromURL, fromURN, fromShortCode)
                )
                if value is not None:
                    return value
        raise ValueError("Invalid CRS %r!" % raw_value)

    @classmethod
    def encode(cls, value):
        """ Encode value to a Unicode string."""
        if value == 0:
            return u'ImageCRS'
        elif validateEPSGCode(value):
            return smart_str(asURL(value))
        raise ValueError("Invalid CRS %r!" % value)

    @classmethod
    def get_diff_dtype(cls):  # string has no difference
        return None
