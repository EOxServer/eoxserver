#-------------------------------------------------------------------------------
#
# WPS 1.0 Capabilities XML encoders
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.component import ServiceComponent, env
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, ns_ows, ns_wps, ns_xlink, ns_xml
)

from .process_description import encode_process_brief
from .base import WPS10BaseXMLEncoder


def _encode_operations_metadata(conf):
    component = ServiceComponent(env)
    versions = ("1.0.0",)
    get_handlers = component.query_service_handlers(
        service="WPS", versions=versions, method="GET"
    )
    post_handlers = component.query_service_handlers(
        service="WPS", versions=versions, method="POST"
    )
    all_handlers = sorted(
        set(get_handlers + post_handlers), key=lambda h: h.request
    )
    url = conf.http_service_url
    return OWS("OperationsMetadata", *[
        OWS("Operation",
            OWS("DCP",
                OWS("HTTP",
                    # TODO: only select available
                    OWS("Get", **{ns_xlink("href"): url}),
                    OWS("Post", **{ns_xlink("href"): url}),
                )
            ), name=handler.request
        )
        for handler in all_handlers
    ])


class WPS10CapabilitiesXMLEncoder(WPS10BaseXMLEncoder):

    @staticmethod
    def encode_capabilities(processes):
        conf = CapabilitiesConfigReader(get_eoxserver_config())
        return WPS("Capabilities",
            OWS("ServiceIdentification",
                OWS("Title", conf.title),
                OWS("Abstract", conf.abstract),
                OWS("Keywords", *(OWS("Keyword", kw) for kw in conf.keywords)),
                OWS("ServiceType", "WPS"),
                OWS("ServiceTypeVersion", "1.0.0"),
                OWS("Fees", conf.fees),
                OWS("AccessConstraints", conf.access_constraints),
            ),
            OWS("ServiceProvider",
                OWS("ProviderName", conf.provider_name),
                OWS("ProviderSite", **{ns_xlink("href"): conf.provider_site}),
                OWS("ServiceContact",
                    OWS("IndividualName", conf.individual_name),
                    OWS("PositionName", conf.position_name),
                    OWS("ContactInfo",
                        OWS("Phone",
                            OWS("Voice", conf.phone_voice),
                            OWS("Facsimile", conf.phone_facsimile)
                        ),
                        OWS("Address",
                            OWS("DeliveryPoint", conf.delivery_point),
                            OWS("City", conf.city),
                            OWS("AdministrativeArea", conf.administrative_area),
                            OWS("PostalCode", conf.postal_code),
                            OWS("Country", conf.country),
                            OWS("ElectronicMailAddress", conf.electronic_mail_address)
                        )
                    )
                )
            ),
            _encode_operations_metadata(conf),
            WPS("ProcessOfferings", *(encode_process_brief(p) for p in processes)),
            WPS("Languages",
                WPS("Default",
                    OWS("Language", "en-US")
                ),
                WPS("Supported",
                    OWS("Language", "en-US")
                )
            ),
            # TODO: WPS("WSDL") ?
            **{
                "service": "WPS",
                "version": "1.0.0",
                ns_xml("lang"): "en-US",
                "updateSequence": conf.update_sequence,
            }
        )
