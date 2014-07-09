#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    BoundingBoxData, BoundingBox
)

CRSS = (
    4326,  # WGS84
    32661, 32761,  # WGS84 UPS-N and UPS-S
    32601, 32602, 32603, 32604, 32605, 32606, 32607, 32608, 32609, 32610,  # WGS84 UTM  1N-10N
    32611, 32612, 32613, 32614, 32615, 32616, 32617, 32618, 32619, 32620,  # WGS84 UTM 11N-20N
    32621, 32622, 32623, 32624, 32625, 32626, 32627, 32628, 32629, 32630,  # WGS84 UTM 21N-30N
    32631, 32632, 32633, 32634, 32635, 32636, 32637, 32638, 32639, 32640,  # WGS84 UTM 31N-40N
    32641, 32642, 32643, 32644, 32645, 32646, 32647, 32648, 32649, 32650,  # WGS84 UTM 41N-50N
    32651, 32652, 32653, 32654, 32655, 32656, 32657, 32658, 32659, 32660,  # WGS84 UTM 51N-60N
    32701, 32702, 32703, 32704, 32705, 32706, 32707, 32708, 32709, 32710,  # WGS84 UTM  1S-10S
    32711, 32712, 32713, 32714, 32715, 32716, 32717, 32718, 32719, 32720,  # WGS84 UTM 11S-20S
    32721, 32722, 32723, 32724, 32725, 32726, 32727, 32728, 32729, 32730,  # WGS84 UTM 21S-30S
    32731, 32732, 32733, 32734, 32735, 32736, 32737, 32738, 32739, 32740,  # WGS84 UTM 31S-40S
    32741, 32742, 32743, 32744, 32745, 32746, 32747, 32748, 32749, 32750,  # WGS84 UTM 41S-50S
    32751, 32752, 32753, 32754, 32755, 32756, 32757, 32758, 32759, 32760,  # WGS84 UTM 51S-60S
    0, # ImageCRS
)

class TestProcess01(Component):
    """ Test identity process (the ouptuts are copies of the inputs)
        demonstrating various features of the bounding box data inputs
        and outputs.
    """
    implements(ProcessInterface)

    identifier = "TC01:identity:bbox"
    title = "Test Case 01: Bounding box data identity."
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("input00", BoundingBoxData("TC01:input00", crss=CRSS,
            default=BoundingBox([[-90, -180], [+90, +180]]),
        )),
    ]
    outputs = [
        ("output00", BoundingBoxData("TC01:output00", crss=(4326, 0))),
    ]

    @staticmethod
    def execute(**inputs):
        outputs = {}
        outputs['output00'] = inputs['input00']
        return outputs

