#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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


from eoxserver.core import Component, implements
from eoxserver.services.ows.interfaces import ExceptionHandlerInterface
from eoxserver.services.ows.common.v20.encoders import OWS20ExceptionXMLEncoder
from eoxserver.core.decoders import (
    DecodingException, MissingParameterException
)


CODES_404 = frozenset((
    "NoSuchCoverage", "NoSuchDatasetSeriesOrCoverage", "InvalidAxisLabel",
    "InvalidSubsetting", "InterpolationMethodNotSupported", "NoSuchField",
    "InvalidFieldSequence", "InvalidScaleFactor", "InvalidExtent",
    "ScaleAxisUndefined", "SubsettingCrs-NotSupported", "OutputCrs-NotSupported",
    "CompressionNotSupported", "CompressionInvalid", "JpegQualityInvalid",
    "PredictorInvalid", "PredictorNotSupported", "InterleavingInvalid",
    "TilingInvalid"

))


class WCS20ExceptionHandler(Component):
    implements(ExceptionHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = None

    def handle_exception(self, request, exception):
        message = str(exception)
        code = getattr(exception, "code", None)
        locator = getattr(exception, "locator", None)
        status = 400

        if code is None:
            if isinstance(exception, MissingParameterException):
                code = "MissingParameterValue"
            elif isinstance(exception, DecodingException):
                code = "InvalidParameterValue"
            else:
                code = "InvalidRequest"

        if code in CODES_404:
            status = 404
        elif code in ("OperationNotSupported", "OptionNotSupported"):
            status = 501

        encoder = OWS20ExceptionXMLEncoder()
        xml = encoder.serialize(
            encoder.encode_exception(message, "2.0.1", code, locator)
        )

        return (xml, encoder.content_type, status)
