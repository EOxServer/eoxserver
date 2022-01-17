#-------------------------------------------------------------------------------
#
#  Execute - XML decoder
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

from lxml import etree
from eoxserver.core.decoders import xml
from eoxserver.services.ows.wps.exceptions import InvalidParameterValue
from eoxserver.services.ows.wps.parameters import (
    InputData, InputReference, Output, ResponseDocument, RawDataOutput
)
from eoxserver.services.ows.wps.v10.util import nsmap, ns_wps, ns_ows, ns_xlink
from eoxserver.services.ows.wps.v10.execute_decoder_common import (
    parse_bool,
)


def _parse_input(element):
    """ Parse one data input element. """
    id_ = element.findtext("./"+ns_ows("Identifier"))
    title = element.findtext("./"+ns_ows("Title"))
    abstract = element.findtext("./"+ns_ows("Abstract"))

    if id_ is None:
        raise ValueError("Missing the mandatory input identifier!")

    elem_ref = element.find("./"+ns_wps("Reference"))
    elem_data = element.find("./"+ns_wps("Data"))

    if elem_ref is not None:
        value = _parse_input_reference(elem_ref, id_, title, abstract)

    elif elem_data is not None:
        if len(elem_data) != 1:
            raise ValueError("Invalid input content of the 'wps:Data' element!")
        value = _parse_input_data(elem_data[0], id_, title, abstract)

    else:
        raise ValueError(
            "Neither 'wps:Data' nor 'wps:Reference' element provided!"
        )

    return id_, value


def _parse_response_form(elem_rform):
    """ Parse ResponseForm element holding either ResponseDocument or
    RawDataOutput elements.
    """
    elem_rdoc = elem_rform.find("./"+ns_wps("ResponseDocument"))
    if elem_rdoc is not None:
        rdoc = ResponseDocument(
            lineage=parse_bool(elem_rdoc.attrib.get("lineage")),
            status=parse_bool(elem_rdoc.attrib.get("status")),
            store_response=parse_bool(
                elem_rdoc.attrib.get("storeExecuteResponse")
            ),
        )
        for elem in elem_rdoc.iterfind("./"+ns_wps("Output")):
            id_ = elem.findtext(ns_ows("Identifier"))
            title = elem.findtext(ns_ows("Title"))
            abstr = elem.findtext(ns_ows("Abstract"))
            rdoc.set_output(_create_output(id_, elem.attrib, title, abstr))
        return rdoc

    elem_rawout = elem_rform.find("./"+ns_wps("RawDataOutput"))
    if elem_rawout is not None:
        id_ = elem_rawout.findtext(ns_ows("Identifier"))
        return RawDataOutput(_create_output(id_, elem_rawout.attrib))

    raise InvalidParameterValue('Invalid ResponseForm!', 'ResponseForm')


def _parse_input_reference(elem, identifier, title, abstract):
    """ Parse one input item passed as a reference. """
    href = elem.attrib.get(ns_xlink("href"))
    if href is None:
        raise ValueError("Missing the mandatory 'xlink:href' attribute!")

    body = elem.findtext("./"+ns_wps("Body"))
    elem_tmp = elem.find("./"+ns_wps("BodyReference"))
    body_href = elem_tmp.attrib.get(ns_xlink("href")) if elem_tmp else None

    headers = dict(
        (header.attrib["key"], header.attrib["value"])
        for header in elem.iterfind("./"+ns_wps("Header"))
    )

    return InputReference(
        identifier, title, abstract,
        href, headers, body,
        elem.attrib.get("method", "GET"),
        elem.attrib.get("mimeType"),
        elem.attrib.get("encoding"),
        elem.attrib.get("schema"),
        body_href,
    )


def _parse_input_data(elem, identifier, title, abstract):
    """ Parse one input item value. """
    if elem.tag == ns_wps("LiteralData"):
        args = _parse_input_literal(elem)
    elif elem.tag == ns_wps("BoundingBoxData"):
        args = _parse_input_bbox(elem)
    elif elem.tag == ns_wps("ComplexData"):
        args = _parse_input_complex(elem)
    else:
        raise ValueError("Invalid input content of the 'wps:Data' element!")
    return InputData(
        identifier=identifier, title=title, abstract=abstract, **args
    )


def _parse_input_literal(elem):
    """ Parse one literal data input item value. """
    args = {}
    args['data'] = elem.text or ""
    args['uom'] = elem.attrib.get("uom")
    return args


def _parse_input_bbox(elem):
    """ Parse one bounding-box input item value. """
    args = {}
    lower_corner = elem.findtext("./"+ns_ows("LowerCorner"))
    upper_corner = elem.findtext("./"+ns_ows("UpperCorner"))
    if lower_corner is None or upper_corner is None:
        raise ValueError("Invalid 'wps:BoundingBoxData' element!")
    args['data'] = (lower_corner, upper_corner, elem.attrib.get("crs"))
    return args


def _parse_input_complex(elem):
    """ Parse one complex data input item value. """
    args = {}
    if len(elem):
        args['data'] = etree.tostring(
            elem[0], pretty_print=False, xml_declaration=True, encoding="utf-8"
        )
    else:
        args['data'] = elem.text or ""
    args['mime_type'] = elem.attrib.get("mimeType")
    args['encoding'] = elem.attrib.get("encoding")
    args['schema'] = elem.attrib.get("schema")
    return args


def _create_output(identifier, attrs, title=None, abstract=None):
    """ Create one Output object.from the parsed id and attributes. """
    return Output(
        identifier, title, abstract, attrs.get("uom"),
        attrs.get("crs"), attrs.get("mimeType"), attrs.get("encoding"),
        attrs.get("schema"), parse_bool(attrs.get("asReference"))
    )


class WPS10ExecuteXMLDecoder(xml.Decoder):
    """ WPS 1.0 POST/XML Execute request decoder class. """
    namespaces = nsmap
    identifier = xml.Parameter("ows:Identifier/text()")

    @property
    def inputs(self):
        """ Get the raw data inputs as a dictionary. """
        return dict(self._inputs)

    @property
    def response_form(self):
        """ Get the unified response form object. """
        resp_form = self._response_form
        return resp_form if resp_form is not None else ResponseDocument()

    _inputs = xml.Parameter(
        "wps:DataInputs/wps:Input", type=_parse_input, num="*", default=[]
    )
    _response_form = xml.Parameter(
        "wps:ResponseForm", type=_parse_response_form, num="?"
    )
