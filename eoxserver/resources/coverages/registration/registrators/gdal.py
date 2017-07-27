#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from eoxserver.contrib import gdal
from eoxserver.backends.access import get_vsi_path
from eoxserver.resources.coverages.metadata.coverage_formats import (
    get_reader_by_test
)
from eoxserver.resources.coverages.registration.base import BaseRegistrator


class GDALRegistrator(BaseRegistrator):
    scheme = "GDAL"

    def _read_metadata_from_data(self, data_item, retrieved_metadata, cache):
        ds = gdal.Open(get_vsi_path(data_item))
        reader = get_reader_by_test(ds)
        if reader:
            values = reader.read(ds)

            format_ = values.pop("format", None)
            if format_:
                data_item.format = format_

            for key, value in values.items():
                retrieved_metadata.setdefault(key, value)
        ds = None
