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

from django.utils.six.moves.urllib.parse import unquote_plus

from eoxserver.core.decoders import kvp
from eoxserver.services.ows.wps.parameters import (
    InputData, InputReference, Output, ResponseDocument, RawDataOutput
)
from eoxserver.services.ows.wps.v10.execute_decoder_common import (
    parse_bool,
)


def _parse_inputs(raw_string):
    """ Parse DataInputs value. """
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
                data=value,
                identifier=id_,
                uom=param.get("uom"),
                mime_type=param.get("mimeType"),
                encoding=param.get("encoding"),
                schema=param.get("schema"),
                asurl=True,
            )
        inputs[id_] = input_
    return inputs


def _parse_param(raw_string):
    """ Parse one input or output item. """
    items = (item.partition('=') for item in raw_string.split("@"))
    attr = {}
    id_, dlm, data = next(items)
    id_ = unquote_plus(id_)
    data = unquote_plus(data) if dlm else None
    for key, dlm, value in items:
        attr[unquote_plus(key)] = unquote_plus(value) if dlm else None
    return id_, data, attr


def _parse_outputs(raw_string):
    """ Parse ResponseDocument parameter. """
    return [
        _create_output(*_parse_param(output))
        for output in raw_string.split(";")
    ]


def _parse_raw_output(raw_string):
    """ Parse RawDataOutput parameter. """
    return RawDataOutput(_create_output(*_parse_param(raw_string)))


def _create_output(identifier, _, attrs):
    """ Create one Output object from the parsed identifier and attributes. """
    return Output(
        identifier, None, None, attrs.get("uom"),
        attrs.get("crs"), attrs.get("mimeType"), attrs.get("encoding"),
        attrs.get("schema"), parse_bool(attrs.get("asReference"))
    )


def parse_query_string(query_string):
    """ Parse URL query string preserving the URL-encoded
    DataInputs, ResponseDocument, and RawDataOutput WPS Execute parameters.
    Note that the standard parser URL-decodes the parameter values and, in cases
    when, e.g., a data input contains an percent-encoded separator
    ('%40' vs. '@') the encoded and non-encoded delimiters cannot
    be distinguished ('@' vs. '@') and the correct parsing cannot be guaranteed.
    """
    unescaped = set(('datainputs', 'responsedocument', 'rawdataoutput'))
    return dict(
        (key, value if key.lower() in unescaped else unquote_plus(value))
        for key, value in (
            (unquote_plus(key), value) for key, _, value in (
                item.partition('=') for item in query_string.split('&')
            )
        )
    )


class WPS10ExecuteKVPDecoder(kvp.Decoder):
    """ WPS 1.0 Execute HTTP/GET KVP request decoder. """
    #pylint: disable=too-few-public-methods
    identifier = kvp.Parameter()

    @property
    def inputs(self):
        """ Get the raw data inputs as a dictionary. """
        return self._inputs or {}

    @property
    def response_form(self):
        """ Get response unified form parsed either from ResponseDocument or
        RawDataOutput parameters.
        """
        raw_response = self._raw_response
        if raw_response:
            return raw_response

        resp_doc = ResponseDocument(
            lineage=self._lineage,
            status=self._status,
            store_response=self._store_response
        )
        for output in self._outputs: # pylint: disable=not-an-iterable
            resp_doc.set_output(output)
        return resp_doc


    _inputs = kvp.Parameter("DataInputs", type=_parse_inputs, num="?")
    _outputs = kvp.Parameter(
        "ResponseDocument", type=_parse_outputs, num="?", default=()
    )
    _raw_response = kvp.Parameter(
        "RawDataOutput", type=_parse_raw_output, num="?"
    )
    _status = kvp.Parameter(
        "status", type=parse_bool, num="?", default=False
    )
    _lineage = kvp.Parameter(
        "lineage", type=parse_bool, num="?", default=False
    )
    _store_response = kvp.Parameter(
        "storeExecuteResponse", type=parse_bool, num="?", default=False
    )
