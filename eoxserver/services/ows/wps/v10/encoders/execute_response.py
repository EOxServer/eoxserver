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
from .parameters import encode_output_def
from .base import WPS10BaseXMLEncoder


# TODO: move data encoding to a separate module
#def encode_input( ... ):
def encode_output(name, parameter, data):
    #TODO: proper output encoding
    elem = encode_output_def(name, parameter)
    elem.append(WPS("Data", WPS("LiteralData", str(data))))
    return elem

def _encode_response(process, inputs, status_elem, lineage):
    """Encode common execute response part shared by all specific responses."""
    elem = WPS("ExecuteResponse",
        encode_process_brief(process),
        WPS("Status", status_elem, creationTime=isoformat(now()))
    )
    if lineage:
        inputs_enc = [] # TODO: encoded inputs
        elem.append(WPS("DataInputs", *inputs_enc))
        elem.append(WPS("OutputDefinitions",
            *(encode_output_def(n, p) for n, p in process.outputs.items())
        ))
    return elem


class WPS10ExecuteResponseXMLEncoder(WPS10BaseXMLEncoder):

    @staticmethod
    def encode_execute_response(process, inputs, results, lineage=False):
        """Encode execute response (SUCCESS) including the output data."""
        status = WPS("ProcessSucceded")
        elem = _encode_response(process, inputs, status, lineage)
        elem.append(WPS("ProcessOutputs",
            *(encode_output(n, process.outputs[n], d) for n, d in results.items())
        ))
        return elem

    #@staticmethod
    #def encode_execute_failure(process, inputs, results, lineage=False):

    #@staticmethod
    #def encode_execute_progress(process, inputs, results, lineage=False):

    #@staticmethod
    #def encode_execute_async(process, inputs, results, lineage=False):
