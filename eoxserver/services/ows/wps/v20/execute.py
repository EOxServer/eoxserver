# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
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
# -------------------------------------------------------------------------------

import typing
from logging import getLogger

from eoxserver.services.ows.wps.util import get_process_by_identifier
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.exceptions import OperationNotSupportedError
from eoxserver.services.ows.wps.parameters import BoundingBox, ResponseForm

from eoxserver.services.ows.wps.v10.execute_util import (
    pack_outputs as pack_outputs_v10,
    parse_params as parse_params_v10,
    decode_output_requests as decode_output_requests_v10,
)
from eoxserver.services.ows.wps.v10.encoders import WPS10ExecuteResponseRawEncoder

from ows.wps.v20 import decoders
import ows.wps.v20.types as pyows_types
import ows.common.types as pyows_common_types


class WPS20ExecuteHandler(object):
    """WPS 2.0 DescribeProcess service handler."""

    service = "WPS"
    versions = ("2.0.0",)
    request = "Execute"
    methods = ["POST"]

    def handle(self, request):
        """Handle HTTP request."""
        logger = getLogger(__name__)

        execute_request: pyows_types.ExecuteRequest = decoders.XMLExecuteDecoder(
            request.body
        ).decode()
        process: ProcessInterface = get_process_by_identifier(
            execute_request.process_id
        )

        input_defs = parse_params_v10(process.inputs)
        output_defs = parse_params_v10(process.outputs)

        # reuse wps 1.0 encoding
        resp_form = ResponseForm()
        for output in execute_request.output_definitions:
            resp_form.set_output(output)
            # these fields are not present in pyows, we set them for compatibility
            output.uom = None
            output.as_reference = None

        inputs = {
            name: getattr(optional_input, "default", None)
            for (name, optional_input) in input_defs.values()
            if optional_input.is_optional
        }
        inputs.update(decode_output_requests_v10(resp_form, output_defs))
        inputs.update(
            {
                input_.identifier: _input_value(input_)
                for input_ in execute_request.inputs
            }
        )

        if execute_request.mode == pyows_types.ExecutionMode.sync:
            logger.debug("Execute process %s", execute_request.process_id)
            outputs = process.execute(**inputs)
        elif execute_request.mode == pyows_types.ExecutionMode.async_:
            raise OperationNotSupportedError("Async mode not implemented")
        else:  # auto
            raise OperationNotSupportedError("Auto mode not implemented")

        if execute_request.response == pyows_types.ResponseType.raw:
            packed_outputs = pack_outputs_v10(
                outputs,
                response_form=resp_form,
                output_defs=output_defs,
            )
            encoder = WPS10ExecuteResponseRawEncoder(resp_form=resp_form)
            response = encoder.encode_response(packed_outputs)
            return encoder.serialize(response)

        else:  # document
            raise OperationNotSupportedError("Document mode not implemented")


def _input_value(input_: pyows_types.Input) -> typing.Any:
    if isinstance(input_.data, pyows_types.Data):

        data_value = input_.data.value

        # TODO: use pattern matching as soon as we can require python 3.10
        if isinstance(data_value, pyows_types.LiteralValue):
            return data_value.value
        elif isinstance(data_value, pyows_common_types.BoundingBox):
            return BoundingBox(
                bbox=(data_value.bbox[:2], data_value.bbox[2:]),
                crs=data_value.crs,
            )
        else:
            raise OperationNotSupportedError("Unsupported input element")
    else:
        raise OperationNotSupportedError("References as input are not implemented")
