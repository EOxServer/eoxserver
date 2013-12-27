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
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import models
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.services.ows.version import Version
from eoxserver.services.exceptions import NoSuchCoverageException
from eoxserver.services.ows.wcs.interfaces import (
    WCSCoverageDescriptionRendererInterface
)
from eoxserver.services.result import result_set_from_raw_data


class CoverageDescriptionMapServerRenderer(BaseRenderer):
    """ A coverage description renderer implementation using mapserver.
    """

    implements(WCSCoverageDescriptionRendererInterface)

    versions = (Version(1, 1), Version(1, 0))
    handles = (models.RectifiedDataset, models.RectifiedStitchedMosaic, models.ReferenceableDataset)

    def supports(self, params):
        return (
            params.version in self.versions 
            and all(
                map(lambda c: issubclass(c.real_type, self.handles), params.coverages)
            )
        )

    def render(self, params):
        map_ = self.create_map()

        use_name = (params.version == Version(1, 0))

        for coverage in params.coverages:

            # ReferenceableDatasets are not supported in WCS < 2.0
            if issubclass(coverage.real_type, models.ReferenceableDataset):
                raise NoSuchCoverageException((coverage.identifier,))

            data_items = self.data_items_for_coverage(coverage)
            native_format = self.get_native_format(coverage, data_items)
            layer = self.layer_for_coverage(
                coverage, native_format, params.version
            )
            map_.insertLayer(layer)
        
        for outputformat in self.get_all_outputformats(not use_name):
            map_.appendOutputFormat(outputformat)

        request = ms.create_request(params)
        raw_result = ms.dispatch(map_, request)
        result = result_set_from_raw_data(raw_result)
        return result
