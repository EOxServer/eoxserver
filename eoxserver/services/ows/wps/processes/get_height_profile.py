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

import csv
from uuid import uuid4

from math import radians, cos, sin, asin, sqrt

import numpy as np
import matplotlib.pyplot as plt

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from eoxserver.contrib import gdal

from eoxserver.core import Component

from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatText, CDAsciiTextBuffer,
    CDByteBuffer, FormatBinaryRaw, FormatBinaryBase64,
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = [radians(v) for v in [lon1, lat1, lon2, lat2]]

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6378137.0
    return c * r


class GetHeightProfileProcess(Component):
    """ GetHeightProfileProcess defines a WPS process for getting Height
        Profile information """

    identifier = "GetHeightProfile"
    title = "Get the hight profile for a coverage"
    description = ("provides a height profile between 2 points within a coverage.")
    metadata = {}
    profiles = ['EOxServer:GetHeightProfile']

    inputs = {
        "coverage": LiteralData(
            "coverage",
            title="coverage identifier."),
        "line": LiteralData(
            "line",
            title="horizontal axis of the height profile."
        ),
        "method": LiteralData(
            "method",
            title="Interpolation method (a.k.a. near, avarage ... etc)."),
        "interval": LiteralData(
            "interval",
            optional=True,
            title="Distance interval."
        ),
    }

    outputs = {
        "profile": ComplexData(
            "profile",
            title="output image data",
            abstract="Binary complex data output.",
            formats=(
                FormatBinaryRaw('image/png'),
                FormatBinaryBase64('image/png'),
                FormatBinaryRaw('image/jpeg'),
                FormatBinaryBase64('image/jpeg'),
                FormatBinaryRaw('image/tiff'),
                FormatBinaryBase64('image/tiff'),
                FormatText('text/csv'),
                FormatText('text/plain')
            )
        ),
    }


    @staticmethod
    def execute(coverage, line, interval, method, profile, **kwarg):
        """ The main execution function for the process.
        """

        if isinstance(line, str):
            line = eval(line)

        line_distance = haversine(line[0], line[1], line[2], line[3])

        # get the dataset series matching the requested ID
        try:
            model = models.Coverage.objects.get(
                identifier=coverage)

            product = models.Product.objects.get(id=model.parent_product_id)


        except models.Coverage.DoesNotExist:
            raise InvalidInputValueError(
                "coverage", "Invalid coverage name '%s'!" % coverage
            )
        try:

            data_items = model.arraydata_items.all()

        except model.arraydata_items.all().length > 1:
            raise InvalidInputValueError(
                "coverage", "coverage '%s' has more than one imagery, the profile process handles single images!" % coverage
            )

        data_item = data_items[0]
        ds = gdal_open(data_item, False)

        proj_wkt = 'PROJCS["unknown",GEOGCS["unknown",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Two_Point_Equidistant"],PARAMETER["Latitude_Of_1st_Point",{}],PARAMETER["Longitude_Of_1st_Point",{}],PARAMETER["Latitude_Of_2nd_Point",{}],PARAMETER["Longitude_Of_2nd_Point",{}],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1,AUTHORITY["EPSG","9001"]],AXIS["Easting",EAST],AXIS["Northing",NORTH]]'.format(line[1], line[0], line[3], line[2])

        bbox = ((-1 * line_distance / 2), (100*0.5), line_distance / 2, -(100*0.5))
        interval = int(interval)

        # # Calculate the number of samples in the profile.
        num_samples = int(line_distance / interval)

        tmp_ds = '/vsimem/%s' % uuid4().hex

        profile_ds = gdal.Warp(tmp_ds, ds, dstSRS=proj_wkt, outputBounds=bbox,
                        height=1, width=num_samples, resampleAlg=method,
                        format='Gtiff')

        array_out = profile_ds.GetRasterBand(1).ReadAsArray()

        y = array_out[0].tolist()

        x = np.arange(0, (num_samples * interval)/1000, interval/1000)

        if (profile['mime_type'] == "text/csv"):
            _output = CDAsciiTextBuffer()
            if getattr(_output, 'mime_type', None) is None:
                setattr(_output, 'mime_type', 'text/csv')

            writer = csv.writer(_output, quoting=csv.QUOTE_ALL)
            header = ["distance", "elevation"]
            writer.writerow(header)

            for (d, value) in enumerate(array_out[0, :]):
                writer.writerow([
                    d * interval,
                    value
                ])

        else:
            if profile['mime_type'] == "image/png":
                extension = "png"

            elif profile['mime_type'] == "image/jpeg":
                extension = "jpg"

            elif profile['mime_type'] == "image/tiff":
                extension = "tif"

            output_filename = 'height_profile.%s' % extension
            fig = plt.figure()
            plt.plot(x, y)
            title = "Height Profile \n Product: %s \n " % product.identifier
            plt.title(title + "start coordinates: (%s, %s), end coordinates: (%s, %s)"
                      % tuple("{:7.4f}".format(point) for point in line),
                      fontsize=10)
            plt.xlabel("Distance (Km)")
            plt.ylabel("Elevation (m)")
            plt.grid(color='green', linestyle='--', linewidth=0.5)

            image_data = BytesIO()
            fig.savefig(image_data, format=extension)
            image_data.seek(0)

            _output = CDByteBuffer(
                    image_data.read(), filename=output_filename,)
            if getattr(_output, 'mime_type', None) is None:
                setattr(_output, 'mime_type', profile['mime_type'])
            tmp_ds = None
            return _output

        tmp_ds = None
        return _output
