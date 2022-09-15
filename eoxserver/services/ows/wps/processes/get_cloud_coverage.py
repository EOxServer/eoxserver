# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2022 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

import json
from datetime import datetime

from eoxserver.core import Component
from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open
from eoxserver.services.ows.wps.parameters import (
    LiteralData,
    ComplexData,
    FormatJSON,
    CDObject,
)
import logging

logger = logging.getLogger(__name__)


class CloudCoverageProcess(Component):

    identifier = "CloudCoverage"
    title = "Cloud coverage information about images of an AOI/TOI"
    description = ""
    metadata = {}
    profiles = ["EOxServer:CloudCoverage"]

    inputs = {
        "begin_time": LiteralData(
            "begin_time",
            datetime,
            title="Start of the time interval.",
        ),
        "end_time": LiteralData(
            "end_time",
            datetime,
            title="End of the time interval.",
        ),
        "product": LiteralData(
            "product",
            title="Product identifier",
        ),
        "geometry": LiteralData(
            "geometry",
            title="Geometry",
        ),
    }

    outputs = {
        "result": ComplexData(
            "result",
            title="output data",
            abstract="Information about cloud coverage",
            formats=(FormatJSON(),),
        ),
    }

    @staticmethod
    def execute(
        begin_time,
        end_time,
        product,
        geometry,
        result,
    ):
        # TODO: product, there are none in the test db

        # TODO: geometry parameter currently can't be passed in https://eox.slack.com/archives/C02LX7L04NQ/p1663149294544739
        qs = models.Coverage.objects.filter(
            #parent_product_id=??,
            begin_time__lte=end_time,
            end_time__gte=begin_time,
            #footprint__intersects=geometry,
        )

        for coverage in qs:

            data_items = coverage.arraydata_items.all()

            for data_item in data_items:
                dataset = gdal_open(data_item)
                breakpoint()
                print(dataset)

        result = {"result": [{"a": "b"}]}
        return CDObject(
            result,
            format=FormatJSON(),
            filename=("cloud_coverage.json"),
        )
