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
from typing import List

from eoxserver.services.ows.wps.util import get_processes
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
import ows.wps.types as pyows_types


class WPS20DescribeProcessHandler(object):
    """WPS 2.0 DescribeProcess service handler."""

    service = "WPS"
    versions = ("2.0.0",)
    request = "DescribeProcess"
    methods = ["GET", "POST"]

    @staticmethod
    def get_decoder(request):
        if request.method == "GET":
            return decoders.KVPDescribeProcessDecoder(request.GET)
        else:
            return decoders.XMLDescribeProcessDecoder(request.body)

    def handle(self, request):
        """Handle HTTP request."""

        decoder = self.get_decoder(request)
        request: decoders.DescribeProcessRequest = decoder.decode()

        identifiers = set(request.process_ids)

        used_processes = []
        for process in get_processes():
            process_identifier = (
                getattr(process, "identifier", None) or type(process).__name__
            )
            if process_identifier in identifiers:
                identifiers.remove(process_identifier)
                used_processes.append(process)

        for identifier in identifiers:
            raise NoSuchProcessError(identifier)
            # TODO: add test for this

        process_descriptions: List[pyows_types.ProcessDescription] = [
            encode_proccess_description(process) for process in used_processes
        ]
        result = encoders.xml_encode_process_offerings(process_descriptions)

        return result.value, result.content_type


def encode_proccess_description(
    process: ProcessInterface,
) -> pyows_types.ProcessDescription:
    summary = encode_process_summary(process)
    return pyows_types.ProcessDescription(
        **dataclasses.asdict(summary),
        inputs=[encode_input(fix_parameter(*param)) for param in process.inputs],
        outputs=[encode_output(fix_parameter(*param)) for param in process.outputs],
    )


def encode_input(param) -> pyows_types.InputDescription:
    if isinstance(param, LiteralData):
        return pyows_types.InputDescription(
            identifier=param.identifier,
            data_description=pyows_types.LiteralDataDescription(
                domains=[
                    pyows_types.Domain(
                        data_type=None,  # TODO: there is param.dtype, but this does not translate to pyows types
                        allowed_values=[],  # TODO: there is param.allowed_values, but this doesn't directly translate to pyows types
                        uom=param.uoms,
                        default_value=param.default,
                    )
                ],
                formats=[],  # TODO:
            ),
            title=param.title,
            abstract=param.abstract,
            # TODO: missing parameters, are values available?
        )
    else:
        # TODO: handle other eoxserver data types
        raise NotImplementedError


def encode_output(param) -> pyows_types.OutputDescription:
    if isinstance(param, LiteralData):
        return pyows_types.OutputDescription(
            identifier=param.identifier,
            data_description=pyows_types.LiteralDataDescription(
                # TODO: probably similar to encode_input()
                domains=[],
                formats=[],
            ),
            title=param.title,
            abstract=param.abstract,
        )
