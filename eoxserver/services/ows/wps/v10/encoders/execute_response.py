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

from django.utils.timezone import now
from eoxserver.core.util.timetools import isoformat
from eoxserver.services.ows.wps.v10.util import (
    OWS, WPS, ns_ows, ns_wps, ns_xlink, ns_xml
)

from .process_description import encode_process_brief
from .parameters import (Parameter, fix_parameter,
    LiteralData, BoundingBoxData, ComplexData,
    encode_input_exec, encode_output_exec,)
from .base import WPS10BaseXMLEncoder


# TODO: move low-level data encoding to a separate module
def _encode_literal(prm, data):
    attrib = { 'dataType': prm.dtype.name }
    if prm.uoms:
        #NOTE: If applicable the default UOM is inserted.
        attrib['uom'] = prm.uoms[0]
    return WPS("LiteralData", unicode(data), **attrib)

def _encode_bbox(prm, data):
    #TODO: proper output encoding
    return WPS("BoundingBoxData")

def _encode_complex(prm, data):
    #TODO: proper output encoding
    return WPS("ComplexData")

def _encode_output(prm, data):
    elem = encode_input_exec(prm.identifier, prm)

    if isinstance(prm, LiteralData):
        elem.append(WPS("Data", _encode_literal(prm, data)))
    if isinstance(prm, BoundingBoxData):
        elem.append(WPS("Data", _encode_bbox(prm, data)))
    if isinstance(prm, ComplexData):
        elem.append(WPS("Data", _encode_complex(prm, data)))

    return elem

def _encode_response(process, inputs, status_elem, lineage):
    """Encode common execute response part shared by all specific responses."""
    elem = WPS("ExecuteResponse",
        encode_process_brief(process),
        WPS("Status", status_elem, creationTime=isoformat(now()))
    )

    if lineage:
        #TODO: proper lineage output
        inputs_data = [encode_output_exec(n, p) for n, p in process.inputs]
        outputs_def = [encode_output_exec(n, p) for n, p in process.outputs]
        elem.append(WPS("DataInputs", *inputs_data))
        elem.append(WPS("OutputDefinitions", *outputs_def))

    return elem


class WPS10ExecuteResponseXMLEncoder(WPS10BaseXMLEncoder):

    @staticmethod
    def encode_execute_response(process, inputs, results, lineage=False):
        """Encode execute response (SUCCESS) including the output data."""
        status = WPS("ProcessSucceded")
        elem = _encode_response(process, inputs, status, lineage)

        outputs = []
        for name, prm in process.outputs: # preserve order of the outputs
            prm = fix_parameter(name, prm) # short-hand def. expansion
            result = results.get(prm.identifier, None)
            if results: # skip missing outputs
                outputs.append(_encode_output(prm, result))
        elem.append(WPS("ProcessOutputs", *outputs))

        return elem

    #@staticmethod
    #def encode_execute_failure(process, inputs, results, lineage=False):

    #@staticmethod
    #def encode_execute_progress(process, inputs, results, lineage=False):

    #@staticmethod
    #def encode_execute_async(process, inputs, results, lineage=False):
