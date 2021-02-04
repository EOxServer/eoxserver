#-------------------------------------------------------------------------------
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

from lxml import etree
from eoxserver.contrib import mapserver as ms
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.services.ows.version import Version
from eoxserver.services.exceptions import NoSuchCoverageException
from eoxserver.services.result import result_set_from_raw_data, ResultBuffer



class CoverageDescriptionMapServerRenderer(BaseRenderer):
    """ A coverage description renderer implementation using mapserver.
    """

    versions = (Version(1, 1), Version(1, 0))

    def supports(self, params):
        return (
            params.version in self.versions and
            all(
                not coverage.grid.is_referenceable
                for coverage in params.coverages
            )
        )

    def render(self, params):
        map_ = self.create_map()

        use_name = (params.version == Version(1, 0))

        for coverage in params.coverages:

            # ReferenceableDatasets are not supported in WCS < 2.0
            if coverage.grid.is_referenceable:
                raise NoSuchCoverageException((coverage.identifier,))

            data_locations = self.arraydata_locations_for_coverage(coverage)
            native_format = self.get_native_format(coverage, data_locations)
            layer = self.layer_for_coverage(
                coverage, native_format, params.version
            )
            map_.insertLayer(layer)

        for outputformat in self.get_all_outputformats(not use_name):
            map_.appendOutputFormat(outputformat)

        request = ms.create_request(params)
        raw_result = ms.dispatch(map_, request)
        
        result = result_set_from_raw_data(raw_result)
        # load XML using lxml
        # find and exclude <metadataLink> nodes if present
        # re-encode

        xml_result = etree.fromstring(result[0].data)

        for elem in xml_result.xpath('//*[local-name() = "metadataLink"]'):
            elem.getparent().remove(elem)

        xml_result_data =  etree.tostring(xml_result, pretty_print=True, encoding='UTF-8', xml_declaration=True)
        
        result[0] = ResultBuffer(xml_result_data, result[0].content_type)
        
        return result
