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
    fix_parameter, Parameter, LiteralData, BoundingBoxData, ComplexData
)
from eoxserver.services.ows.wps.exceptions import (
    NoSuchProcessException, MissingInputException,
    InvalidReferenceException,
)
from eoxserver.services.ows.wps.v10.util import nsmap, ns_wps, ns_ows, ns_xlink
from eoxserver.services.ows.wps.v10.encoders import (
    WPS10ExecuteResponseXMLEncoder, WPS10ExecuteResponseRawEncoder
)


def _normalize_results(output_defs, results):
    """Convert result to a common form."""
    if isinstance(results, dict):
        return results
    elif len(output_defs) == 1:
        return {output_defs[0][0]: results}
    else:
        try:
            return dict(results)
        except ValueError:
            raise ValueError("Failed to convert the results to a dictionary!")

def _resolve_reference(reference, request):
    """ Get the input passed as a reference. """
    url = urlparse(reference.href)

    # if the href references a part in the multipart request, iterate over
    # all parts and return the correct one
    if url.scheme == "cid":
        for headers, data in mp.iterate(request):
            if headers.get("Content-ID") == url.path:
                return data
        raise InvalidReferenceException(
            "No part with content-id '%s'." % url.path
        )

    try:
        request = urllib2.Request(reference.href, reference.body)
        response = urllib2.urlopen(request)
        return response.read()
    except urllib2.URLError, e:
        raise InvalidReferenceException(str(e))


def decode_process_inputs(process, decoder, request):
    """ Iterates over all input options stated in the process and parses
        all given inputs. This also includes resolving references
    """
    inputs = decoder.inputs

    #TODO: remove followin backward compatibility conversion
    if isinstance(process.inputs, dict):
        process.inputs = process.inputs.items()
    input_defs = process.inputs

    decoded_inputs = {}
    for name, prm in input_defs:
        prm = fix_parameter(name, prm) # short-hand def. expansion
        try:
            # get the "raw" input value
            raw_value = inputs.pop(prm.identifier)
            if isinstance(raw_value, Reference):
                value = _resolve_reference(raw_value, request)
            else:
                value = prm.dtype.parse(raw_value)
        except KeyError:
            if prm.is_optional:
                value = None
                if isinstance(prm, LiteralData):
                    value = prm.default
                # TODO: defaults for non-literal types
            else:
                raise MissingInputException("Input '%s' is required."%name)
        decoded_inputs[name] = value
    return decoded_inputs


def encode_process_outputs(process, decoder, results):
    resp_form = decoder.response_form or ResponseDocument()

    #TODO: remove followin backward compatibility conversion
    if isinstance(process.outputs, dict):
        process.outputs = process.outputs.items()
    output_defs = process.outputs

    results = _normalize_results(output_defs, results)

    encoded_results = {}
    for name, prm in output_defs:
        prm = fix_parameter(name, prm) # short-hand def. expansion

        # Don't encode outputs if not requested by the response form.
        if resp_form and not resp_form.is_output_included(prm.identifier):
            continue

        # TODO: check stadard to get the proper behaviour
        # skip mising outputs
        result = results.get(name, None)
        if result is None:
            continue

        encoded_result = resp_form.encode(process, prm, result)
        encoded_results[prm.identifier] = encoded_result

    if not resp_form.raw:
        encoder = WPS10ExecuteResponseXMLEncoder()
    else:
        encoder = WPS10ExecuteResponseRawEncoder(results)

    return encoder.serialize(
        encoder.encode_execute_response(
            process, decoder.inputs, encoded_results,
            getattr(resp_form, "lineage", False)
        )
    ), encoder.content_type



class WPS10ExcecuteHandler(Component):
    implements(ServiceHandlerInterface)
    implements(GetServiceHandlerInterface)
    implements(PostServiceHandlerInterface)

    service = "WPS"
    versions = ("1.0.0",)
    request = "Execute"

    processes = ExtensionPoint(ProcessInterface)
    #result_storage = ExtensionPoint(ResultStorageInterface)


    @staticmethod
    def get_decoder(request):
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

        for item in self.processes:
            if item.identifier == decoder.identifier:
                process = item
                break
        else:
            raise NoSuchProcessException(decoder.identifier)

        kwargs = decode_process_inputs(process, decoder, request)

        # TODO: exception catching + proper error execute response generation
        # execute the process and prepare the result
        result = process.execute(**kwargs)

        return encode_process_outputs(process, decoder, result)



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

    def __init__(self, output_options=None):
        self.output_options = output_options or {}

    def is_output_included(self, output_identifier):
        if not self.output_options or output_identifier in self.output_options:
            return True
        return False


    def encode(self, process, parameter, raw_result):
        if isinstance(parameter, LiteralData):
            if parameter.check(raw_result):
                return parameter.encode(raw_result)
            else:
                raise ValueError("Invalid output '%s'!"%parameter.identifier)

        elif isinstance(parameter, ComplexData):
            # get the requested format encoding or use the default

            frmt = self._get_selected_format(
                parameter.identifier, parameter.formats
            )

            # try this order: use formats encoding function, use processes
            # encoding function

            try:
                return frmt.encode_data(raw_result)
            except NotImplementedError:
                return process.encode_complex_output(
                    parameter.identifier, raw_result,
                    frmt.mime_type, frmt.encoding, frmt.schema
                )

    def _get_selected_format(self, output_identifier, formats):
        options = output_options.get(output_identifier)
        mime_type = options.get("mime_type")

        # first make a "strict" iteration
        for frmt in formats:
            if frmt.mime_type == mime_type:
                return mime_type

        # return the default, the first format
        return formats[0]


class RawDataOutput(ResponseForm):
    raw = True

class ResponseDocument(ResponseForm):
    def __init__(self, output_options=None, lineage=False):
        super(ResponseDocument, self).__init__(output_options)
        self.lineage = lineage


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


def parse_output(attrs):
    return {
        "reference": attrs.get("asReference") == "true",
        "uom": attrs.get("uom"),
        "mime_type": attrs.get("mimeType"),
        "encoding": attrs.get("encoding"),
        "schema": attrs.get("schema")
    }

def parse_response_document_kvp(raw_string):
    outputs = {}
    for kvp in raw_string.split(";"):
        key, value = parse_complex_kvp(kvp)
        outputs[key] = parse_output(value)

    return ResponseDocument(outputs)


def parse_raw_response_kvp(raw_string):
    key, value = parse_complex_kvp(raw_string)
    return RawResponse({key: parse_output(value)})


def parse_response_form_xml(elem):
    if elem.tag == ns_wps("ResponseDocument"):
        outputs = {}
        for output_elem in elem.xpath("wps:Output", namespaces=nsmap):
            identifier = output_elem.findtext(ns_ows("Identifier"))
            outputs[identifier] = parse_output(output_elem.attrib)

        return ResponseDocument(
            outputs, elem.attrib.get("lineage") == "true"
        )
    elif elem.tag == ns_wps("RawDataOutput"):
        return RawDataOutput(
            {elem.findtext(ns_ows("Identifier")): parse_output(elem.attrib)}
        )

    raise


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

