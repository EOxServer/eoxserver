# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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


from eoxserver.contrib import mapserver as ms
from eoxserver.core.util.iteratortools import pairwise_iterative


def create_raster_style(name, layer, minvalue=0, maxvalue=255):
    if name in LINEAR_SCALES:
        colors = LINEAR_SCALES[name]
        length = len(colors)
        colors = [
            (float(i) / length, color)
            for i, color in enumerate(colors)
        ]
    else:
        colors = UNLINEAR_SCALES.get(name)
        if not colors:
            raise KeyError(name)

    # Create style for values below range
    cls = ms.classObj()
    cls.setExpression("([pixel] <= %s)" % (minvalue))
    cls.group = name
    style = ms.styleObj()
    style.color = colors[0][1]
    cls.insertStyle(style)
    layer.insertClass(cls)

    # Create style for values above range
    cls = ms.classObj()
    cls.setExpression("([pixel] > %s)" % (maxvalue))
    cls.group = name
    style = ms.styleObj()
    style.color = colors[-1][1]
    cls.insertStyle(style)
    layer.insertClass(cls)
    layer.classgroup = name

    interval = (maxvalue - minvalue)
    for prev_item, next_item in pairwise_iterative(colors):
        prev_perc, prev_color = prev_item
        next_perc, next_color = next_item

        cls = ms.classObj()
        cls.setExpression("([pixel] >= %s AND [pixel] < %s)" % (
            (minvalue + prev_perc * interval), (minvalue + next_perc * interval)
        ))
        cls.group = name

        style = ms.styleObj()
        style.mincolor = prev_color
        style.maxcolor = next_color
        style.minvalue = minvalue + prev_perc * interval
        style.maxvalue = minvalue + next_perc * interval
        style.rangeitem = ""
        cls.insertStyle(style)
        layer.insertClass(cls)


LINEAR_SCALES = {
    "coolwarm": [
        ms.colorObj(255, 0, 0),
        ms.colorObj(255, 255, 255),
        ms.colorObj(0, 0, 255),
    ]
}

UNLINEAR_SCALES = {
    "hsv": [
        (0.0, ms.colorObj(255, 0, 0)),
        (0.169, ms.colorObj(253, 255, 2)),
        (0.173, ms.colorObj(247, 255, 2)),
        (0.337, ms.colorObj(0, 252, 4)),
        (0.341, ms.colorObj(0, 252, 10)),
        (0.506, ms.colorObj(1, 249, 255)),
        (0.671, ms.colorObj(2, 0, 253)),
        (0.675, ms.colorObj(8, 0, 253)),
        (0.839, ms.colorObj(255, 0, 251)),
        (0.843, ms.colorObj(255, 0, 245)),
        (1.0, ms.colorObj(255, 0, 6)),
    ]
}
