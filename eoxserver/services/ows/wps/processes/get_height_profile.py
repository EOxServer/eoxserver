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

from uuid import uuid4

from datetime import datetime
from math import radians, cos, sin, asin, sqrt

from eoxserver.contrib import gdal

from eoxserver.core import Component, implements

from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatText
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open



class GetHeightProfileProcess(Component):
    """ GetHeightProfileProcess defines a WPS process needed by the EOxC
        DEM implementtation """

    implements(ProcessInterface)

    identifier = "GetHeightProfile"
    title = "Get the hight profile for a coverage"
    description = ("provides a height profile between 2 points within a product "
                  " The process is used by the  by the EOxC DEM implementtation")
    metadata = {}
    profiles = ['EOxServer:GetHeightProfile']

    inputs = {
        "product": LiteralData(
            "product",
            title="Product identifier."),
        "line": ComplexData(
            "line",
            datetime,
            title="horizontal axis of the height profile."
        ),
        "output_format": LiteralData(
            "format",
            optional=True,
            title="Optional end of the time interval."
        ),
        "interpolation_method": LiteralData(
            "collection",
            title="Collection name (a.k.a. dataset-series identifier)."),
    }

    outputs = {
        "times": ComplexData(
            "times",
            formats=(FormatText('text/csv'), FormatText('text/plain')),
            title=(
                "Comma separated list of collection's coverages, "
                "their extents and times."
            ),
            abstract=(
                "NOTE: The use of the 'text/plain' format is "
                "deprecated! This format will be removed!'"
            )
        )
    }

    def haversine(lon1, lat1, lon2, lat2):
        """
        Calculate the great circle distance between two points
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6378137.0
        return c * r

    @staticmethod
    def execute(self, product, line, interval, output_format, interpolation_method, **kwarg):
        """ The main execution function for the process.
        """

        # get the dataset series matching the requested ID
        try:
            model = models.EOObject.objects.filter(
                identifier=product
            ).select_subclasses().get()

        except models.EOObject.DoesNotExist:
            raise InvalidInputValueError(
                "product", "Invalid product name '%s'!" % product
            )
        try:

            data_items = model.arraydata_items.all()

        except data_items.length > 1:
            raise InvalidInputValueError(
                "product", "product '%s' has more than one imagery, the profile process handles single images!" % product
            )
        data_item = data_items[0]
        ds = gdal_open(data_item, False)

        proj_str = "+proj=tpeqd +lon_1={} +lat_1={} +lon_2={} +lat_2={}".format(line[0], line[1], line[2], line[3])

        line_distance = self.haversine(line[0], line[1], line[2], line[3])

        bbox = ((-1 * line_distance / 2), (100*0.5), line_distance / 2, -(100*0.5))

        # Calculate the number of samples in our profile.
        num_samples = int(line_distance / interval)

        tmp_name = '/vsimem/%s' % uuid4().hex

        profile = gdal.Warp(tmp_name, ds, dstSRS=proj_str, outputBounds=bbox,
                        height=1, width=num_samples, resampleAlg=interpolation_method,
                        format=output_format)

        array_out = profile.GetRasterBand(1).ReadAsArray()

        # TODO: return the output as a csv or as png plot using matpoltlib

        # with open('out.csv', 'w') as f:
        #     f.write("dist,value\n")
        #     for (d, value) in enumerate(array_out[0, :]):
        #         f.write("{},{}\n".format(d*interval, value))

        gdal.Unlink(tmp_name)

        return array_out
