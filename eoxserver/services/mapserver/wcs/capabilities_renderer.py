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

from lxml import etree

from eoxserver.core import Component, implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.timetools import isoformat
from eoxserver.contrib.mapserver import create_request, Map, Layer
from eoxserver.resources.coverages import crss
from eoxserver.render.coverage.objects import Coverage
from eoxserver.services.mapserver.wcs.base_renderer import BaseRenderer
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wcs.interfaces import (
    WCSCapabilitiesRendererInterface
)
from eoxserver.services.ows.version import Version
from eoxserver.services.result import result_set_from_raw_data, get_content_type, ResultBuffer
from eoxserver.services.urls import get_http_service_url


class MapServerWCSCapabilitiesRenderer(BaseRenderer):
    """ WCS Capabilities renderer implementation using MapServer.
    """
    implements(WCSCapabilitiesRendererInterface)

    versions = (Version(1, 0), Version(1, 1))

    def supports(self, params):
        return params.version in self.versions

    def render(self, params):
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        http_service_url = get_http_service_url(params.http_request)

        map_ = Map()
        map_.setMetaData({
            "enable_request": "*",
            "onlineresource": http_service_url,
            "service_onlineresource": conf.onlineresource,
            "updateSequence": conf.update_sequence,
            "name": conf.name,
            "title": conf.title,
            "label": conf.title,
            "abstract": conf.abstract,
            "accessconstraints": conf.access_constraints,
            "addresstype": "",
            "address": conf.delivery_point,
            "stateorprovince": conf.administrative_area,
            "city": conf.city,
            "postcode": conf.postal_code,
            "country": conf.country,
            "contactelectronicmailaddress": conf.electronic_mail_address,
            "contactfacsimiletelephone": conf.phone_facsimile,
            "contactvoicetelephone": conf.phone_voice,
            "contactperson": conf.individual_name,
            "contactorganization": conf.provider_name,
            "contactposition": conf.position_name,
            "role": conf.role,
            "hoursofservice": conf.hours_of_service,
            "contactinstructions": conf.contact_instructions,
            "fees": conf.fees,
            "keywordlist": ",".join(conf.keywords),
            "formats": " ".join([f.wcs10name for f in self.get_wcs_formats()]),
            "srs": " ".join(crss.getSupportedCRS_WCS(format_function=crss.asShortCode)),
        }, namespace="ows")
        map_.setProjection("EPSG:4326")

        for outputformat in self.get_all_outputformats(False):
            map_.appendOutputFormat(outputformat)

        for coverage in params.coverages:
            layer = Layer(coverage.identifier)

            render_coverage = Coverage.from_model(coverage)
            layer.setProjection(render_coverage.grid.spatial_reference.proj)
            extent = render_coverage.extent
            size = render_coverage.size
            resolution = ((extent[2] - extent[0]) / float(size[0]),
                          (extent[1] - extent[3]) / float(size[1]))

            layer.setExtent(*extent)
            layer.setMetaData({
                "title": coverage.identifier,
                "label": coverage.identifier,
                "extent": "%.10g %.10g %.10g %.10g" % extent,
                "resolution": "%.10g %.10g" % resolution,
                "size": "%d %d" % size,
                "formats": " ".join([f.wcs10name for f in self.get_wcs_formats()]),
                "srs": " ".join(crss.getSupportedCRS_WCS(format_function=crss.asShortCode)),
            }, namespace="wcs")

            map_.insertLayer(layer)

        request = create_request(params)
        request.setParameter("version", params.version)
        raw_result = map_.dispatch(request)
        result = result_set_from_raw_data(raw_result)
        xml_result = etree.fromstring(result[0].data)

        for elem in xml_result.xpath('//*[local-name() = "metadataLink"]'):
            elem.getparent().remove(elem)

        # Add CQL parameter to GetCapabilities operation
        for elem in xml_result.xpath('//*[local-name() = "Operation"][@name = "GetCapabilities"]'):
            ows = elem.nsmap['ows']
            param = etree.SubElement(elem, '{%s}Parameter' % ows)
            param.attrib['name'] = 'cql'
            etree.SubElement(param, '{%s}AnyValue' % ows)

        xml_result_data = etree.tostring(xml_result, pretty_print=True, encoding='UTF-8', xml_declaration=True)

        result[0] = ResultBuffer(xml_result_data, result[0].content_type)
        return result
