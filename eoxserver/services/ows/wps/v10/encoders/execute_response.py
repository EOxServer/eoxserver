#-------------------------------------------------------------------------------
#
# WPS 1.0 execute response XML encoder
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
#pylint: disable=too-many-arguments, missing-docstring, too-many-locals
#pylint: disable=bad-continuation

from lxml import etree
from django.utils.timezone import now
from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.ows.wps.v10.util import WPS, OWS, ns_xlink, ns_xml

from eoxserver.services.ows.wps.parameters import (
    Parameter, LiteralData, ComplexData, BoundingBoxData,
    fix_parameter, InputReference, Reference,
)

from .process_description import encode_process_brief
from .parameters import (
    encode_input_exec, encode_output_exec, encode_output_def
)
from .base import WPS10BaseXMLEncoder

from eoxserver.services.ows.wps.exceptions import InvalidOutputValueError

#-------------------------------------------------------------------------------

class WPS10ExecuteResponseXMLEncoder(WPS10BaseXMLEncoder):

    content_type = "application/xml; charset=utf-8"

    @staticmethod
    def encode_response(process, results, resp_form, inputs, raw_inputs,
                        status_location=None):
        """Encode execute response (SUCCESS) including the output data."""
        status = WPS(
            "ProcessSucceeded",
            "The processes execution completed successfully."
        )
        elem = _encode_common_response(
            process, status, inputs, raw_inputs, resp_form
        )
        if status_location:
            elem.set("statusLocation", status_location)

        outputs = []
        for result, prm, req in results.itervalues():
            outputs.append(_encode_output(result, prm, req))
        elem.append(WPS("ProcessOutputs", *outputs))

        return elem

    @staticmethod
    def encode_failed(process, exception, resp_form, inputs, raw_inputs,
                      status_location):
        """ Encode execute response for a running asynchronous job."""
        code = getattr(exception, "code", None)
        locator = getattr(exception, "locator", None)
        message = str(exception)

        if not code:
            code = "NoApplicableCode"
            locator = type(exception).__name__

        exc_attr = {"exceptionCode": code}
        if locator:
            exc_attr["locator"] = locator

        exc_elem = OWS("Exception", OWS("ExceptionText", message), **exc_attr)

        status = WPS("ProcessFailed", WPS("ExceptionReport", exc_elem))

        elem = _encode_common_response(
            process, status, inputs, raw_inputs, resp_form
        )
        if status_location:
            elem.set("statusLocation", status_location)

        return elem

    @staticmethod
    def encode_started(process, resp_form, inputs, raw_inputs, status_location,
                       progress=0):
        """ Encode execute response for a running asynchronous job."""
        status = WPS(
            "ProcessStarted", "The processes execution is in progress.",
            percentCompleted=("%d" % min(99, max(0, int(float(progress)))))
        )
        elem = _encode_common_response(
            process, status, inputs, raw_inputs, resp_form
        )
        if status_location:
            elem.set("statusLocation", status_location)

        return elem

    @staticmethod
    def encode_paused(process, resp_form, inputs, raw_inputs, status_location,
                      progress=0):
        """ Encode execute response for a paused asynchronous job."""
        status = WPS(
            "ProcessPaused", "The processes execution is paused.",
            percentCompleted=("%d" % min(99, max(0, int(float(progress)))))
        )
        elem = _encode_common_response(
            process, status, inputs, raw_inputs, resp_form
        )
        if status_location:
            elem.set("statusLocation", status_location)

        return elem

    @staticmethod
    def encode_accepted(process, resp_form, inputs, raw_inputs, status_location):
        """ Encode execute response for a successfully accepted asynchronous
        request.
        """
        status = WPS(
            "ProcessAccepted", "The processes was accepted for execution."
        )
        elem = _encode_common_response(
            process, status, inputs, raw_inputs, resp_form
        )
        if status_location:
            elem.set("statusLocation", status_location)

        return elem

#-------------------------------------------------------------------------------

def _encode_common_response(process, status_elem, inputs, raw_inputs, resp_doc):
    """Encode common execute response part shared by all specific responses."""
    conf = CapabilitiesConfigReader(get_eoxserver_config())
    url = conf.http_service_url
    dlm = "?" if url[-1] != "?" else ""
    elem = WPS("ExecuteResponse",
        encode_process_brief(process),
        WPS("Status", status_elem, creationTime=isoformat(now())),
        {
            "service": "WPS",
            "version": "1.0.0",
            ns_xml("lang"): "en-US",
            "serviceInstance": "%s%sservice=WPS&version=1.0.0&request="\
                               "GetCapabilities"%(url, dlm)
        },
    )

    if resp_doc.lineage:
        inputs_data = []
        for id_, prm in process.inputs:
            prm = fix_parameter(id_, prm)
            data = inputs.get(id_)
            rawinp = raw_inputs.get(prm.identifier)
            if rawinp is not None:
                inputs_data.append(_encode_input(data, prm, rawinp))
        elem.append(WPS("DataInputs", *inputs_data))

        outputs_def = []
        for id_, prm in process.outputs:
            prm = fix_parameter(id_, prm)
            outdef = resp_doc.get(prm.identifier)
            if outdef is not None:
                outputs_def.append(encode_output_def(outdef))
        elem.append(WPS("OutputDefinitions", *outputs_def))

    return elem


def _encode_input(data, prm, raw):
    elem = encode_input_exec(raw)

    if isinstance(raw, InputReference):
        elem.append(_encode_input_reference(raw))
    elif isinstance(prm, LiteralData):
        elem.append(WPS("Data", _encode_literal(data, prm, raw)))
    elif isinstance(prm, BoundingBoxData):
        elem.append(WPS("Data", _encode_bbox(data, prm)))
    elif isinstance(prm, ComplexData):
        elem.append(WPS("Data", _encode_complex(data, prm)))
    return elem


def _encode_output(data, prm, req):
    elem = encode_output_exec(Parameter(
        prm.identifier, req.title or prm.title, req.abstract or prm.abstract
    ))
    if isinstance(data, Reference):
        elem.append(_encode_output_reference(data, prm))
    elif isinstance(prm, LiteralData):
        elem.append(WPS("Data", _encode_literal(data, prm, req)))
    elif isinstance(prm, BoundingBoxData):
        elem.append(WPS("Data", _encode_bbox(data, prm)))
    elif isinstance(prm, ComplexData):
        elem.append(WPS("Data", _encode_complex(data, prm)))
    return elem


def _encode_input_reference(ref):
    #TODO proper input reference encoding
    return WPS("Reference", **{ns_xlink("href"): ref.href})


def _encode_output_reference(ref, prm):
    #TODO proper output reference encoding
    mime_type = getattr(ref, 'mime_type', None)
    encoding = getattr(ref, 'encoding', None)
    schema = getattr(ref, 'schema', None)
    if mime_type is None and hasattr(prm, 'default_format'):
        default_format = prm.default_format
        mime_type = default_format.mime_type
        encoding = default_format.encoding
        schema = default_format.schema

    attr = {
        #ns_xlink("href"): ref.href,
        'href': ref.href,
    }
    if mime_type:
        attr['mimeType'] = mime_type
    if encoding is not None:
        attr['encoding'] = encoding
    if schema is not None:
        attr['schema'] = schema

    return WPS("Reference", **attr)


def _encode_literal(data, prm, req):
    attrib = {'dataType': prm.dtype.name}
    uom = req.uom or prm.default_uom
    if prm.uoms:
        attrib['uom'] = uom
    try:
        encoded_data = prm.encode(data, uom)
    except (ValueError, TypeError) as exc:
        raise InvalidOutputValueError(prm.identifier, exc)
    return WPS("LiteralData", encoded_data, **attrib)


def _encode_bbox(data, prm):
    try:
        lower, upper, crs = prm.encode_xml(data)
    except (ValueError, TypeError) as exc:
        raise InvalidOutputValueError(prm.identifier, exc)

    return WPS("BoundingBoxData",
        OWS("LowerCorner", lower),
        OWS("UpperCorner", upper),
        crs=crs,
        #dimension="%d"%prm.dimension,
    )
    #NOTE: Although derived from OWS BoundingBox the WPS (schema) does not
    #      allow the dimenstion attribute.


def _encode_format_attr(data, prm):
    mime_type = getattr(data, 'mime_type', None)
    if mime_type is not None:
        encoding = getattr(data, 'encoding', None)
        schema = getattr(data, 'schema', None)
    else:
        deffrm = prm.default_format
        mime_type = deffrm.mime_type
        encoding = deffrm.encoding
        schema = deffrm.schema
    attr = {"mimeType": mime_type}
    if encoding is not None:
        attr['encoding'] = encoding
    if schema is not None:
        attr['schema'] = schema
    return attr


def _encode_complex(data, prm):
    try:
        payload = prm.encode_xml(data)
    except (ValueError, TypeError) as exc:
        raise InvalidOutputValueError(prm.identifier, exc)

    elem = WPS("ComplexData", **_encode_format_attr(data, prm))
    if isinstance(payload, etree._Element):
        elem.append(payload)
    else:
        elem.text = etree.CDATA(payload)
    return elem
