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

import urllib2
from urlparse import urlparse
from django.http import HttpResponse

from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.core.decoders import kvp, xml
from eoxserver.core.util import multiparttools as mp
from eoxserver.services.ows.interfaces import (
    ServiceHandlerInterface, GetServiceHandlerInterface, 
    PostServiceHandlerInterface
)
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    LiteralData, LITERAL_DATA_NAME
)
from eoxserver.services.ows.wps.exceptions import NoSuchProcessException
from eoxserver.services.ows.wps.v10.util import nsmap, ns_wps, ns_xlink
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ExecuteResponseXMLEncoder
)


class WPS10ExcecuteHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    service = "WPS"
    versions = ("1.0.0",)
    request = "Execute"


    processes = ExtensionPoint(ProcessInterface)
    #result_storage = ExtensionPoint(ResultStorageInterface)
    

    def get_decoder(self, request):
        if request.method == "GET":
            return WPS10ExecuteKVPDecoder(request.GET)
        elif request.method == "POST":
            # support for multipart items
            if request.META["CONTENT_TYPE"].startswith("multipart/"):
                _, data = next(mp.iterate(request.body))
                return WPS10ExecuteXMLDecoder(data)
            return WPS10ExecuteXMLDecoder(request.body)


    def handle(self, request):
        decoder = self.get_decoder(request)

        for process in self.processes:
            if process.identifier == decoder.identifier:
                break
        else: 
            raise NoSuchProcessException((decoder.identifier,))

        input_params = process.inputs
        inputs = decoder.inputs

        kwargs = {}
        for key, parameter in input_params.items():
            if parameter in LITERAL_DATA_NAME:
                parameter = LiteralData(key, parameter)
            try:
                raw_value = inputs.pop(key)

                if isinstance(raw_value, Reference):
                    value = self.resolve_reference(raw_value, request)
                else:
                    value = parameter.parse_value(raw_value)

            except KeyError:
                if parameter.default is None: # TODO: maybe an extra optional flag to allow None as a default value?
                    raise Exception("Parameter '%s' is required." % key)
                value = parameter.default

            kwargs[key] = value

        # execute the process and prepare the result
        result = process.execute(**kwargs)

        response_form = decoder.response_form or ResponseDocument()
        if response_form.raw:
            # Raw response
            # create a direct HTTPResponse from it

            # TODO: multiple outputs
            return HttpResponse(str(result[response_form.outputs[0]]))
        else:
            actual_result = {}
            for output_name in response_form.outputs:
                actual_result[output_name] = result[output_name]

            encoder = WPS10ExecuteResponseXMLEncoder()
            return encoder.serialize(
                encoder.encode_execute_response(
                    process, actual_result
                )
            )

    def resolve_reference(self, reference, request):
        url = urlparse(reference.href)

        # if the href references a part in the multipart request, iterate over 
        # all parts and return the correct one 
        if url.scheme == "cid":
            for headers, data in mp.iterate(request):
                if headers.get("Content-ID") == url.path:
                    return data
            raise ReferenceException(
                "No part with content-id '%s'." % url.path
            )
        
        try:
            response = urllib2.urlopen()
        except:
            pass



class Reference(object):
    def __init__(self, href, headers, body, method, mime_type, encoding, schema):
        self.href = href
        self.headers = headers
        self.body = body
        self.method = method
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema

class ResponseForm(object):
    raw = False
    def __init__(self, outputs=None):
        self.outputs = outputs or ()

class RawResponse(ResponseForm):
    raw = True

class ResponseDocument(ResponseForm):
    pass


class AttributedValue(dict):
    def __init__(self, value, attributes):
        super(AttributedValue, self).__init__(attributes)
        self.value = value


def parse_complex_kvp(raw_string):
    key, _, raw_value_part = raw_string.partition("=")

    raw_value_items = raw_value_part.split("@")
    value = raw_value_items[0]

    return key, AttributedValue(value, [
        attribute.split("=")
        for attribute in raw_value_items[1:]
    ])


def parse_inputs_kvp(raw_string):

    kvps = []
    for kvp in raw_string.split(";"):
        key, value = parse_complex_kvp(kvp)

        if "href" in value or "xlink:href" in value:
            value = Reference(
                value.get("href") or value.get("xlink:href"),
                value.get("method"),
                value.get("mimeType"),
                value.get("encoding"),
                value.get("schema")
            )
        else:
            value = value.value

        kvps.append((key, value))

    return dict(kvps)


def parse_input_xml(element):
    name = element.xpath("ows:Identifier/text()", namespaces=nsmap)[0]
    data_elem = element.xpath("wps:Data/*[1]", namespaces=nsmap)[0]

    if data_elem.tag == ns_wps("Reference"):
        headers = dict(
            (header.attrib["key"], header.attrib["value"])
            for header in data_elem.xpath("wps:Header", namespaces=nsmap)
        )
        body = etree.tostring(data_elem.xpath("wps:Body")[0])
        # TODO: BodyReference?
        
        value = Reference(
            data_elem.attrib[ns_xlink("href")], headers, body,
            data_elem.attrib.get("method", "GET"),
            data_elem.attrib.get("mimeType"), data_elem.attrib.get("encoding"),
            data_elem.attrib.get("schema")
        )

    elif data_elem.tag == ns_wps("LiteralData"):
        value = data_elem.text

    elif data_elem.tag == ns_wps("BoundingBoxData"):
        # TODO: parse BBOX
        pass

    elif data_elem.tag == ns_wps("ComplexData"):
        value = data_elem[0]

    return name, value



def parse_response_document_kvp(value):
    return ResponseDocument()

def parse_raw_response_kvp(value):
    return RawResponse((value,))

def parse_response_form_xml(elem):
    if elem.tag == ns_wps("ResponseDocument"):
        return ResponseDocument(
            map(str, elem.xpath("wps:Output/ows:Identifier/text()", namespaces=nsmap))
        )


class WPS10ExecuteKVPDecoder(kvp.Decoder):
    identifier = kvp.Parameter()
    inputs = kvp.Parameter("DataInputs", type=parse_inputs_kvp, num="?", default={})

    response_document = kvp.Parameter("ResponseDocument", type=parse_response_document_kvp, num="?")
    raw_response = kvp.Parameter("RawDataOutput", type=parse_raw_response_kvp, num="?")

    @property
    def response_form(self):
        raw_response = self.raw_response
        if raw_response: 
            return raw_response

        return self.response_document or ResponseDocument()



class WPS10ExecuteXMLDecoder(xml.Decoder):
    identifier = xml.Parameter("ows:Identifier/text()")
    inputs_ = xml.Parameter("wps:DataInputs/wps:Input", type=parse_input_xml, num="*", default=[])

    response_form = xml.Parameter("wps:ResponseForm/*", type=parse_response_form_xml, num="?")

    @property
    def inputs(self):
        return dict(self.inputs_)

    namespaces = nsmap


class UnitMixIn(object):
    def __new__(cls, value, unit):
        obj = super(UnitMixIn, cls).__new__(cls, value)
        obj.unit = unit
        return obj

class UnitFloat(UnitMixIn, float):
    pass


class WPSExecuteParameters(object):
    @property
    def input_values(self):
        pass

    @property
    def output_definitions(self):
        pass



class ExampleProcess(Component):
    implements(ProcessInterface)

    identifier = "random"

    inputs = {
        "lower": float,
        "upper": float
    }

    outputs = {
        "value": float
    }


    def execute(self, lower, upper):
        import random

        return {
            "value": lower + random.random() * (upper - lower)
        }
