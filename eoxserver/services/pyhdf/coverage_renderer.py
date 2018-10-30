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

from pyhdf.HDF import HDF, HC
from pyhdf.SD import SD
import pyhdf.VS

import numpy as np
from scipy.interpolate import interp1d

from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config
from eoxserver.core.util.rect import Rect
from eoxserver.contrib import vsi, vrt, gdal
from eoxserver.contrib.vrt import VRTBuilder
from eoxserver.services.ows.version import Version
from eoxserver.services.result import ResultFile, ResultBuffer
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.exceptions import (
    RenderException, OperationNotSupportedException
)
from eoxserver.processing.gdal import reftools


logger = logging.getLogger(__name__)


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

        print coverage, range_type

        filename, part = params.coverage.arraydata_locations[0].path

        print part

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


                if params.scalefactor:
                    size = float(cur_size) * params.scalefactor

                    old_x = np.linspace(0, 1, cur_size)
                    new_x = np.linspace(0, 1, size)

                    print data

                    data = interp1d(old_x, data, kind='nearest')(new_x)

                    print data


        if part == 'Height':
            sd_file = SD(str(filename))
            data = sd_file.select(str(part))[:]
            data = np.array(data)




        # if params.subset


        # import pdb; pdb.set_trace()

        print data[:10]



