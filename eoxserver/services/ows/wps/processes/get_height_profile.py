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

import csv
from uuid import uuid4
import os

from math import radians, cos, sin, asin, sqrt

import numpy as np
import matplotlib.pyplot as plt

from eoxserver.contrib import gdal

from eoxserver.core import Component, implements

from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, FormatText, CDAsciiTextBuffer,
    CDByteBuffer, FormatBinaryRaw, FormatBinaryBase64,
)
from eoxserver.services.ows.wps.exceptions import InvalidInputValueError

from eoxserver.resources.coverages import models
from eoxserver.backends.access import gdal_open


class GetHeightProfileProcess(Component):
    """ GetHeightProfileProcess defines a WPS process needed by the EOxC
        DEM implementtation """

    def __init__(self):
        super(GetHeightProfileProcess, self).__init__()

    implements(ProcessInterface)

    identifier = "GetHeightProfile"
    title = "Get the hight profile for a coverage"
    description = ("provides a height profile between 2 points within a coverage "
                  " The process is used by the  by the EOxC DEM implementtation")
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
        "interpolation_method": LiteralData(
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
    def execute(coverage, line, interval, interpolation_method, profile, **kwarg):
        """ The main execution function for the process.
        """

        if isinstance(line, str):
            line = eval(line)

        line_distance = GetHeightProfileProcess.haversine(line[0], line[1], line[2], line[3])

        # get the dataset series matching the requested ID
        try:
            model = models.Coverage.objects.get(
                identifier=coverage)

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
        proj_str = "+proj=tpeqd +lon_1={} +lat_1={} +lon_2={} +lat_2={}".format(line[0], line[1], line[2], line[3])
        bbox = ((-1 * line_distance / 2), (100*0.5), line_distance / 2, -(100*0.5))
        interval = int(interval)

        # # Calculate the number of samples in the profile.
        num_samples = int(line_distance / interval)

        tmp_ds = '/vsimem/%s' % uuid4().hex

        profile_ds = gdal.Warp(tmp_ds, ds, dstSRS=proj_str, outputBounds=bbox,
                        height=1, width=num_samples, resampleAlg=interpolation_method,
                        format='Gtiff')

        array_out = profile_ds.GetRasterBand(1).ReadAsArray()

        y = []
        for (d, value) in enumerate(array_out[0, :]):
            y.append(value)
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
                extension = ".png"

            elif profile['mime_type'] == "image/jpeg":
                extension = ".jpg"

            elif profile['mime_type'] == "image/tiff":
                extension = ".tif"

            tmppath = '{}.{}'.format(uuid4().hex, extension)
            output_filename = 'height_profile.%s' % extension
            fig = plt.figure()
            plt.plot(x, y)
            fig.savefig(tmppath)
            with open(tmppath, 'rb') as fid:
                _output = CDByteBuffer(
                    fid.read(), filename=output_filename,
                )
            os.remove(tmppath)
            return _output

        return _output
