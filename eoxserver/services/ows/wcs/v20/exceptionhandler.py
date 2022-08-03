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

import traceback

from django.conf import settings
from django.template.loader import render_to_string

from eoxserver.core import Component, implements
from eoxserver.core.decoders import kvp, lower, xml
from eoxserver.services.ows.interfaces import ExceptionHandlerInterface
from eoxserver.services.ows.common.v20.encoders import OWS20ExceptionXMLEncoder
from eoxserver.services.ows.config import DEFAULT_EOXS_WCS_ERROR_HTML_TEMPLATE
from eoxserver.services.ows.wcs.v20.util import ns_wcs
from eoxserver.core.decoders import (
    DecodingException, MissingParameterException
)
from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap


CODES_404 = frozenset((
    "NoSuchCoverage", "NoSuchDatasetSeriesOrCoverage", "InvalidAxisLabel",
    "InvalidSubsetting", "InterpolationMethodNotSupported", "NoSuchField",
    "InvalidFieldSequence", "InvalidScaleFactor", "InvalidExtent",
    "ScaleAxisUndefined", "SubsettingCrs-NotSupported", "OutputCrs-NotSupported",
    "CompressionNotSupported", "CompressionInvalid", "JpegQualityInvalid",
    "PredictorInvalid", "PredictorNotSupported", "InterleavingInvalid",
    "TilingInvalid"

))


class WCS20ExceptionHandlerKVPDecoder(kvp.Decoder):
    exceptions = kvp.Parameter(num="?", type=lower, default="application/xml")


class WCS20ExceptionHandlerXMLDecoder(xml.Decoder):
    namespaces = NameSpaceMap(
        ns_wcs, NameSpace("http://eoxserver.org/eoxs/1.0", "eoxs")
    )
    exceptions = xml.Parameter("wcs:Extension/eoxs:exceptions/text()", num="?", type=lower, default="application/xml")


class OWS20ExceptionHTMLEncoder(object):
    @property
    def content_type(self):
        return "text/html"

    def serialize(self, message):
        # content is already str
        return message

    def encode_exception(self, message, version, code, locator=None, request=None, exception=None):
        template_name = getattr(
            settings,
            'EOXS_ERROR_HTML_TEMPLATE',
            DEFAULT_EOXS_WCS_ERROR_HTML_TEMPLATE,
        )
        # pass in original traceback and debug to allow usage in template
        debug = getattr(settings, 'DEBUG', False)
        stack_trace = traceback.format_exc()

        template_params = {
            "message": message,
            "exception": exception,
            "debug": debug,
            "stack_trace": stack_trace,
        }
        return render_to_string(
            template_name,
            context=template_params,
            request=request
        )


class WCS20ExceptionHandler(Component):
    implements(ExceptionHandlerInterface)

    service = "WCS"
    versions = ("2.0.0", "2.0.1")
    request = None

    def get_encoder(self, request):
        if request.method == "GET":
            decoder = WCS20ExceptionHandlerKVPDecoder(request.GET)
        elif request.method == "POST":
            decoder = WCS20ExceptionHandlerXMLDecoder(request.body)

        if decoder.exceptions == "text/html":
            return OWS20ExceptionHTMLEncoder()
        else:
            return OWS20ExceptionXMLEncoder()

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

        encoder = self.get_encoder(request)
        xml = encoder.serialize(
            encoder.encode_exception(message, "2.0.1", code, locator, request=request, exception=exception)
        )

        return (xml, encoder.content_type, status)
