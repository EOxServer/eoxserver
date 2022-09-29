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
from uuid import uuid4

from osgeo import ogr, osr

from eoxserver.core import Component
from eoxserver.contrib import gdal
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
        # https://github.com/EOxServer/pyows/issues/5

        geometry = "MULTIPOLYGON (((69.1714578 80.1407449, 69.1714578 80.1333736, 69.2069740 80.1333736, 69.2069740 80.1407449, 69.1714578 80.1407449)))"
        # geometry = "MULTIPOLYGON (((69.1714578 80.1387449, 69.1714578 80.1333736, 69.1969740 80.1333736, 69.1714578 80.1387449)))"
        # geometry = "MULTIPOLYGON (((69.1904578 80.1407449, 69.1904578 80.1333736, 69.2069740 80.1333736, 69.2069740 80.1407449, 69.1904578 80.1407449)))"
        # geometry = "MULTIPOLYGON (((69.1714578 80.1407449, 69.2069740 80.1333736, 69.2069740 80.1407449, 69.1714578 80.1407449)))"

        coverages = models.Coverage.objects.filter(
            # parent_product_id=??,
            begin_time__lte=end_time,
            end_time__gte=begin_time,
            footprint__intersects=geometry,
        )

        geometry_mem_path = f"/vsimem/{uuid4()}.shp"

        _create_geometry_feature_in_memory(
            wkt_geometry=geometry,
            memory_path=geometry_mem_path,
        )

        cloud_coverage_ratios = {
            coverage: cloud_coverage_ratio_in_geometry(
                coverage.arraydata_items.get(
                    field_index=0,  # TODO: how to get SCL band?
                ),
                geometry_mem_path=geometry_mem_path,
            )
            for coverage in coverages
        }

        gdal.Unlink(geometry_mem_path)

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
    geometry_mem_path: str,
) -> float:
    tmp_ds = f"/vsimem/{uuid4()}.tif"
    original_ds = gdal_open(data_item)
    result_ds = gdal.Warp(
        tmp_ds,
        original_ds,
        # TODO: ideally only cut relevant band. possibly retrieve
        #       single band and only bbox with with gdal_translate
        options=gdal.WarpOptions(
            cutlineDSName=geometry_mem_path,
            cropToCutline=True,
        ),
    )

    # NOTE: using histogram is safe because it defaults to a bin distribution
    # which captures integers
    histogram = result_ds.GetRasterBand(1).GetHistogram(
        approx_ok=False,
        include_out_of_range=True,
    )

    num_cloud = sum(
        histogram[scl_value]
        for scl_value in [
            CloudCoverageProcess.SCL_LAYER_CLOUD_MEDIUM_PROBABILITY,
            CloudCoverageProcess.SCL_LAYER_CLOUD_HIGH_PROBABILITY,
            CloudCoverageProcess.SCL_LAYER_THIN_CIRRUS,
        ]
    )

    num_pixels = sum(histogram)
    cloud_coverage_ratio = num_cloud / num_pixels

    gdal.Unlink(tmp_ds)

    return cloud_coverage_ratio


def _create_geometry_feature_in_memory(wkt_geometry: str, memory_path: str) -> None:

    ogr_geometry = ogr.CreateGeometryFromWkt(wkt_geometry)

    drv = ogr.GetDriverByName("ESRI Shapefile")

    feature_ds = drv.CreateDataSource(memory_path)

    srs = osr.SpatialReference()
    # TODO: always this value?
    srs.ImportFromEPSG(4326)
    feature_layer = feature_ds.CreateLayer("layer", srs, geom_type=ogr.wkbPolygon)

    featureDefnHeaders = feature_layer.GetLayerDefn()

    outFeature = ogr.Feature(featureDefnHeaders)

    outFeature.SetGeometry(ogr_geometry)

    feature_layer.CreateFeature(outFeature)

    feature_ds.FlushCache()
