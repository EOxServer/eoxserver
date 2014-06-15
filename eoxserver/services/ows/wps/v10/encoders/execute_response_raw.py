#-------------------------------------------------------------------------------
#
# WPS 1.0 execute response raw encoder
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

from eoxserver.services.result import (
    to_http_response, ResultBuffer, #ResultFile,
)
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, BoundingBoxData,
)

#-------------------------------------------------------------------------------

class WPS10ExecuteResponseRawEncoder(object):

    @staticmethod
    def serialize(result_items):
        return to_http_response(result_items)

    def __init__(self):
        self.content_type = None

    def encode_response(self, process, results, resp_form, inputs, raw_inputs):
        """Pack the raw execute response."""
        outputs = []
        for data, prm, req in results.itervalues():
            if prm.identifier in resp_form:
                outputs.append(_encode_raw_output(data, prm, req))

        if len(outputs) == 1:
            self.content_type = outputs[0].content_type
        else:
            self.content_type = "multipart/related"

        return outputs

#-------------------------------------------------------------------------------

def _encode_raw_output(data, prm, req):
    """ Encode single raw output item."""
    if isinstance(prm, LiteralData):
        return _encode_raw_literal(data, prm, req)
    elif isinstance(prm, BoundingBoxData):
        return _encode_raw_bbox(data, prm, req)
    elif isinstance(prm, ComplexData):
        return _encode_raw_complex(data, prm, req)
    raise TypeError("Invalid output type! %r"%(prm))

def _encode_raw_literal(data, prm, req):
    """ Encode single raw literal."""
    return ResultBuffer(prm.encode(data, req.uom or prm.default_uom, 'utf8'),
        content_type="text/plain" if req.mime_type is None else req.mime_type,
        identifier=prm.identifier)

def _encode_raw_bbox(data, prm, req):
    """ Encode single raw bounding box."""
    #TODO: proper output encoding
    return None

def _encode_raw_complex(data, prm, req):
    #TODO: proper output encoding
    """ Encode single raw complex data."""
    return None

