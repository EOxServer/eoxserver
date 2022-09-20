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

from datetime import datetime
import operator

from osgeo import ogr

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

    SCL_LAYER_CLOUD_MEDIUM_PROBABILITY = 8
    SCL_LAYER_CLOUD_HIGH_PROBABILITY = 9
    SCL_LAYER_THIN_CIRRUS = 10

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

        geometry = "MULTIPOLYGON (((69.1714578 80.1407449, 69.1714578 80.1333736, 69.2069740 80.1333736, 69.2069740 80.1407449, 69.1714578 80.1407449)))"

        coverages = models.Coverage.objects.filter(
            # parent_product_id=??,
            begin_time__lte=end_time,
            end_time__gte=begin_time,
            footprint__intersects=geometry,
        )

        ogr_geometry = ogr.CreateGeometryFromWkt(geometry)

        cloud_coverage_ratios = {
            coverage: cloud_coverage_ratio_in_geometry(
                coverage.arraydata_items.get(
                    field_index=0,  # TODO: how to get SCL band?
                ),
                ogr_geometry=ogr_geometry,
            )
            for coverage in coverages
        }
        # ds = gdal_open(coverages[0].arraydata_items.get())

        result = {
            "result": [
                # TODO: how to derive date from coverage/band?
                {coverage.identifier: cloud_cover_ratio}
                for coverage, cloud_cover_ratio in sorted(
                    cloud_coverage_ratios.items(),
                    key=operator.itemgetter(1),
                )
            ]
        }
        return CDObject(
            result,
            format=FormatJSON(),
            filename=("cloud_coverage.json"),
        )


def cloud_coverage_ratio_in_geometry(
    data_item: models.ArrayDataItem,
    ogr_geometry: ogr.Geometry,
) -> float:
    dataset = gdal_open(data_item)
    histogram = dataset.GetRasterBand(1).GetHistogram()

    # TODO: reduce dataset to geometry

    num_cloud = sum(
        histogram[scl_value]
        for scl_value in [
            CloudCoverageProcess.SCL_LAYER_CLOUD_MEDIUM_PROBABILITY,
            CloudCoverageProcess.SCL_LAYER_CLOUD_HIGH_PROBABILITY,
            CloudCoverageProcess.SCL_LAYER_THIN_CIRRUS,
        ]
    )

    # TODO: this won't work for arbitrary geometry
    num_pixels = dataset.RasterXSize * dataset.RasterYSize

    return num_cloud / num_pixels
