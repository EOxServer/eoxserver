# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

from eoxserver.core.decoders import InvalidParameterException
from eoxserver.core.util.timetools import parse_iso8601


def parse_bbox(string):
    try:
        bbox = [float(v) for v in string.split(",")]
    except ValueError:
        raise InvalidParameterException("Invalid 'BBOX' parameter.", "bbox")

    if len(bbox) != 4:
        raise InvalidParameterException(
            "Wrong number of arguments for 'BBOX' parameter.", "bbox"
        )

    return bbox


def parse_time(string):
    items = string.split("/")

    if len(items) == 1:
        return [parse_iso8601(items[0])]
    elif len(items) in (2, 3):
        # ignore resolution
        return [parse_iso8601(items[0]), parse_iso8601(items[1])]

    raise InvalidParameterException("Invalid TIME parameter.", "time")


def int_or_str(string):
    try:
        return int(string)
    except ValueError:
        return string


def float_or_str(string):
    try:
        return float(string)
    except ValueError:
        return string


def parse_render_variables(raw):
    items = [
        item.partition("=")[::2]
        for item in raw.split(',')
    ]
    return dict(
        (item[0], float_or_str(item[1]))
        for item in items
    )
