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

try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from eoxserver.contrib.vsi import open as vsi_open


def is_landsat8_l1_metadata_file(path):
    """ Checks whether the referenced file is a Landsat 8 metadata file """
    try:
        with vsi_open(path) as f:
            lines = _read_lines(f)

        return next(iter(lines)).strip() == "GROUP = L1_METADATA_FILE"
    except (ValueError, StopIteration):
        return False


def is_landsat8_l1_metadata_content(content):
    """ Checks whether the referenced file is a Landsat 8 metadata file """
    try:
        f = StringIO(content.decode())
        f.seek(0)
        return next(f).strip() == "GROUP = L1_METADATA_FILE"
    except (ValueError, StopIteration):
        return False


def parse_landsat8_l1_metadata_file(path):
    """ Parses a Landsat 8 metadata file to a nested dict representation"""
    with vsi_open(path) as f:
        lines = _read_lines(f)

    iterator = iter(lines)
    _, _ = _parse_line(next(iterator))
    return _parse_group(iterator)


def parse_landsat8_l1_metadata_content(content):
    """ Parses a Landsat 8 metadata file to a nested dict representation"""
    f = StringIO(content.decode())
    f.seek(0)
    _, _ = _parse_line(next(f))
    return _parse_group(f)


def _read_lines(f):
    return f.read().split(b'\n')


def _parse_group(iterator):
    group = {}
    for line in iterator:
        key, value = _parse_line(line)
        if not key or key == "END_GROUP":
            break
        elif key == "GROUP":
            key = value
            value = _parse_group(iterator)
        group[key] = value
    return group


def _parse_line(line):
    line = line.strip()
    if not line or line == "END":
        return (None, None)

    key, _, value = line.partition(" = ")
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]

    return key, value
