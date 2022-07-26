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

from django.conf import settings
import traceback
from itertools import chain

from lxml import etree
from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap
from eoxserver.services.ows.dispatch import filter_handlers


ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
ns_ows = NameSpace("http://www.opengis.net/ows/2.0", "ows", "http://schemas.opengis.net/ows/2.0/owsAll.xsd")
ns_xml = NameSpace("http://www.w3.org/XML/1998/namespace", "xml")

nsmap = NameSpaceMap(ns_ows)
OWS = ElementMaker(namespace=ns_ows.uri, nsmap=nsmap)


class OWS20Encoder(XMLEncoder):
    def get_conf(self):
        raise NotImplementedError

    def get_http_service_url(self, request):
        conf = self.get_conf()
        if conf.http_service_url:
            return conf.http_service_url
        from eoxserver.services.urls import get_http_service_url
        return get_http_service_url(request)

    def encode_reference(self, node_name, href, reftype="simple"):

        attributes = {ns_xlink("href"): href}
        if reftype:
            attributes[ns_xlink("type")] = reftype

        return OWS(node_name, **attributes)

    def encode_service_identification(self, service, conf, profiles):
        # get a list of versions in descending order from all active
        # GetCapabilities handlers.
        handlers = filter_handlers(
            service=service, request="GetCapabilities"
        )
        versions = sorted(
            set(chain(*[handler.versions for handler in handlers])),
            reverse=True
        )

        elem = OWS("ServiceIdentification",
            OWS("Title", conf.title),
            OWS("Abstract", conf.abstract),
            OWS("Keywords", *[
                OWS("Keyword", keyword) for keyword in conf.keywords
            ]),
            OWS("ServiceType", "OGC WCS", codeSpace="OGC")
        )

        elem.extend(
            OWS("ServiceTypeVersion", version) for version in versions
        )

        elem.extend(
            OWS("Profile", "http://www.opengis.net/%s" % profile)
            for profile in profiles
        )

        elem.extend((
            OWS("Fees", conf.fees),
            OWS("AccessConstraints", conf.access_constraints)
        ))
        return elem

    def encode_service_provider(self, conf):
        return OWS("ServiceProvider",
            OWS("ProviderName", conf.provider_name),
            self.encode_reference("ProviderSite", conf.provider_site),
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
                        OWS(
                            "ElectronicMailAddress",
                            conf.electronic_mail_address
                        )
                    ),
                    self.encode_reference(
                        "OnlineResource", conf.onlineresource
                    ),
                    OWS("HoursOfService", conf.hours_of_service),
                    OWS("ContactInstructions", conf.contact_instructions)
                ),
                OWS("Role", conf.role)
            )
        )

    def encode_operations_metadata(self, request, service, versions):
        get_handlers = filter_handlers(
            service=service, versions=versions, method="GET"
        )
        post_handlers = filter_handlers(
            service=service, versions=versions, method="POST"
        )
        all_handlers = sorted(
            set(get_handlers + post_handlers),
            key=lambda h: (getattr(h, "index", 10000), h.request)
        )

        http_service_url = self.get_http_service_url(request)

        operations = []
        for handler in all_handlers:
            methods = []
            if handler in get_handlers:
                methods.append(
                    self.encode_reference("Get", http_service_url)
                )
            if handler in post_handlers:
                post = self.encode_reference("Post", http_service_url)
                post.append(
                    OWS("Constraint",
                        OWS("AllowedValues",
                            OWS("Value", "XML")
                        ), name="PostEncoding"
                    )
                )
                methods.append(post)

            operations.append(
                OWS("Operation",
                    OWS("DCP",
                        OWS("HTTP", *methods)
                    ),
                    # apply default values as constraints
                    *([
                        OWS("Constraint",
                            OWS("NoValues"),
                            OWS("DefaultValue", str(default)),
                            name=name
                        )
                        for name, default
                        in getattr(handler(), "constraints", {}).items()
                    ] + [
                        OWS("Parameter",
                            OWS("AnyValue")
                            if allowed_values is None else
                            OWS("AllowedValues", *[
                                OWS("Value", value)
                                for value in allowed_values
                            ]),
                            name=name
                        )
                        for name, allowed_values
                        in getattr(handler(), "additional_parameters", {}).items()
                    ]),

                    name=handler.request
                )
            )

        return OWS("OperationsMetadata", *operations)


class OWS20ExceptionXMLEncoder(XMLEncoder):
    def encode_exception(self, message, version, code, locator=None, request=None, exception=None):
        exception_attributes = {
            "exceptionCode": str(code)
        }

        if locator:
            exception_attributes["locator"] = str(locator)

        exception_text = (OWS("ExceptionText", message),) if message else ()

        report = OWS("ExceptionReport",
            OWS("Exception", *exception_text, **exception_attributes),
            version=version, **{ns_xml("lang"): "en"}
        )

        try:
            if getattr(settings, 'DEBUG', False):
                report.append(etree.Comment(traceback.format_exc()))
        except:
            pass

        return report

    def get_schema_locations(self):
        return nsmap.schema_locations
