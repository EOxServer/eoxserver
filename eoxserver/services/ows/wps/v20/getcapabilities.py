# -------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Bernhard Mallinger <bernhard.mallinger@eox.at>
#
# -------------------------------------------------------------------------------
# Copyright (C) 2021 EOX IT Services GmbH
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
# -------------------------------------------------------------------------------

from typing import List

from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.dispatch import filter_handlers
from eoxserver.services.ows.wps.util import get_processes
from eoxserver.services.ows.wps.interfaces import ProcessInterface

from ows.wps.v20 import encoders
from ows.wps.types import ProcessSummary, ServiceCapabilities
from ows.common.types import Metadata, Operation, OperationMethod


class WPS20GetCapabilitiesHandler(object):
    """WPS 2.0 GetCapabilities service handler."""

    service = "WPS"
    versions = ("2.0.0",)
    request = "GetCapabilities"
    methods = ["GET", "POST"]

    def handle(self, request):
        """Handle HTTP request."""

        conf = CapabilitiesConfigReader(get_eoxserver_config())

        capabilities = ServiceCapabilities(
            title=conf.title,
            abstract=conf.abstract,
            keywords=conf.keywords,
            service_type=self.__class__.service,
            service_type_versions=self.__class__.versions,
            profiles=[],
            fees=conf.fees,
            access_constraints=conf.access_constraints,
            # service provider
            provider_name=conf.provider_name,
            provider_site=conf.provider_site,
            individual_name=conf.individual_name,
            organisation_name=None,
            position_name=conf.position_name,
            # contact info
            phone_voice=conf.phone_voice,
            phone_facsimile=conf.phone_facsimile,
            # address fields
            delivery_point=conf.delivery_point,
            city=conf.city,
            administrative_area=conf.administrative_area,
            postal_code=conf.postal_code,
            country=conf.country,
            electronic_mail_address=conf.electronic_mail_address,
            online_resource=conf.onlineresource,
            hours_of_service=conf.hours_of_service,
            contact_instructions=conf.contact_instructions,
            role=conf.role,
            operations=self._encode_operations_metadata(conf),
            process_summaries=_encode_process_summaries(),
        )

        result = encoders.xml_encode_capabilities(capabilities=capabilities)

        return result.value, result.content_type

    def _encode_operations_metadata(
        self, conf: CapabilitiesConfigReader
    ) -> List[Operation]:
        get_handlers = filter_handlers(
            service="WPS", versions=self.versions, method="GET"
        )
        post_handlers = filter_handlers(
            service="WPS", versions=self.versions, method="POST"
        )
        all_handlers = sorted(
            set(get_handlers + post_handlers), key=lambda h: h.request
        )
        url = conf.http_service_url
        return [
            Operation(
                name=handler.request,
                operation_methods=[
                    OperationMethod(
                        method=method,
                        service_url=url,
                    )
                    for method in handler.methods
                ],
            )
            for handler in all_handlers
        ]


def _encode_process_summaries() -> List[ProcessSummary]:
    processes: List[ProcessInterface] = get_processes()
    return [
        ProcessSummary(
            identifier=(
                identifier := getattr(process, "identifier", type(process).__name__)
            ),
            title=getattr(process, "title", identifier),
            abstract=getattr(process, "description", process.__doc__),
            keywords=[],  # TODO: which value to use?
            metadata=[
                Metadata(
                    about=key,
                    href=value,
                )  # TODO: check if this translation makes sense?
                for key, value in getattr(process, "metadata", {}).items()
            ],
            sync_execute=getattr(process, "synchronous", False),
            async_execute=getattr(process, "asynchronous", False),
            by_value=False,  # TODO: which value to use?
            by_reference=False,  # TODO: which value to use?
            version=getattr(process, "version", "1.0.0"),
            model=None,  # TODO: which value to use?
        )
        for process in processes
    ]
