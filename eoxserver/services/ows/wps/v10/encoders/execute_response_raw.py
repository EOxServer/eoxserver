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

import types
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from eoxserver.services.result import (
    to_http_response, ResultItem,
)
from eoxserver.services.ows.wps.parameters import (
    LiteralData, ComplexData, BoundingBoxData,
)
from eoxserver.services.ows.wps.exceptions import InvalidOutputValueError
from django.utils.six import string_types, itervalues


class WPS10ExecuteResponseRawEncoder(object):
    """ WPS 1.0 raw output Execute response encoder. """

    @staticmethod
    def serialize(result_items, **kwargs):
        """ Serialize the result items to the HTTP response object. """
        # pylint: disable=unused-argument
        return to_http_response(result_items)

    def __init__(self, resp_form):
        self.content_type = None
        self.resp_form = resp_form

    def encode_response(self, results):
        """Pack the raw execute response."""
        outputs = []
        for data, prm, req in itervalues(results):
            if prm.identifier in self.resp_form:
                outputs.append(_encode_raw_output(data, prm, req))

        if len(outputs) == 1:
            self.content_type = outputs[0].content_type
        else:
            self.content_type = "multipart/related"

        return outputs

#-------------------------------------------------------------------------------

class ResultAlt(ResultItem):
    """ Alternative implementation of the result buffer. The object can be
    initialized with a byte-string, sequence or generator of byte-strings,
    or seekable file(-like) object.
    """

    def __init__(self, buf, content_type=None, filename=None, identifier=None,
                 close=False, headers=None):
        # pylint: disable=too-many-arguments
        ResultItem.__init__(self, content_type, filename, identifier)
        if isinstance(buf, string_types) or isinstance(buf, bytes):
            self._file = StringIO(buf.decode('utf-8'))  # make sure a byte string is passed
        elif isinstance(buf, (tuple, list, types.GeneratorType)):
            tmp = StringIO()
            for chunk in buf:
                tmp.write(chunk)
            self._file = tmp
        else:
            self._file = buf
        self._close = close
        self.headers = headers or []

    def __del__(self):
        if self._close:
            self._file.close()

    def __len__(self):
        self._file.seek(0, 2)
        return self._file.tell()

    @property
    def data_file(self):
        self._file.seek(0)
        return self._file

    @property
    def data(self):
        return self.data_file.read()

    def chunked(self, chunksize):
        if chunksize < 0:
            raise ValueError("Invalid chunk-size %d!" % chunksize)
        data_file = self.data_file
        for chunk in iter(lambda: data_file.read(chunksize), ''):
            yield chunk

#-------------------------------------------------------------------------------


def _encode_raw_output(data, prm, req):
    """ Encode a raw output item."""
    if isinstance(prm, LiteralData):
        return _encode_raw_literal(data, prm, req)
    elif isinstance(prm, BoundingBoxData):
        return _encode_raw_bbox(data, prm, req)
    elif isinstance(prm, ComplexData):
        return _encode_raw_complex(data, prm)
    raise TypeError("Invalid output type! %r"%(prm))


def _encode_raw_literal(data, prm, req):
    """ Encode a raw literal."""
    content_type = "text/plain" if req.mime_type is None else req.mime_type
    content_type = "%s; charset=utf-8" % content_type
    try:
        encoded_data = prm.encode(data, req.uom or prm.default_uom, 'utf-8')
    except (ValueError, TypeError) as exc:
        raise InvalidOutputValueError(prm.identifier, exc)
    return ResultAlt(
        encoded_data, identifier=prm.identifier, content_type=content_type
    )


def _encode_raw_bbox(data, prm, req):
    """ Encode a raw bounding box."""
    content_type = "text/plain" if req.mime_type is None else req.mime_type
    content_type = "%s; charset=utf-8"%content_type
    try:
        encoded_data = prm.encode_kvp(data).encode('utf-8')
    except (ValueError, TypeError) as exc:
        raise InvalidOutputValueError(prm.identifier, exc)
    return ResultAlt(
        encoded_data, identifier=prm.identifier,
        content_type="text/plain" if req.mime_type is None else req.mime_type
    )


def _encode_raw_complex(data, prm):
    """ Encode raw complex data."""
    payload, content_type = prm.encode_raw(data)
    return ResultAlt(
        payload, identifier=prm.identifier, content_type=content_type,
        filename=getattr(data, "filename", None),
        headers=getattr(data, "headers", None),
    )
