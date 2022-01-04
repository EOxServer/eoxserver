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

from ows.wps.v20 import decoders
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

        execute_request: pyows_types.ExecuteRequest = decoders.XMLExecuteDecoder(
            request.body
        ).decode()
        process: ProcessInterface = get_process_by_identifier(
            execute_request.process_id
        )

        inputs = {
            input_.identifier: _input_value(input_) for input_ in execute_request.inputs
        }

        # TODO: tests for all cases
        if execute_request.mode == pyows_types.ExecutionMode.sync:
            logger.debug("Execute process %s", execute_request.process_id)
            response = process.execute(**inputs)
        elif execute_request.mode == pyows_types.ExecutionMode.async_:
            raise OperationNotSupportedError("Async mode not implemented")
        else:  # auto
            raise OperationNotSupportedError("Auto mode not implemented")

        if execute_request.response == pyows_types.ResponseType.raw:
            content_type = None
            # TODO: proper output encoding
            if len(execute_request.output_definitions) == 1:
                content_type = (
                    execute_request.output_definitions[0].mime_type
                    or "text/plain; charset=utf-8"
                )

            return response, content_type, 200
        else:  # document
            raise OperationNotSupportedError("Document mode not implemented")


def _input_value(input_: pyows_types.Input) -> typing.Any:
    if isinstance(input_.data, pyows_types.Data):

        value = input_.data.value


        # TODO: figure out what types can really be used here. judging by the examples it can be a
        #       wild mix of xml tags or just literal data without even a LiteralData tag.
        if isinstance(value, str):
            return value

        elem = value[0]

        # TODO: we need something like eoxserver.services.ows.wps.v10.execute_decoder_xml._parse_input
        #       here. Either generalize this to namespace for 2.0 or implement in pyows (what are the
        #       differences between wps 1.0 and 2.0 here?)
        if elem.tag == "{http://www.opengis.net/wps/2.0}BoundingBoxData":

            # ad hoc reimplementation of _parse_input_bbox to get call to work now
            def parse_corner(corner):
                return [float(x) for x in corner.split(" ")]

            lower_corner = elem.findtext(
                "./{http://www.opengis.net/ows/2.0}LowerCorner"
            )
            upper_corner = elem.findtext(
                "./{http://www.opengis.net/ows/2.0}UpperCorner"
            )
            return (
                parse_corner(lower_corner),
                parse_corner(upper_corner),
                # elem.attrib.get("crs"),  # NOTE: crs seems to be decoded for wps 1.0, but then disappears somewhere
            )
        else:
            return elem
    else:
        # TODO: how do we deal with references?
        raise OperationNotSupportedError("References as input are not implemented")
