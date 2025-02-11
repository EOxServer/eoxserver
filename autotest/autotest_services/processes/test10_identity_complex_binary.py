#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2025 EOX IT Services GmbH
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
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    ComplexData, CDObject, FormatBinaryBase64, FormatBinaryRaw,
)


class TestProcess10(Component):
    """ Test identity process (the outputs are copies of the inputs)
    demonstrating various features of the binary complex data inputs and outputs.
    """
    implements(ProcessInterface)

    identifier = "TC10:identity:complex:binary"
    title = "Test Case 10: Binary complex data identity."
    metadata = {"test-metadata": "http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("input_", ComplexData(
            'TC10:input', title="Test case #10: Complex input #00",
            abstract="Binary complex data input.",
            formats=[
                FormatBinaryBase64("application/octet-stream"),
                #FormatBinaryRaw("application/octet-stream"),
            ],
        )),
    ]

    outputs = [
        ("output", ComplexData(
            'TC10:output', title="Test case #10: Binary complex output #00",
            abstract="Binary complex data output (copy of the input).",
            formats=[
                FormatBinaryBase64("application/octet-stream"),
                FormatBinaryRaw("application/octet-stream"),
            ],
        )),
    ]

    @staticmethod
    def execute(input_, output, **kwarg):
        """ WPS Process execute handler. """

        return CDObject(input_, filename="data.bin", **output)
