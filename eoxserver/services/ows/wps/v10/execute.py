#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

import urllib2
from urlparse import urlparse
import logging

from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.util import multiparttools as mp
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface,
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.exceptions import (
    NoSuchProcessError, MissingRequiredInputError,
    InvalidInputError, InvalidOutputError, InvalidOutputDefError,
    InvalidInputReferenceError, InvalidInputValueError,
)
from eoxserver.services.ows.wps.parameters import (
    fix_parameter, LiteralData, BoundingBoxData, ComplexData,
    InputReference, InputData,
)
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ExecuteResponseXMLEncoder, WPS10ExecuteResponseRawEncoder
)
from eoxserver.services.ows.wps.v10.execute_decoder_xml import (
    WPS10ExecuteXMLDecoder
)
from eoxserver.services.ows.wps.v10.execute_decoder_kvp import (
    WPS10ExecuteKVPDecoder
)

LOGGER = logging.getLogger(__name__)

class WPS10ExcecuteHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    service = "WPS"
    versions = ("1.0.0",)
    request = "Execute"

    processes = ExtensionPoint(ProcessInterface)
    #result_storage = ExtensionPoint(ResultStorageInterface)

    @staticmethod
    def get_decoder(request):
        if request.method == "GET":
            return WPS10ExecuteKVPDecoder(request.GET)
        elif request.method == "POST":
            # support for multipart items
            if request.META["CONTENT_TYPE"].startswith("multipart/"):
                _, data = next(mp.iterate(request.body))
                return WPS10ExecuteXMLDecoder(data)
            return WPS10ExecuteXMLDecoder(request.body)

    def get_process(self, identifier):
        for process in self.processes:
            if process.identifier == identifier:
                return process
        raise NoSuchProcessError(identifier)

    def handle(self, request):
        decoder = self.get_decoder(request)
        process = self.get_process(decoder.identifier)
        input_defs, input_ids = _normalize_params(process.inputs)
        output_defs, output_ids = _normalize_params(process.outputs)
        raw_inputs = decoder.inputs
        resp_form = decoder.response_form

        _check_invalid_inputs(input_ids, raw_inputs)
        _check_invalid_outputs(output_ids, resp_form)

        inputs = {}
        inputs.update(prepare_process_output_requests(output_defs, resp_form))
        inputs.update(decode_process_inputs(input_defs, raw_inputs, request))

        outputs = process.execute(**inputs)

        packed_outputs = pack_process_outputs(output_defs, outputs, resp_form)

        if resp_form.raw:
            encoder = WPS10ExecuteResponseRawEncoder()
        else:
            encoder = WPS10ExecuteResponseXMLEncoder()

        response = encoder.encode_response(
            process, packed_outputs, resp_form, inputs, raw_inputs
        )

        return encoder.serialize(response, encoding='utf-8')


def _normalize_params(param_defs):
    if isinstance(param_defs, dict):
        param_defs = param_defs.iteritems()
    params, param_ids = [], []
    for name, param in param_defs:
        param = fix_parameter(name, param) # short-hand def. expansion
        param_ids.append(param.identifier)
        params.append((name, param))
    return params, param_ids

def _check_invalid_inputs(input_ids, inputs):
    invalids = set(inputs) - set(input_ids)
    if len(invalids):
        raise InvalidInputError(invalids.pop())

def _check_invalid_outputs(output_ids, outputs):
    invalids = set(outputs) - set(output_ids)
    if len(invalids):
        raise InvalidOutputError(invalids.pop())


def decode_process_inputs(input_defs, raw_inputs, request):
    """ Iterates over all input options stated in the process and parses
        all given inputs. This also includes resolving references
    """
    decoded_inputs = {}
    for name, prm in input_defs:
        raw_value = raw_inputs.get(prm.identifier)
        if raw_value is not None:
            if isinstance(raw_value, InputReference):
                try:
                    raw_value = _resolve_reference(raw_value, request)
                except ValueError as exc:
                    raise InvalidInputReferenceError(prm.identifier, exc)
            try:
                value = _decode_input(prm, raw_value)
            except ValueError as exc:
                raise InvalidInputValueError(prm.identifier, exc)
        elif prm.is_optional:
            value = getattr(prm, 'default', None)
        else:
            raise MissingRequiredInputError(prm.identifier)
        decoded_inputs[name] = value
    return decoded_inputs

def prepare_process_output_requests(output_defs, response_form):
    """ Complex data format selection (mimeType, encoding, schema)
        is passed as an input to the process
    """
    output_requests = {}
    for name, prm in output_defs:
        outreq = response_form.get_output(prm.identifier)
        if isinstance(prm, ComplexData):
            format_ = prm.get_format(
                outreq.mime_type, outreq.encoding, outreq.schema
            )
            if format_ is None:
                raise InvalidOutputDefError(
                    prm.identifier, "Invalid complex data format!"
                    " mimeType=%r encoding=%r schema=%r" % (
                        outreq.mime_type, outreq.encoding, outreq.schema
                    )
                )
            output_requests[name] = {
                "mime_type": format_.mime_type,
                "encoding": format_.encoding,
                "schema": format_.schema,
            }
    return output_requests

def pack_process_outputs(output_defs, results, response_form):
    """ Collect data, output declaration and output request for each item."""
    # Normalize the outputs to a dictionary.
    if not isinstance(results, dict):
        if len(output_defs) == 1:
            results = {output_defs[0][0]: results}
        else:
            results = dict(results)
    # Pack the results to a tuple containing:
    #   - the output data (before encoding)
    #   - the process output declaration (ProcessDescription/Output)
    #   - the output's requested form (RequestForm/Output)
    packd_results = OrderedDict()
    for name, prm in output_defs:
        outreq = response_form.get_output(prm.identifier)
        result = results.get(name)
        # TODO: Can we silently skip the missing outputs? Check the standard!
        if result is not None:
            packd_results[prm.identifier] = (result, prm, outreq)
        elif isinstance(prm, LiteralData) and prm.default is not None:
            packd_results[prm.identifier] = (prm.default, prm, outreq)
    return packd_results

def _decode_input(prm, raw_value):
    """ Decode raw input and check it agains the allowed values."""
    if isinstance(prm, LiteralData):
        return prm.parse(raw_value.data, raw_value.uom)
    elif isinstance(prm, BoundingBoxData):
        return prm.parse(raw_value.data)
    elif isinstance(prm, ComplexData):
        return prm.parse(raw_value.data, raw_value.mime_type,
                raw_value.schema, raw_value.encoding, urlsafe=raw_value.asurl)
    else:
        raise TypeError("Unsupported parameter type %s!"%(type(prm)))

def _resolve_reference(iref, request):
    """ Get the input passed as a reference."""
    # prepare HTTP/POST request
    if iref.method == "POST":
        if iref.body_href is not None:
            iref.body = _resolve_url(
                iref.body_href, None, iref.headers, request
            )
        if iref.body is not None:
            ValueError("Missing the POST request body!")
    else:
        iref.body = None
    data = _resolve_url(iref.href, iref.body, iref.headers, request)
    return InputData(
        iref.identifier, iref.title, iref.abstract, data,
        None, None, iref.mime_type, iref.encoding, iref.schema
    )

def _resolve_url(href, body, headers, request):
    """ Resolve the input reference URL."""
    LOGGER.debug("resolving: %s%s", href, "" if body is None else " (POST)")
    url = urlparse(href)
    if url.scheme == "cid":
        return _resolve_multipart_related(url.path, request)
    elif url.scheme in ('http', 'https'):
        return _resolve_http_url(href, body, headers)
    else:
        raise ValueError("Unsupported URL scheme %r!"%(url.scheme))

def _resolve_http_url(href, body=None, headers=()):
    """ Resolve the HTTP request."""
    try:
        request = urllib2.Request(href, body, dict(headers))
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.URLError, exc:
        raise ValueError(str(exc))

def _resolve_multipart_related(cid, request):
    """ Resolve reference to another part of the multi-part request."""
    # iterate over the parts to find the correct one
    for headers, data in mp.iterate(request):
        if headers.get("Content-ID") == cid:
            return data
    raise ValueError("No part with content-id '%s'." % cid)
