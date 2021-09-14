#-------------------------------------------------------------------------------
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

import os
import os.path
try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO

from uuid import uuid4

from django.http import HttpResponse
from django.utils.six import b

from eoxserver.core.util import multiparttools as mp


class ResultItem(object):
    """ Base class (or interface) for result items of a result set.

    :param content_type: the content type of the result item. in HTTP this will
                         be translated to the ``Content-Type`` header
    :param filename: the filename of the result item.
    :param identifier: the identifier of the result item. translated to
                       ``Content-Id`` HTTP header
    """

    def __init__(self, content_type=None, filename=None, identifier=None):
        self._content_type = content_type
        self.filename = filename
        self.identifier = identifier

    @property
    def data(self):
        """ Returns the "raw" data, usually as a string, buffer, memoryview,
        etc.
        """
        return ""

    @property
    def data_file(self):
        """ Returns the data as a Python file-like object.
        """
        return StringIO("")

    @property
    def content_type(self):
        """ Reterns a binary value of content-type if it is a string.
        """
        if isinstance(self._content_type, str):
            self._content_type = b(self._content_type)
        return self._content_type

    def __len__(self):
        """ Unified access to size of data.
        """
        raise NotImplementedError

    size = property(lambda self: len(self))

    def chunked(self, chunksize):
        """ Returns a chunk of the data, which has at most ``chunksize`` bytes.
        """
        yield ""

    def delete(self):
        """ Cleanup any associated files, allocated memory, etc.
        """
        pass


class ResultFile(ResultItem):
    """ Class for results that wrap physical files on the disc.
    """

    def __init__(self, path, content_type=None, filename=None, identifier=None):
        super(ResultFile, self).__init__(content_type, filename, identifier)
        self.path = path

    @property
    def data(self):
        with open(self.path, 'rb') as f:
            return f.read()

    @property
    def data_file(self):
        return open(self.path)

    def __len__(self):
        return os.path.getsize(self.path)

    def chunked(self, chunksize):
        with open(self.path, 'rb') as f:
            while True:
                data = f.read(chunksize)
                if not data:
                    break

                yield data

    def delete(self):
        os.remove(self.path)


class ResultBuffer(ResultItem):
    """ Class for results that are actually a subset of a larger context.
        Usually a buffer.
    """

    def __init__(self, buf, content_type=None, filename=None, identifier=None):
        super(ResultBuffer, self).__init__(content_type, filename, identifier)
        if isinstance(buf, str) or isinstance(buf, bytes):
            self.buf = buf
        else:
            self.buf = buf.tobytes()

    @property
    def data(self):
        return self.buf
    # @property
    # def data_file(self):
    #     return StringIO(self.buf)

    def __len__(self):
        return len(self.buf)

    def chunked(self, chunksize):
        if chunksize < 0:
            raise ValueError

        size = len(self.buf)
        if chunksize >= size:
            yield self.buf
            return

        i = 0
        while i < size:
            yield self.buf[i:i+chunksize]
            i += chunksize


def get_content_type(result_set):
    """ Returns the content type of a result set. If only one item is included
        its content type is used, otherwise the constant "multipart/related".
    """
    if len(result_set) == 1:
        return result_set[0].content_type
    else:
        return "multipart/related"


def get_headers(result_item):
    """ Yields content headers, if they are set in the result item.
    """
    if hasattr(result_item, 'headers'):
        for header in result_item.headers:
            yield header
    yield b"Content-Type", result_item.content_type or b"application/octet-stream"
    if result_item.identifier:
        yield b"Content-Id", result_item.identifier.encode('utf-8')
        if  isinstance(result_item.filename, str):
            result_item.filename = b(result_item.filename)
    if result_item.filename:
        yield (
            b"Content-Disposition", b'attachment; filename="%s"'
            % result_item.filename
        )
    try:
        yield b"Content-Length", b"%d" % len(result_item)
    except (AttributeError, NotImplementedError):
        pass


def get_payload_size(result_set, boundary):
    """ Calculate the size of the result set and all entailed result items plus
        headers.
    """
    boundary_str = b"%s--%s%s" % (mp.CRLF, boundary, mp.CRLF)
    boundary_str_end = b"%s--%s--" % (mp.CRLF, boundary)

    size = 0
    for item in result_set:
        size += len(boundary_str)
        size += len(
            mp.CRLF.join(b"%s: %s" % (k, v) for k, v in get_headers(item))
        )
        size += len(mp.CRLFCRLF)
        size += len(item)
    size += len(boundary_str_end)
    return size


def to_http_response(result_set, response_type=HttpResponse, boundary=None):
    """ Returns a response for a given result set. The ``response_type`` is the
        class to be used. It must be capable to work with iterators. This
        function is also responsible to delete any temporary files and buffers
        of the ``result_set``.

        :param result_set: an iterable of objects following the
                           :class:`ResultItem` interface
        :param response_type: the response type class to use; defaults to
                              :class:`HttpResponse <django.http.HttpResponse>`.
                              For streaming responses use
                              :class:`StreamingHttpResponse
                              <django.http.StreamingHttpResponse>`
        :param boundary: the multipart boundary; if omitted a UUID hex string is
                         computed and used
        :returns: a response object of the desired type
    """

    # if more than one item is contained in the result set, the content type is
    # multipart
    if len(result_set) > 1:
        boundary = boundary or (uuid4().hex).encode('utf-8')
        content_type = b"multipart/related; boundary=%s" % boundary
        headers = (('Content-Length', get_payload_size(result_set, boundary)), )

    # otherwise, the content type is the content type of the first included item
    elif len(result_set) < 1 or result_set[0].content_type is None:
        boundary = None
        content_type = b"application/octet-stream"
        headers = (('Content-Length', 0 ),)

    else:
        boundary = None
        content_type = result_set[0].content_type or b"application/octet-stream"
        headers = tuple(get_headers(result_set[0]))

    def response_iterator(items, boundary=None):
        try:
            if boundary:
                boundary_str = b"%s--%s%s" % (mp.CRLF, boundary, mp.CRLF)
                boundary_str_end = b"%s--%s--" % (mp.CRLF, boundary)

            for item in items:
                if boundary:
                    yield boundary_str
                    yield mp.CRLF.join(
                    b"%s: %s" % (key, value)
                    for key, value in get_headers(item)
                    ) + mp.CRLFCRLF
                yield item.data
            if boundary:
                yield boundary_str_end
        finally:
            for item in items:
                try:
                    item.delete()
                except:
                    pass  # bad exception swallowing...

    # workaround for bug in django, that does not consume iterator in tests.
    if response_type == HttpResponse:
        response = response_type(
            list(response_iterator(result_set, boundary)),
            content_type
        )
    else:
        response = response_type(
            response_iterator(result_set, boundary), content_type
        )

    # set any headers
    for key, value in headers:
        response[key] = value

    return response


def parse_headers(headers):
    """ Convenience function to read the "Content-Type", "Content-Disposition"
        and "Content-Id" headers.

        :param headers: the raw header :class:`dict`
    """
    content_type = headers.get(b"Content-Type", b"application/octet-stream")
    _, params = mp.parse_parametrized_option(
        headers.get(b"Content-Disposition", b"")
    )
    filename = params.get(b"filename")
    if filename:
        if filename.startswith(b'"'):
            filename = filename[1:]
        if filename.endswith(b'"'):
            filename = filename[:-1]

    identifier = headers.get(b"Content-Id")
    return content_type, filename, identifier


def result_set_from_raw_data(data):
    """ Create a result set from raw HTTP data. This can either be a single
        or a multipart string. It returns a list containing objects of the
        :class:`ResultBuffer` type that reference substrings of the given data.

        :param data: the raw byte data
        :returns: a result set: a list containing :class:`ResultBuffer`
    """
    return [
        ResultBuffer(d, *parse_headers(headers))
        for headers, d in mp.iterate(data)
        if not headers.get(b"Content-Type").startswith(b"multipart")
    ]
