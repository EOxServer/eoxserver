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

from logging import getLogger

from eoxserver.core.util import multiparttools as mp
from eoxserver.services.ows.wps.interfaces import (
    ProcessInterface, AsyncBackendInterface,
)
from eoxserver.services.ows.wps.util import (
    parse_named_parts, InMemoryURLResolver, get_process_by_identifier
)
from eoxserver.services.ows.wps.exceptions import (
    InvalidParameterValue, StorageNotSupported,
)
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ExecuteResponseXMLEncoder, WPS10ExecuteResponseRawEncoder
)
from eoxserver.services.ows.wps.v10.execute_decoder_xml import (
    WPS10ExecuteXMLDecoder,
)
from eoxserver.services.ows.wps.v10.execute_decoder_kvp import (
    WPS10ExecuteKVPDecoder, parse_query_string,
)
from eoxserver.services.ows.wps.v10.execute_util import (
    parse_params, check_invalid_inputs, check_invalid_outputs,
    decode_raw_inputs, decode_output_requests, pack_outputs,
    resolve_request_parameters,
)

from eoxserver.services.ows.wps.util import get_async_backends


class WPS10ExecuteHandler(object):
    """ WPS 1.0 Execute service handler. """

    service = "WPS"
    versions = ("1.0.0",)
    request = "Execute"
    methods = ['GET', 'POST']

    @staticmethod
    def get_decoder(request):
        """ Get request decoder matching the request format. """
        if request.method == "GET":
            return WPS10ExecuteKVPDecoder(
                parse_query_string(request.META['QUERY_STRING'])
            )
        elif request.method == "POST":
            # support for multipart items
            if request.META["CONTENT_TYPE"].startswith("multipart/"):
                _, data = next(mp.iterate(request.body))
                return WPS10ExecuteXMLDecoder(data)
            return WPS10ExecuteXMLDecoder(request.body)

    def get_async_backend(self):
        """ Get available asynchronous back-end matched by the service version.
        """
        version_set = set(self.versions)
        for backend in get_async_backends():
            if set(backend.supported_versions) & version_set:
                return backend

    def handle(self, request):
        # pylint: disable=redefined-variable-type, too-many-locals
        """ Request handler. """
        logger = getLogger(__name__)
        # decode request
        decoder = self.get_decoder(request)

        # parse named requests parts used in case of cid references
        extra_parts = parse_named_parts(request)

        # get the process and convert input/output definitions to a common format
        process = get_process_by_identifier(decoder.identifier)
        logger.debug("Execute process %s", decoder.identifier)
        input_defs = parse_params(process.inputs)
        output_defs = parse_params(process.outputs)

        # get the unparsed (raw) inputs and the requested response parameters
        raw_inputs = check_invalid_inputs(decoder.inputs, input_defs)
        resp_form = check_invalid_outputs(decoder.response_form, output_defs)

        # resolve the special request input parameters
        raw_inputs = resolve_request_parameters(raw_inputs, input_defs, request)

        if resp_form.raw:
            encoder = WPS10ExecuteResponseRawEncoder(resp_form)
        else:
            encoder = WPS10ExecuteResponseXMLEncoder(
                process, resp_form, raw_inputs
            )

        if not resp_form.raw and resp_form.store_response:
            # asynchronous execution
            async_backend = self.get_async_backend()
            if not async_backend:
                raise StorageNotSupported(
                    "This service instance does not support asynchronous "
                    "execution!"
                )

            if not getattr(process, 'asynchronous', False):
                raise StorageNotSupported(
                    "This process does not allow asynchronous execution!",
                )

            if not resp_form.status:
                raise InvalidParameterValue(
                    "The status update cannot be blocked for an asynchronous "
                    "execute request!", "status"
                )

            # pass the control over the processing to the asynchronous back-end
            job_id = async_backend.execute(
                process, raw_inputs, resp_form, extra_parts, request=request,
            )

            # encode the StatusAccepted response
            encoder.status_location = async_backend.get_response_url(job_id)
            response = encoder.encode_accepted()

        else:
            # synchronous execution
            if not getattr(process, 'synchronous', True):
                raise InvalidParameterValue(
                    "This process does not allow synchronous execution!",
                    "storeExecuteResponse"
                )

            if resp_form.status:
                raise InvalidParameterValue(
                    "The status update cannot be provided for a synchronous "
                    "execute request!", "status"
                )

            # prepare inputs passed to the process execution subroutine
            inputs = {}
            inputs.update(decode_output_requests(resp_form, output_defs))
            inputs.update(decode_raw_inputs(
                raw_inputs, input_defs, InMemoryURLResolver(extra_parts, logger)
            ))
            if not resp_form.raw:
                encoder.inputs = inputs

            # execute the process
            outputs = process.execute(**inputs)

            # pack the outputs
            packed_outputs = pack_outputs(outputs, resp_form, output_defs)

            # encode the StatusSucceeded response
            response = encoder.encode_response(packed_outputs)

        return encoder.serialize(response)
