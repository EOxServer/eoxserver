#-------------------------------------------------------------------------------
#
#  WPS input and output parameters and data types
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

from .base import Parameter
from .literaldata import LiteralData
from .complexdata import (
    ComplexData, CDBase, CDObject, CDTextBuffer, CDByteBuffer,
    CDAsciiTextBuffer, CDFile, CDPermanentFile,
)
from .formats import (
    Format, FormatText, FormatXML, FormatJSON,
    FormatBinaryRaw, FormatBinaryBase64,
)
from .codecs import Codec, CodecBase64, CodecRaw
from .bboxdata import BoundingBox, BoundingBoxData
from .units import UnitOfMeasure, UnitLinear
from .allowed_values import (
    BaseAllowed, AllowedAny, AllowedEnum, AllowedRange,
    AllowedRangeCollection, AllowedByReference
)
from .data_types import (
    DTYPES, BaseType, Boolean, Integer, Double, String,
    Duration, Date, Time, DateTime
)
from .crs import CRSType
from .inputs import InputReference, InputData
from .response_form import (
    Output, ResponseForm, ResponseDocument, RawDataOutput
)

def fix_parameter(name, prm):
    """ Expand short-hand definition of the parameter."""
    if isinstance(prm, Parameter):
        return prm
    return LiteralData(name, dtype=prm)
