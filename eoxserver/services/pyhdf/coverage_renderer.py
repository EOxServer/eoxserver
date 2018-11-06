# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2018 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------


from os.path import join
from datetime import datetime
from uuid import uuid4
import logging
import csv
import tempfile

from pyhdf.HDF import HDF, HC
from pyhdf.SD import SD
import pyhdf.VS


import numpy as np
from scipy.interpolate import interp1d

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.core.util.rect import Rect
from eoxserver.contrib import vsi, vrt, gdal, gdal_array
from eoxserver.contrib.vrt import VRTBuilder
from eoxserver.services.ows.version import Version
from eoxserver.services.result import ResultFile, ResultBuffer
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.exceptions import (
    RenderException, OperationNotSupportedException
)
from eoxserver.processing.gdal import reftools


logger = logging.getLogger(__name__)


INTERPOLATION_MAP = {
    "nearest-neighbour": "nearest",
    "bilinear": "linear",
    "cubic": "cubic",
    "cubic-spline": "cubic",
}


class PyHDFCoverageRenderer(object):
    versions = (Version(2, 1),)

    def supports(self, params):
        return (
            params.version in self.versions and
            params.coverage.arraydata_locations[0].format == 'HDF'
        )

    def render(self, params):
        coverage = params.coverage
        data_items = coverage.arraydata_locations
        range_type = coverage.range_type

        filename, part = params.coverage.arraydata_locations[0].path

        if part in ('Latitude', 'Longitude', 'Profile_time'):
            vdata = HDF(str(filename), HC.READ).vstart()
            data = vdata.attach(str(part))[:]
            data = np.hstack(data)

            if params.subsets:
                for subset in params.subsets:
                    if subset.is_x and hasattr(subset, 'low'):
                        if subset.low is not None and subset.high is not None:
                            data = data[subset.low:subset.high]
                        elif subset.low is not None:
                            data = data[subset.low:]
                        elif subset.high is not None:
                            data = data[:subset.high]

                    # TODO: subset slice

            cur_size = data.shape[0]

            new_size = None
            if params.scalefactor:
                new_size = float(cur_size) * params.scalefactor

            elif params.scales and params.scales[0].axis == 'x':
                scale = params.scales[0]
                if hasattr(scale, 'scale'):
                    new_size = float(cur_size) * scale.scale
                elif hasattr(scale, 'size'):
                    new_size = scale.size

            if new_size is not None:
                old_x = np.linspace(0, 1, cur_size)
                new_x = np.linspace(0, 1, new_size)

                if params.interpolation:
                    interpolation = INTERPOLATION_MAP[params.interpolation]
                else:
                    interpolation = 'nearest'

                data = interp1d(old_x, data, kind=interpolation)(new_x)

        if part == 'Height':
            sd_file = SD(str(filename))
            data = sd_file.select(str(part))

            slc_x = slice(None)
            slc_y = slice(None)

            for subset in params.subsets:
                if subset.is_x:
                    if hasattr(subset, 'low'):
                        if subset.low is not None and subset.high is not None:
                            slc_x = slice(int(subset.low), int(subset.high) + 1)
                        elif subset.low is not None:
                            slc_x = slice(subset.low, None)
                        elif subset.high is not None:
                            slc_x = slice(None, int(subset.high) + 1)
                    if hasattr(subset, 'value'):
                        slc_x = int(subset.value)

                if subset.is_y:
                    if hasattr(subset, 'low'):
                        if subset.low is not None and subset.high is not None:
                            slc_y = slice(int(subset.low), int(subset.high) + 1)
                        elif subset.low is not None:
                            slc_y = slice(int(subset.low), None)
                        elif subset.high is not None:
                            slc_y = slice(None, int(subset.high) + 1)
                    if hasattr(subset, 'value'):
                        slc_y = int(subset.value)

            data = data[slc_x, slc_y]

            for d, name in ((0, 'x'), (1, 'y')):
                cur_size = data.shape[d]

                new_size = None
                if params.scalefactor:
                    new_size = float(cur_size) * params.scalefactor

                for scale in params.scales:
                    if scale.axis != name:
                        continue

                    if hasattr(scale, 'scale'):
                        new_size = float(cur_size) * scale.scale
                    elif hasattr(scale, 'size'):
                        new_size = scale.size

                if new_size is not None:
                    old_x = np.linspace(0, 1, cur_size)
                    new_x = np.linspace(0, 1, new_size)

                    if params.interpolation:
                        interpolation = INTERPOLATION_MAP[params.interpolation]
                    else:
                        interpolation = 'nearest'

                    data = interp1d(
                        old_x, data, kind=interpolation, axis=d
                    )(new_x)

        frmt = params.format

        if not frmt:
            raise Exception('Missing format')

        if frmt == 'text/csv':
            if data.ndim != 1:
                raise Exception('CSV encoding only possible for 1D outputs.')

            out_path = '/tmp/%s.csv' % uuid4().hex

            with open(out_path, 'w') as f:
                writer = csv.writer(f)
                writer.writerow([part])
                writer.writerows(data.reshape((data.shape[0], 1)))

            return [
                ResultFile(out_path, 'text/csv', '%s.csv' % coverage.identifier)
            ]

        elif frmt == 'image/tiff':
            if data.ndim not in (1, 2):
                raise Exception('TIFF encoding only possible for 2D outputs.')

            if data.ndim == 1:
                data = data.reshape(data.shape[0], 1)

            out_path = '/tmp/%s.tif' % uuid4().hex
            gdal_array.SaveArray(data, out_path, 'GTiff')

            return [
                ResultFile(
                    out_path, 'image/tiff', '%s.tif' % coverage.identifier
                )
            ]
