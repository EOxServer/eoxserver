#-------------------------------------------------------------------------------
# $Id$
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


from eoxserver.core import Component, implements
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.util.timetools import isoformat
from eoxserver.contrib.mapserver import create_request, Map, Layer
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wcs.interfaces import (
    WCSCapabilitiesRendererInterface
)


class MapServerWCSCapabilitiesRenderer(Component):
    """ WCS Capabilities renderer implementation using MapServer.
    """
    implements(WCSCapabilitiesRendererInterface)

    def render(self, coverages, request_values):
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        map_ = Map()
        map_.setMetaData({
            "enable_request": "*",
            "onlineresource": conf.http_service_url,
            "service_onlineresource": conf.http_service_url,
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
        }, namespace="ows")
        map_.setProjection("EPSG:4326")


        for coverage in coverages:
            layer = Layer(coverage.identifier)
            
            layer.setProjection(coverage.spatial_reference.proj)
            extent = coverage.extent
            size = coverage.size
            resolution = ((extent[2] - extent[0]) / float(size[0]),
                          (extent[1] - extent[3]) / float(size[1]))

            layer.setExtent(*extent)
            layer.setMetaData({
                "title": coverage.identifier,
                "label": coverage.identifier,
                "extent": "%.10g %.10g %.10g %.10g" % extent,
                "resolution": "%.10g %.10g" % resolution,
                "size": "%d %d" % size,
            }, namespace="wcs")

            map_.insertLayer(layer)
        
        request = create_request(request_values)
        response = map_.dispatch(request)
        return response.content, response.content_type
