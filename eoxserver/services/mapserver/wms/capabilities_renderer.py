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
from eoxserver.services.ows.wms.interfaces import (
    WMSCapabilitiesRendererInterface
)


class MapServerWMSCapabilitiesRenderer(Component):
    """ WMS Capabilities renderer implementation using MapServer.
    """
    implements(WMSCapabilitiesRendererInterface)

    def render(self, collections, suffixes, request_values):
        conf = CapabilitiesConfigReader(get_eoxserver_config())

        map_ = Map()
        map_.setMetaData({
            "enable_request": "*",
            "onlineresource": conf.http_service_url,
            "title": conf.title,
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
            "fees": conf.fees,
            "keywordlist": ",".join(conf.keywords),
        }, namespace="ows")
        map_.setProjection("EPSG:4326")


        for collection in collections:
            group_name = None
            
            # calculate extent and timextent for every collection
            extent = " ".join(map(str, collection.extent_wgs84))

            eo_objects = collection.eo_objects.filter(
                begin_time__isnull=False, end_time__isnull=False
            )
            timeextent = ",".join(
                map(
                    lambda o: (
                        "/".join(
                            map(isoformat, o.time_extent)
                        ) + "/PT1S"
                    ), eo_objects
                )
            )

            if len(suffixes) > 1:
                # create group layer, if there is more than one suffix for this 
                # collection
                group_name = collection.identifier + "_group"
                group_layer = Layer(group_name)
                group_layer.setMetaData({
                    "title": group_name,
                    "extent": extent
                }, namespace="wms")
                map_.insertLayer(group_layer)

            for suffix in suffixes:
                layer_name = collection.identifier + (suffix or "")
                layer = Layer(layer_name)
                if group_name:
                    layer.setMetaData({
                        "layer_group": "/" + group_name
                    }, namespace="wms")

                layer.setMetaData({
                    "title": layer_name,
                    "extent": extent,
                    "timeextent": timeextent
                }, namespace="wms")
                map_.insertLayer(layer)
        
        request = create_request(request_values)
        response = map_.dispatch(request)
        return response.content, response.content_type
