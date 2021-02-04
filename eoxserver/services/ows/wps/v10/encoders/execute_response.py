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
#pylint: disable=too-many-arguments, too-many-locals, bad-continuation

from lxml import etree
from django.utils.timezone import now
from django.utils.six import itervalues

from eoxserver.core.config import get_eoxserver_config
from eoxserver.services.ows.common.config import CapabilitiesConfigReader
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.ows.wps.v10.util import WPS, OWS, ns_xlink, ns_xml

from eoxserver.services.ows.wps.exceptions import OWS10Exception
from eoxserver.services.ows.wps.parameters import (
    Parameter, LiteralData, ComplexData, BoundingBoxData,
    fix_parameter, InputReference, Reference, RequestParameter,
)

from .process_description import encode_process_brief
from .parameters import (
    encode_input_exec, encode_output_exec, encode_output_def
)
from .base import WPS10BaseXMLEncoder
from eoxserver.services.ows.wps.exceptions import InvalidOutputValueError


class WPS10ExecuteResponseXMLEncoder(WPS10BaseXMLEncoder):
    """ WPS 1.0 ExecuteResponse XML response encoder. """

    def __init__(self, process, resp_form, raw_inputs, inputs=None,
                 status_location=None):
        super(WPS10ExecuteResponseXMLEncoder, self).__init__()
        self.process = process
        self.resp_form = resp_form
        self.raw_inputs = raw_inputs
        self.inputs = inputs
        self.status_location = status_location

    def _encode_common(self, status):
        """ Encode common response element. """
        elem = _encode_common_response(
            self.process, status, self.inputs, self.raw_inputs, self.resp_form
        )
        if self.status_location:
            elem.set("statusLocation", self.status_location)
        return elem

    def encode_response(self, results):
        """Encode ProcessSucceeded execute response including the output data."""
        elem = self._encode_common(WPS(
            "ProcessSucceeded",
            "The processes execution completed successfully."
        ))
        outputs = []
        for result, prm, req in itervalues(results):
            outputs.append(_encode_output(result, prm, req))
        elem.append(WPS("ProcessOutputs", *outputs))
        return elem

    def encode_failed(self, exception):
        """ Encode ProcessFailed execute response."""
        # NOTE: Some exceptions such as the urllib2.HTTPError have also
        # the 'code' attribute and the duck typing does not work very well.
        # Therefore we need match the exception base type.
        if isinstance(exception, OWS10Exception):
            code = exception.code
            locator = exception.locator
        else:
            code = "NoApplicableCode"
            locator = type(exception).__name__
        message = str(exception)
        exc_attr = {"exceptionCode": str(code)}
        if locator:
            exc_attr["locator"] = str(locator)
        exc_elem = OWS("Exception", OWS("ExceptionText", message), **exc_attr)
        status = WPS("ProcessFailed", WPS("ExceptionReport", exc_elem))
        return self._encode_common(status)

    def encode_started(self, progress=0, message=None):
        """ Encode ProcessStarted execute response."""
        if not message:
            message = "The processes execution is in progress."
        return self._encode_common(WPS(
            "ProcessStarted", message,
            percentCompleted=("%d" % min(99, max(0, int(float(progress)))))
        ))

    def encode_paused(self, progress=0):
        """ Encode ProcessPaused execute response."""
        return self._encode_common(WPS(
            "ProcessPaused", "The processes execution is paused.",
            percentCompleted=("%d" % min(99, max(0, int(float(progress)))))
        ))

    def encode_accepted(self):
        """ Encode ProcessAccepted execute response."""
        return self._encode_common(WPS(
            "ProcessAccepted", "The processes was accepted for execution."
        ))

#-------------------------------------------------------------------------------

def _encode_common_response(process, status_elem, inputs, raw_inputs, resp_doc):
    """Encode common execute response part shared by all specific responses."""
    inputs = inputs or {}
    conf = CapabilitiesConfigReader(get_eoxserver_config())
    url = conf.http_service_url
    if url[-1] == "?":
        url = url[:-1]
    elem = WPS("ExecuteResponse",
        encode_process_brief(process),
        WPS("Status", status_elem, creationTime=isoformat(now())),
        {
            "service": "WPS",
            "version": "1.0.0",
            ns_xml("lang"): "en-US",
            "serviceInstance": (
                "%s?service=WPS&version=1.0.0&request=GetCapabilities" % url
            )
        },
    )

    if resp_doc.lineage:
        inputs_data = []
        for id_, prm in process.inputs:
            if isinstance(prm, RequestParameter):
                continue
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
    """ Encode one DataInputs sub-element. """
    elem = encode_input_exec(raw)
    if isinstance(raw, InputReference):
        elem.append(_encode_input_reference(raw))
    elif isinstance(prm, LiteralData):
        elem.append(WPS("Data", _encode_raw_input_literal(raw, prm)))
    elif isinstance(prm, BoundingBoxData):
        if data is None:
            data = prm.parse(raw.data)
        elem.append(WPS("Data", _encode_bbox(data, prm)))
    elif isinstance(prm, ComplexData):
        if data is None:
            data = prm.parse(
                data=raw.data, mime_type=raw.mime_type, encoding=raw.encoding,
                schema=raw.schema
            )
        elem.append(WPS("Data", _encode_complex(data, prm)))
    return elem


def _encode_output(data, prm, req):
    """ Encode one ProcessOutputs sub-element. """
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
    """ Encode DataInputs/Reference element. """
    #TODO proper input reference encoding
    return WPS("Reference", **{ns_xlink("href"): ref.href})


def _encode_output_reference(ref, prm):
    """ Encode ProcessOutputs/Reference element. """
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


def _encode_raw_input_literal(input_raw, prm):
    """ Encode Data/LiteralData element from a raw (unparsed) input ."""
    attrib = {'dataType': prm.dtype.name}
    uom = input_raw.uom or prm.default_uom
    if prm.uoms:
        attrib['uom'] = uom
    return WPS("LiteralData", input_raw.data, **attrib)


def _encode_literal(data, prm, req):
    """ Encode Data/LiteralData element. """
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
    """ Encode Data/BoundingBoxData element. """
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
    #      allow the dimension attribute.


def _encode_format_attr(data, prm):
    """ Get format attributes of the Data/ComplexData element. """
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
    """ Encode Data/ComplexData element. """
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
