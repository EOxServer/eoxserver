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

import contextlib
import concurrent
import functools
from datetime import datetime
import json
from uuid import uuid4
from typing import List, Callable, Optional, Any

from osgeo import ogr, osr

from eoxserver.core import Component
from eoxserver.contrib import gdal
from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError
from eoxserver.services.ows.wps.parameters import (
    LiteralData,
    ComplexData,
    FormatJSON,
    FormatText,
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
        "geometry": ComplexData(
            "geometry",
            title="Geometry",
            formats=[FormatText()],
        ),
        "cloud_mask": ComplexData(
            "cloud_mask",
            optional=True,
            title="Values of data which are interpreted as cloud",
            formats=[FormatJSON()],
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

    SCL_LAYER_NO_DATA = 0
    SCL_LAYER_CLOUD_MEDIUM_PROBABILITY = 8
    SCL_LAYER_CLOUD_HIGH_PROBABILITY = 9
    SCL_LAYER_THIN_CIRRUS = 10
    SCL_LAYER_SATURATED_OR_DEFECTIVE = 1

    DEFAULT_SCL_CLOUD_MASK = [
        SCL_LAYER_CLOUD_MEDIUM_PROBABILITY,
        SCL_LAYER_CLOUD_HIGH_PROBABILITY,
        SCL_LAYER_THIN_CIRRUS,
        SCL_LAYER_SATURATED_OR_DEFECTIVE,
    ]

    # https://labo.obs-mip.fr/multitemp/sentinel-2/majas-native-sentinel-2-format/#English
    # anything nonzero should be cloud, however that includes also cloud shadows which
    # have a lot of false positives (or shadows that are not visible to the naked eye)
    # for now only use the upper 4 bits which are:
    # bit 4 (16) : clouds detected via mono-temporal thresholds
    # bit 5 (32) : clouds detected via multi-temporal thresholds
    # bit 6 (64) : thinnest clouds
    # bit 7 (128) : high clouds detected by 1.38 µm
    # sometimes bit 4 also seems to count things as cloud which don't appear to
    # be clouds
    CLM_MASK_ONLY_CLOUD = 0b11110000

    @staticmethod
    def execute(
        begin_time,
        end_time,
        geometry,
        cloud_mask,
        result,
    ):
        wkt_geometry = geometry[0].text

        if cloud_mask:
            # NOTE: cloud mask could be list or integer bitmask based on type,
            #       so just accept json
            try:
                cloud_mask = json.loads(cloud_mask[0].text)
            except ValueError:
                raise InvalidInputValueError("cloud_mask", "Invalid cloud mask value")

        # TODO Use queue object for more complex query if parent_product__footprint is not enough
        relevant_coverages = models.Coverage.objects.filter(
            parent_product__begin_time__lte=end_time,
            parent_product__end_time__gte=begin_time,
            parent_product__footprint__intersects=wkt_geometry,
        ).order_by("parent_product__begin_time")

        if coverages_clm := relevant_coverages.filter(coverage_type__name="CLM"):
            logger.info("Matched %s CLM covs for cloud coverage", coverages_clm.count())
            calculation_fun = cloud_coverage_ratio_for_CLM
            coverages = coverages_clm
            # CLM is a bitmask, this value would mean that all types of cloud were found
            # hopefully this never occurs naturally, so we can use it as no_data
            no_data_value = 0b11111111

        elif coverages_scl := relevant_coverages.filter(coverage_type__name="SCL"):
            logger.info("Matched %s SCL covs for cloud coverage", coverages_scl.count())
            calculation_fun = cloud_coverage_ratio_for_SCL
            coverages = coverages_scl
            no_data_value = None

        else:
            calculation_fun = None
            coverages = []
            no_data_value = None

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as e:
            cloud_coverage_ratios = e.map(
                functools.partial(
                    cloud_coverage_ratio_in_geometry,
                    calculation_fun=calculation_fun,
                    wkt_geometry=wkt_geometry,
                    no_data_value=no_data_value,
                    cloud_mask=cloud_mask,
                ),
                [coverage.arraydata_items.get() for coverage in coverages],
            )

        result = {
            "result": {
                coverage.parent_product.begin_time.isoformat(): cloud_cover_ratio
                for coverage, cloud_cover_ratio in zip(coverages, cloud_coverage_ratios)
            }
        }
        return CDObject(
            result,
            format=FormatJSON(),
            filename=("cloud_coverage.json"),
        )


def cloud_coverage_ratio_in_geometry(
    data_item: models.ArrayDataItem,
    wkt_geometry: str,
    calculation_fun: Callable[[List[int], Any], float],
    no_data_value: Optional[int],
    cloud_mask: Any,
) -> float:
    histogram = _histogram_in_geometry(
        data_item=data_item,
        wkt_geometry=wkt_geometry,
        no_data_value=no_data_value,
    )
    return calculation_fun(histogram, cloud_mask)


def cloud_coverage_ratio_for_CLM(histogram: List[int], cloud_mask: Any) -> float:
    cloud_mask = (
        cloud_mask
        if cloud_mask is not None
        else CloudCoverageProcess.CLM_MASK_ONLY_CLOUD
    )
    num_is_cloud = sum(
        value for index, value in enumerate(histogram) if index & cloud_mask > 0
    )

    num_pixels = sum(histogram)
    return ((num_is_cloud / num_pixels)) if num_pixels != 0 else 0.0


def cloud_coverage_ratio_for_SCL(histogram: List[int], cloud_mask: Any) -> float:
    cloud_mask = (
        cloud_mask
        if cloud_mask is not None
        else CloudCoverageProcess.DEFAULT_SCL_CLOUD_MASK
    )
    num_cloud = sum(histogram[scl_value] for scl_value in cloud_mask)

    num_no_data = histogram[CloudCoverageProcess.SCL_LAYER_NO_DATA]

    num_pixels = sum(histogram) - num_no_data

    return num_cloud / num_pixels if num_pixels != 0 else 0.0


def _histogram_in_geometry(
    data_item: models.ArrayDataItem,
    wkt_geometry: str,
    no_data_value: Optional[int],
) -> List[int]:
    # NOTE: this is executed in threads, but all gdal operations are contained
    #       in here, so each thread has separate gdal data

    tmp_ds = f"/vsimem/{uuid4()}.tif"
    original_ds = gdal_open(data_item)

    with _create_geometry_feature_in_memory(wkt_geometry) as geometry_mem_path:
        result_ds = gdal.Warp(
            tmp_ds,
            original_ds,
            # TODO: ideally only cut relevant band. possibly retrieve
            #       single band and only bbox with with gdal_translate
            options=gdal.WarpOptions(
                cutlineDSName=geometry_mem_path,
                cropToCutline=True,
                warpOptions=["CUTLINE_ALL_TOUCHED=TRUE"],
                dstNodata=no_data_value,
            ),
        )

    # NOTE: using histogram is safe because it defaults to a bin distribution
    # which captures integers
    histogram = result_ds.GetRasterBand(1).GetHistogram(
        approx_ok=False,
        include_out_of_range=True,
    )

    gdal.Unlink(tmp_ds)

    return histogram


@contextlib.contextmanager
def _create_geometry_feature_in_memory(wkt_geometry: str):
    memory_path = f"/vsimem/{uuid4()}.shp"

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

    yield memory_path

    drv.DeleteDataSource(memory_path)
