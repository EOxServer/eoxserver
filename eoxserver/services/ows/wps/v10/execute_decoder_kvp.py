#-------------------------------------------------------------------------------
#
#  Execute - KVP decoder
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


import urllib
from eoxserver.core.decoders import kvp

from eoxserver.services.ows.wps.parameters import (
    InputData, InputReference, Output, ResponseDocument, RawDataOutput
)

def _parse_inputs(raw_string):
    inputs = {}
    for item in raw_string.split(";"):
        id_, value, param = _parse_param(item)
        href = param.get("href") or param.get("xlink:href")
        if href is not None:
            input_ = InputReference(
                href=href,
                identifier=id_,
                mime_type=param.get("mimeType"),
                encoding=param.get("encoding"),
                schema=param.get("schema")
            )
        else:
            #NOTE: KVP Bounding box cannot be safely detected and parsed.
            input_ = InputData(
                identifier=id_,
                data=value,
                uom=param.get("uom"),
                mime_type=param.get("mimeType"),
                encoding=param.get("encoding"),
                schema=param.get("schema"),
                asurl=True,
            )
        inputs[id_] = input_
    return inputs

def _parse_param(raw_string):
    items = (item.partition('=') for item in raw_string.split("@"))
    attr = {}
    id_, dlm, data = items.next()
    data = urllib.unquote_plus(data) if dlm else None
    for key, dlm, val in items:
        if dlm:
            attr[urllib.unquote_plus(key)] = urllib.unquote_plus(val)
    return id_, data, attr


def _parse_outputs(raw_string):
    outputs = []
    for output in raw_string.split(";"):
        outputs.append(_create_output(*_parse_param(output)))
    return outputs


def _parse_raw_output(raw_string):
    return RawDataOutput(_create_output(*_parse_param(raw_string)))


def _parse_bool(raw_string):
    return raw_string == 'true'


def _create_output(identifier, _, attrs):
    attr_as_reference = False
    #attr_as_reference = attrs.get("asReference")
    #if attr_as_reference is not None:
    #    attr_as_reference = attr_as_reference == true

    return Output(identifier, None, None, attrs.get("uom"),
            attrs.get("crs"), attrs.get("mimeType"), attrs.get("encoding"),
            attrs.get("schema"), attr_as_reference)


class WPS10ExecuteKVPDecoder(kvp.Decoder):
    identifier = kvp.Parameter()
    inputs = kvp.Parameter("DataInputs", type=_parse_inputs, num="?", default={})
    outputs = kvp.Parameter("ResponseDocument", type=_parse_outputs, num="?", default=[])
    raw_response = kvp.Parameter("RawDataOutput", type=_parse_raw_output, num="?")
    status = kvp.Parameter("status", type=_parse_bool, num="?", default=False)
    lineage = kvp.Parameter("lineage", type=_parse_bool, num="?", default=False)
    store_response = kvp.Parameter("storeExecuteResponse= ", type=_parse_bool, num="?", default=False)

    @property
    def response_form(self):
        raw_response = self.raw_response
        if raw_response:
            return raw_response

        resp_doc = ResponseDocument(
            lineage=self.lineage,
            status=self.status,
            store_response=self.store_response
        )
        for output in self.outputs:
            resp_doc.set_output(output)
        return resp_doc

