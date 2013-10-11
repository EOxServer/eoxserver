#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


from eoxserver.core import implements
from eoxserver.contrib.mapserver import create_request
from eoxserver.backends.cache import CacheContext
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.services.ows.wcs.interfaces import (
    WCSCoverageDescriptionRendererInterface
)


class CoverageDescriptionMapServerRenderer(BaseRenderer):
    implements(WCSCoverageDescriptionRendererInterface)

    def render(self, coverages, request_values):
        map_ = self.create_map()

        use_name = self.find_param(request_values, "version").startswith("1.0")

        for coverage in coverages:
            data_items = self.data_items_for_coverage(coverage)
            native_format = self.get_native_format(coverage, data_items)
            layer = self.layer_for_coverage(coverage, native_format)

            map_.insertLayer(layer)

        
        for outputformat in self.get_all_outputformats(not use_name):
            map_.appendOutputFormat(outputformat)

        request = create_request(request_values)
        response = map_.dispatch(request)

        return response.content, response.content_type
