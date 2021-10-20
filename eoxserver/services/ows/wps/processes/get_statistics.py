# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Mussab Abdalla<mussab.abdalla@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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
from eoxserver.contrib import gdal
import numpy as np

from eoxserver.core import Component, implements
# from eoxserver.resources import coverages

from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatJSON, CDObject
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open
from django.db.models import Q

from django.contrib.gis.geos import Polygon
import logging

logger = logging.getLogger(__name__)


class GetStatisticsProcess(Component):
    """ GetStatistics defines a WPS process needed by the EOxC
        DEM implementtation """

    def __init__(self):
        super(GetStatisticsProcess, self).__init__()

    implements(ProcessInterface)

    identifier = "GetStatistics"
    title = "Get statistics for a coverage/s that intersects with the input bbox"
    description = ("provides statistics of all the coverages whithin a provided bounding box. "
                  " The process is used by the  by the EOxC DEM implementtation")
    metadata = {}
    profiles = ['EOxServer:GetStatistics']

    inputs = {
        "bbox": LiteralData(
            "bbox",
            title="bounding box that intersect with the products."
        ),
    }

    outputs = {
        "statistic": ComplexData(
            "statistic",
            title="output statistics",
            abstract="coverage/s statistics in json format.",
            formats=FormatJSON()
        ),
    }

    @staticmethod
    def execute(bbox, **kwarg):
        """ The main execution function for the process.
        """

        values = list(map(float, bbox.split(",")))
        if len(values) != 4:
            raise ValueError("Invalid number of coordinates in 'bbox'.")

        parsed_bbox = Polygon.from_bbox(values)

        # get the dataset series intersecting with the requested bbox

        coverages = models.Coverage.objects.filter(
            Q(footprint__intersects=parsed_bbox)
            | Q(footprint__isnull=True, parent_product__footprint__intersects=parsed_bbox))

        report = {}
        for index, coverage in enumerate(coverages):

            try:
                data_items = coverage.arraydata_items.all()

            except coverage.arraydata_items.all().length > 1:
                raise InvalidInputValueError(
                    "coverage", "coverage '%s' has more than one imagery, this process handles single images!" % coverage
                )

            data_item = data_items[0]

            ds = gdal_open(data_item, False)

            band = ds.GetRasterBand(1)
            image_array = band.ReadAsArray()
            stats = ds.GetRasterBand(1).GetStatistics(0, 1)
            bin_array, hist = np.histogram(image_array, bins=np.arange(int(stats[0]), int(stats[1]), 20, int))

            # nodata = band.GetNoDataValue()
            # no_value = np.where(np.any(image_array==nodata, axis=1))

            id_key = "Coverage_%s" % str(index + 1)
            coverage_id = coverage.identifier

            stats_json = {
                "id": coverage_id,
                "MINIMUM": stats[0],
                "MAXIMUM": stats[1],
                "MEAN": stats[2],
                "STDDEV": stats[3],
                "HISTOGRAM_FREQUENCY": bin_array.tolist(),
                "HISTOGRAM_PIXEL_VALUES": hist.tolist(),
                # "NUMBER_OF_NODATA_PIXELS": no_value[0].size
                }
            report[id_key] = stats_json

        _output = CDObject(
            report, format=FormatJSON(),
            filename=("identity_complex.json")
        )

        return _output
