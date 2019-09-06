#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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
#-------------------------------------------------------------------------------

"""\
This module imports and initializes GDAL; i.e enables exceptions and registers
all available drivers.
"""

import os
import contextlib


if os.environ.get('READTHEDOCS', None) != 'True':
    try:
        from osgeo.gdal import *
    except ImportError:
        from gdal import *

    try:
        from collections import OrderedDict as SortedDict
    except ImportError:
        from django.utils.datastructures import SortedDict

    UseExceptions()
    AllRegister()

    GCI_TO_NAME = SortedDict((
        (GCI_Undefined, "Undefined"),
        (GCI_GrayIndex, "GrayIndex"),
        (GCI_PaletteIndex, "PaletteIndex"),
        (GCI_RedBand, "RedBand"),
        (GCI_GreenBand, "GreenBand"),
        (GCI_BlueBand, "BlueBand"),
        (GCI_AlphaBand, "AlphaBand"),
        (GCI_HueBand, "HueBand"),
        (GCI_SaturationBand, "SaturationBand"),
        (GCI_LightnessBand, "LightnessBand"),
        (GCI_CyanBand, "CyanBand"),
        (GCI_MagentaBand, "MagentaBand"),
        (GCI_YellowBand, "YellowBand"),
        (GCI_BlackBand, "BlackBand"),
        (GCI_YCbCr_YBand, "YBand"),
        (GCI_YCbCr_CbBand, "CbBand"),
        (GCI_YCbCr_CrBand, "CrBand"),
    ))

    NAME_TO_GCI = dict((j.lower(), i) for (i, j) in GCI_TO_NAME.items())

    GDT_TO_NAME = SortedDict((
        (GDT_Byte, "Byte"),
        (GDT_UInt16, "UInt16"),
        (GDT_Int16, "Int16"),
        (GDT_UInt32, "UInt32"),
        (GDT_Int32, "Int32"),
        (GDT_Float32, "Float32"),
        (GDT_Float64, "Float64"),
        (GDT_CInt16, "CInt16"),
        (GDT_CInt32, "CInt32"),
        (GDT_CFloat32, "CFloat32"),
        (GDT_CFloat64, "CFloat64"),
    ))

    NAME_TO_GDT = SortedDict((j.lower(), i) for (i, j) in GDT_TO_NAME.items())

    GDT_NUMERIC_LIMITS = {
        GDT_Byte: (0, 255),
        GDT_Int16: (-32768, 32767),
        GDT_UInt16: (0, 65535),
        GDT_CInt16: (complex(-32768, -32768), complex(32767, 32767)),
        GDT_Int32: (-2147483648, 2147483647),
        GDT_UInt32: (0, 4294967295),
        GDT_CInt32: (
            complex(-2147483648, -2147483648), complex(2147483647, 2147483647)
        ),
        GDT_Float32: (-3.40282e+38, 3.40282e+38),
        GDT_CFloat32: (
            complex(-3.40282e+38, -3.40282e+38),
            complex(3.40282e+38, 3.40282e+38)
        ),
        GDT_Float64: (-1.79769e+308, 1.79769e+308),
        GDT_CFloat64: (
            complex(-1.79769e+308, -1.79769e+308),
            complex(1.79769e+308, 1.79769e+308)
        )
    }

    GDT_SIGNIFICANT_FIGURES = {
        GDT_Byte: 3,
        GDT_Int16: 5,
        GDT_UInt16: 5,
        GDT_CInt16: 5,
        GDT_Int32: 10,
        GDT_UInt32: 10,
        GDT_CInt32: 10,
        GDT_Float32: 38,
        GDT_CFloat32: 38,
        GDT_Float64: 308,
        GDT_CFloat64: 308
    }

    GDT_INTEGRAL_TYPES = frozenset(
        (GDT_Byte, GDT_Int16, GDT_UInt16, GDT_Int32, GDT_UInt32)
    )

    GDT_INTEGRAL_COMPLEX_TYPES = frozenset((GDT_CInt16, GDT_CInt32))

    GDT_FLOAT_TYPES = frozenset((GDT_Float32, GDT_Float64))

    GDT_FLOAT_COMPLEX_TYPES = frozenset((GDT_CFloat32, GDT_CFloat64))

    GDT_COMPLEX_TYPES = frozenset(
        (GDT_CInt16, GDT_CInt32, GDT_CFloat32, GDT_CFloat64)
    )


def get_extent(ds):
    """ Gets the extent of the GDAL Dataset in the form (min-x, min-y, max-x, max-y).
    """
    gt = ds.GetGeoTransform()

    x_a = gt[0]
    x_b = gt[0] + gt[1] * ds.RasterXSize
    y_a = gt[3]
    y_b = gt[3] + gt[5] * ds.RasterYSize

    return (min(x_a, x_b), min(y_a, y_b), max(x_a, x_b), max(y_a, y_b))


def set_env(env, fail_on_override=False, return_old=False):
    old_values = {} if return_old else None
    for key, value in env.items():
        if fail_on_override or return_old:
            # old_value = GetConfigOption(str(key))
            old_value = os.environ.get(key)
            if fail_on_override and old_value != value:
                raise Exception(
                    'Would override previous value of %s: %s with %s'
                    % (key, old_value, value)
                )
            elif old_value != value:
                old_values[key] = old_value

        # SetConfigOption(str(key), str(value))
        if value is not None:
            os.environ[key] = value

    return old_values


@contextlib.contextmanager
def config_env(env, fail_on_override=False, reset_old=True):
    old_env = set_env(env, fail_on_override, reset_old)
    yield
    if reset_old:
        set_env(old_env, False, False)


def open_with_env(path, env, shared=True):
    with config_env(env, False):
        return OpenShared(path) if shared else Open(path)
