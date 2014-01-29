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

from django.utils.timezone import now

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap
from eoxserver.core.util.timetools import isoformat
from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.component import ServiceComponent, env
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.services.ows.wps.parameters import (
    is_literal_type, LiteralData, ComplexData, BoundingBoxData
)
from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, ns_ows, ns_wps, ns_xlink, ns_xml
)


class WPS10BaseXMLEncoder(XMLEncoder):
    def encode_process_brief(self, process):
        elem = WPS("Process",
            OWS("Identifier", process.identifier),
            OWS("Title", getattr(process, "title", None) or process.identifier),
            OWS("Abstract", getattr(process, "description", ""))
        )

        elem.extend([
            OWS("Metadata", metadata)
            for metadata in getattr(process, "metadata", [])
        ])

        elem.extend([
            OWS("Profile", profile)
            for profile in getattr(process, "profiles", [])
        ])

        version = getattr(process, "version", None)
        if version:
            elem.attr[ns_wps("processVersion")] = version

        return elem

    def encode_parameter(self, name, parameter, is_input):
        # support for the shorthand
        if is_literal_type(parameter):
            parameter = LiteralData(name, parameter)

        # TODO: minOccurs/maxOccurs correct
        elem = WPS("Input" if is_input else "Output",
            OWS("Identifier", parameter.identifier or name)
        )

        if parameter.title:
            elem.append(OWS("Title", parameter.title))
        if parameter.description:
            elem.append(OWS("Abstract", parameter.description))

        if isinstance(parameter, LiteralData):
            data_elem = WPS("LiteralData" if is_input else "LiteralOutput")

            literal_type_name = parameter.type_name
            if literal_type_name:
                data_elem.append(
                    OWS("DataType", literal_type_name, **{
                        ns_ows("reference"): "http://www.w3.org/TR/xmlschema-2/#%s" % literal_type_name
                    })
                )

            if parameter.uoms:
                data_elem.append(
                    WPS("UOMs",
                        WPS("Default",
                            OWS("UOM", parameter.uoms[0])
                        ),
                        WPS("Supported", *[
                            OWS("UOM", uom) for uom in parameter.uoms
                        ])
                    )
                )

            if is_input and parameter.allowed_values:
                data_elem.append(
                    OWS("AllowedValues", *[
                        OWS("AllowedValue", str(allowed_value))
                        for allowed_value in parameter.allowed_values
                    ])
                )
            elif is_input and parameter.values_reference:
                data_elem.append(
                    WPS("ValuesReference", **{
                        ns_ows("reference"): parameter.values_reference,
                        "valuesForm": parameter.values_reference
                    })
                )
            elif is_input:
                data_elem.append(OWS("AnyValue"))

            if is_input and parameter.default is not None:
                elem.attrib["minOccurs"] = "0"
                data_elem.append(
                    WPS("Default", str(parameter.default))
                )

        elif isinstance(parameter, ComplexData):
            formats = parameter.formats
            if isinstance(formats, Format):
                formats = (formats,)

            data_elem = WPS("ComplexData" if is_input else "ComplexOutput",
                WPS("Default",
                    self.encode_format(formats[0])
                ),
                WPS("Supported", *[
                    self.encode_format(frmt) for frmt in formats
                ])
            )

        elif isinstance(parameter, BoundingBoxData):
            # TODO: implement
            data_elem = WPS("BoundingBoxData" if is_input else "BoundingBoxOutput")

        elem.append(data_elem)
        return elem
        

    def encode_format(self, frmt):
        elem = WPS("Format",
            WPS("MimeType", frmt.mime_type)
        )

        if frmt.encoding:
            elem.append(WPS("Encoding", frmt.encoding))

        if frmt.encoding:
            elem.append(WPS("Schema", frmt.schema))



class WPS10CapabilitiesXMLEncoder(WPS10BaseXMLEncoder):
    def encode_capabilities(self, processes):

        config = get_eoxserver_config()

        # TODO


        conf = CapabilitiesConfigReader(get_eoxserver_config())

        return WPS("Capabilities",
            OWS("ServiceIdentification",
                OWS("Title", conf.title),
                OWS("Abstract", conf.abstract),
                OWS("Keywords", *[
                    OWS("Keyword", keyword) for keyword in conf.keywords 
                ]),
                OWS("ServiceType", "WPS"),
                OWS("ServiceTypeVersion", "1.0.0"),
                OWS("Fees", conf.fees),
                OWS("AccessConstraints", conf.access_constraints),
            ),
            OWS("ServiceProvider",
                OWS("ProviderName", conf.provider_name),
                OWS("ProviderSite", conf.provider_site),
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
            self.encode_operations_metadata(conf),
            self.encode_process_offerings(processes),
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
                "service": "WPS", ns_xml("lang"): "en-US",
                "updateSequence": conf.update_sequence
            }
        )
    
    def encode_operations_metadata(self, conf):
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

        return OWS("OperationsMetadata",*[
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

    def encode_process_offerings(self, processes):
        return WPS("ProcessOfferings", *[
                self.encode_process_brief(process)
                for process in processes
            ]
        )

    def get_schema_locations(self):
        return {"wps": ns_wps.schema_location}




class WPS10ProcessDescriptionsXMLEncoder(WPS10BaseXMLEncoder):
    def encode_process_descriptions(self, processes):
        return WPS("ProcessDescriptions", *[
            self.encode_process_description(process) for process in processes
        ])

    def encode_process_description(self, process):
        elem = self.encode_process_brief(process)

        elem.extend([
            WPS("DataInputs", *[
                self.encode_parameter(name, parameter, True)
                for name, parameter in process.inputs.items()
            ]),
            WPS("ProcessOutputs", *[
                self.encode_parameter(name, parameter, False)
                for name, parameter in process.outputs.items()
            ])
        ])
        return elem


class WPS10ExecuteResponseXMLEncoder(WPS10BaseXMLEncoder):
    def encode_execute_response(self, process, outputs):
        return WPS("ExecuteResponse",
            self.encode_process_brief(process),
            WPS("Status",
                WPS("ProcessSucceded"), # TODO: other states
                creationTime=isoformat(now())
            ),
            WPS("DataInputs",
            ), # TODO: only if lineage == True
            WPS("OutputDefinitions", *[
                self.encode_parameter(name, parameter, False)
                for name, parameter in process.outputs.items()
            ]),
            WPS("ProcessOutputs", *[
                self.encode_output(name, process.outputs[name], data)
                for name, data in outputs.items()
            ])
        )

    def encode_output(self, name, parameter, data):
        elem = self.encode_parameter(name, parameter, False)
        elem.append(
            WPS("Data",
                WPS("LiteralData", str(data))
            )
        )
        return elem
