#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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


from eoxserver.core import implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import xml
from eoxserver.contrib import mapserver as ms
from eoxserver.resources.coverages import models
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.mapserver.wms.util import MapServerWMSBaseComponent
from eoxserver.services.ows.wms.interfaces import (
    WMSFeatureInfoRendererInterface
)
from eoxserver.services.ows.wcs.v20.encoders import WCS20EOXMLEncoder
from eoxserver.services.result import (
    result_set_from_raw_data, get_content_type, ResultBuffer
)
from eoxserver.services.urls import get_http_service_url

class MapServerWMSFeatureInfoRenderer(MapServerWMSBaseComponent):
    """ A WMS feature info renderer using MapServer.
    """
    implements(WMSFeatureInfoRendererInterface)

    
    def render(self, layer_groups, request_values, request, **options):
        config = CapabilitiesConfigReader(get_eoxserver_config())
        http_service_url = get_http_service_url(request)
        map_ = ms.Map()
        map_.setMetaData({
            "enable_request": "*",
            "onlineresource": http_service_url,
        }, namespace="ows")

        map_.setMetaData("wms_getfeatureinfo_formatlist", "text/html")
        map_.setProjection("EPSG:4326")

        session = self.setup_map(layer_groups, map_, options)

        # check if the required format is EO O&M
        frmt = pop_param(request_values, "info_format")
        use_eoom = False
        if frmt in ("application/xml", "text/xml"):
            request_values.append(("info_format", "application/vnd.ogc.gml"))
            use_eoom = True
        else:
            request_values.append(("info_format", frmt))
        
        with session:
            request = ms.create_request(request_values)
            raw_result = map_.dispatch(request)
            result = result_set_from_raw_data(raw_result)

            if not use_eoom:
                # just return the response
                return result, get_content_type(result)
            else:
                # do a postprocessing step and get all identifiers in order
                # to encode them with EO O&M
                decoder = GMLFeatureDecoder(result[0].data_file.read())
                identifiers = decoder.identifiers
                coverages = models.Coverage.objects.filter(
                    identifier__in=identifiers
                )

                # sort the result with the returned order of coverages
                lookup_table = dict((c.identifier, c) for c in coverages)
                coverages = [
                    lookup_table[identifier] for identifier in identifiers
                ]

                # encode the coverages with the EO O&M 
                encoder = WCS20EOXMLEncoder()

                return [
                    ResultBuffer(
                        encoder.serialize(
                            encoder.encode_coverage_descriptions(coverages)
                        ), encoder.content_type
                    )
                ], encoder.content_type



def pop_param(request_values, name, default=None):
    """ Helper to pop one param from a key-value list
    """
    for param_name, value in request_values:
        if param_name.lower() == name:
            request_values.remove((param_name, value))
            return value
    return default


class GMLFeatureDecoder(xml.Decoder):
    identifiers = xml.Parameter("//identifier/text()", num="*")
