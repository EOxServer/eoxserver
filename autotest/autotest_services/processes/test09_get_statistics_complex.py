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

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    ComplexData,
    FormatJSON,
    CDObject,
    BoundingBoxData,
)


class Test09GetStatisticsComplex(Component):
    """Test processes mimicking real world get statistics with complex output"""

    implements(ProcessInterface)

    identifier = "TC:GetStatisticsComplex"
    title = "TC09: Test Case GetStatistics Complex"

    inputs = [
        (
            "bbox",
            BoundingBoxData(
                "TC08:bbox",
            ),
        ),
    ]

    outputs = {
        "statistics": ComplexData(
            "statistics",
            title="output statistics",
            abstract="coverage/s statistics in json format.",
            formats=FormatJSON(),
        ),
    }

    def execute(self, bbox, collection):
        return CDObject(
            {"data": 5},
            format=FormatJSON(),
            filename="foo.json",
        )
