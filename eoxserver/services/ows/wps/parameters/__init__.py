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
    CDAsciiTextBuffer, CDFileWrapper, CDFile, CDPermanentFile,
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
    Duration, Date, Time, DateTime, DateTimeTZAware
)
from .crs import CRSType
from .inputs import InputReference, InputData
from .response_form import (
    Output, ResponseForm, ResponseDocument, RawDataOutput
)

class RequestParameter(object):
    """ Special input parameter extracting input from the request metadata.
    This might be used to pass information such as, e.g., HTTP headers or
    user authentication to the process like a regular input variable.

    This class is the base class and it expected that `parse_request`
    method get overloaded by inheritance or by a function passed as
    an argument to the constructor.
    """
    # pylint: disable=method-hidden, too-few-public-methods

    def __init__(self, request_parser=None):
        if request_parser:
            self.parse_request = request_parser

    def parse_request(self, request):
        """ Method extracting information from the Django HTTP request object.
        """
        raise NotImplementedError


def fix_parameter(name, prm):
    """ Expand short-hand definition of the parameter."""
    if isinstance(prm, Parameter):
        return prm
    elif isinstance(prm, RequestParameter):
        # The leading backslash indicates an internal parameter.
        # Note: backslash is not an allowed URI character and it cannot appear
        # in the WPS inputs' names.
        prm.identifier = "\\" + name
        return prm
    else:
        return LiteralData(name, dtype=prm)


class Reference(object):
    """ Output reference. An instance of this class defines a CommplexData
    output passed by a reference. The output must be stored in a file.

    Constructor parameters:
        path        path to the output file in the local file-system
        href        public URL of the output reference
        mime_type   output ComplexData mime-type
        encoding    output ComplexData encoding
        schema      output ComplexData schema
    """
    # pylint: disable=too-few-public-methods, too-many-arguments
    def __init__(self, path, href, mime_type=None, encoding=None, schema=None,
                 **kwarg):
        self.path = path
        self.href = href
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema
