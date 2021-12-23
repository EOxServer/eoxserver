# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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

import dataclasses
import typing
from logging import getLogger

from eoxserver.services.ows.wps.util import get_process_by_identifier
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.exceptions import NoSuchProcessError
from eoxserver.services.ows.wps.v20.common import encode_process_summary
from eoxserver.services.ows.wps.parameters import (
    fix_parameter,
    LiteralData,
    ComplexData,
    BoundingBoxData,
)

from ows.wps.v20 import encoders, decoders
import ows.wps.v20.types as pyows_types


class WPS20ExecuteHandler(object):
    """WPS 2.0 DescribeProcess service handler."""

    service = "WPS"
    versions = ("2.0.0",)
    request = "Execute"
    methods = ["POST"]


    def handle(self, request):
        """Handle HTTP request."""
        logger = getLogger(__name__)

        request: pyows_types.ExecuteRequest = decoders.XMLExecuteDecoder(request.body).decode()
        process: ProcessInterface = get_process_by_identifier(request.process_id)

        inputs = {
            input_.identifier: _input_value(input_) for input_ in request.inputs
        }

        # TODO: tests for all cases
        if request.mode == pyows_types.ExecutionMode.sync:
            logger.debug("Execute process %s", request.process_id)
            response = process.execute(**inputs)
        elif request.mode == pyows_types.ExecutionMode.async_:
            ...
        else:  # auto
            ...

        if request.response == pyows_types.ResponseType.raw:
            return response, "", 200  # TODO: content type?
        else:  # document
            ...  # TODO: implement in pyows?

        # TODO:
        request.output_definitions



def _input_value(input_: pyows_types.Input) -> typing.Any:
    if isinstance(input_.data, pyows_types.Data):
        return input_.data.value
    else:
        # TODO: how do we deal with references?
        raise NotImplementedError
