# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Mussab Abdalla<mussab.abdalla@eox.at>
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

from uuid import uuid4
import numpy as np

from eoxserver.core import Component

from eoxserver.contrib import gdal

from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatJSON, CDObject, BoundingBoxData
)

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open
from django.db.models import Q, F

from django.contrib.gis.geos import Polygon
import logging

logger = logging.getLogger(__name__)


class GetStatisticsProcess(Component):
    """ GetStatistics defines a WPS process for Raster image Statistics
        retrieval"""

    identifier = "GetStatistics"
    title = "Get statistics for a coverage/s that intersects with the input bbox"
    description = ("provides statistics of all the coverages whithin a provided bounding box.")
    metadata = {}
    profiles = ['EOxServer:GetStatistics']

    inputs = {
        "bbox": BoundingBoxData(
            "bbox",
            title="bounding box that intersect with the products."
        ),
        "collection": LiteralData(
            "collection",
            title="The Identifier of the collection of intrest."
        ),
    }

    outputs = {
        "statistics": ComplexData(
            "statistics",
            title="output statistics",
            abstract="coverage/s statistics in json format.",
            formats=FormatJSON()
        ),
    }

    @staticmethod
    def execute(bbox, collection, **kwarg):
        """ The main execution function for the process.
        """

        np_bbox = np.array(bbox)
        flattened_bbox = np_bbox.flatten()
        values = flattened_bbox.tolist()

        parsed_bbox = Polygon.from_bbox(values)

        # get the dataset series intersecting with the requested bbox
        collection = models.Collection.objects.get(identifier=collection)

        coverages = models.Coverage.objects.filter(
                (
                    Q(collections=collection)
                    | Q(parent_product__collections=collection)
                ) &
                (
                    Q(footprint__intersects=parsed_bbox)
                    | Q(footprint__isnull=True, parent_product__footprint__intersects=parsed_bbox)
                )
            )

        report = {
            "result": []}
        for coverage in coverages:

            coverage_id = coverage.identifier
            coverage_type = coverage.coverage_type
            fields = coverage_type.field_types.all()
            stats_json = {
                "id": coverage_id,
                "bands": []
            }

            for field_idx, field in enumerate(fields):
                nill_values = [float(item['value']) for item in field.nil_values.values('value')]
                array_data_item = coverage.arraydata_items.get(
                    field_index__lte=field_idx,
                    field_index__gt=field_idx - F('band_count')
                            )

                ds = gdal_open(array_data_item, False)
                geoTransform = ds.GetGeoTransform()
                minx = geoTransform[0]
                maxy = geoTransform[3]
                maxx = minx + geoTransform[1] * ds.RasterXSize
                miny = maxy + geoTransform[5] * ds.RasterYSize
                coverage_bbox = Polygon.from_bbox((minx, miny, maxx, maxy))

                if not parsed_bbox.contains(coverage_bbox):
                    values_bbox = coverage_bbox.intersection(parsed_bbox)
                    if round(values_bbox.area, 2) > 0:
                        values = list(values_bbox.extent)
                    else:
                        logger.error('The provided bbox is not inside or intersecting with the coverage')
                        continue

                    tmp_ds = '/vsimem/%s.tif' % uuid4().hex
                    ds = gdal.Warp(tmp_ds, ds, dstSRS=ds.GetProjection(), outputBounds=values, format='Gtiff')
                    gdal.Unlink(tmp_ds)

                band_number = array_data_item.field_index - field_idx + 1

                band = ds.GetRasterBand(band_number)
                image_array = band.ReadAsArray()
                data_array = image_array
                no_data_list = []
                for no_data in nill_values:
                    no_data_list.append(np.sum(image_array == no_data))
                    data_array = data_array[data_array != no_data]
                # if the image is empty GetStatistics will throw an error
                # so we check if the number of the image pixels is greater
                # than the number of noData pixels
                nodata_number = sum(no_data_list).item()
                if ((image_array.size - nodata_number) > 0):
                    stats = ds.GetRasterBand(band_number).GetStatistics(0, 1)
                    interval = (np.amax(data_array) - np.amin(data_array)) / 25

                    bin_array, hist = np.histogram(data_array, bins=np.arange(
                        int(stats[0]), int(stats[1]), interval, int))

                    band_data = {
                        "BAND_ID": band_number,
                        "MINIMUM": stats[0],
                        "MAXIMUM": stats[1],
                        "MEAN": stats[2],
                        "STDDEV": stats[3],
                        "HISTOGRAM_FREQUENCY": bin_array.tolist(),
                        "HISTOGRAM_PIXEL_VALUES": hist.tolist(),
                        "NUMBER_OF_NODATA_PIXELS": nodata_number
                        }
                    stats_json["bands"].append(band_data)

            if len(stats_json["bands"]) >= 1:
                report["result"].append(stats_json)

        _output = CDObject(
            report, format=FormatJSON(),
            filename=("identity_complex.json")
        )

        return _output
