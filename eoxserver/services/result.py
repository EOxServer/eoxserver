

import os
from cStringIO import StringIO
from uuid import uuid4

from django.http import HttpResponse
from django.utils.datastructures import SortedDict

from eoxserver.core.util import multiparttools as mp


class ResultItem(object):
    """ Base class for render results.
    """

    def __init__(self, content_type=None, filename=None, identifier=None):
        self.content_type = content_type
        self.filename = filename
        self.identifier = identifier
    
    @property
    def data(self):
        """ Returns the "raw" data, usually as a string, buffer, memoryview, etc.
        """
        return ""

    @property
    def data_file(self):
        """ Returns the data as a file-like object.
        """
        return StringIO("")

    def chunked(self, chunksize):
        """ Returns a chunk of the data, which has at most ``chunksize`` bytes.
        """
        yield ""

    def delete(self):
        """ Cleanup any associated files, allocated memory, etc.
        """
        pass


    @property
    def get_headers(self):
        headers = SortedDict([("Content-Type", self.content_type)])

        if self.filename:
            headers["Content-Disposition"] = 'inline; filename="%s"' % self.filename
        if self.identifier:
            headers["Content-Id"] = self.identifier
        
        return headers


class ResultFile(ResultItem):
    """ Class for results that wrap physical files on the disc.
    """

    def __init__(self, fp, content_type=None, filename=None, identifier=None):
        super(ResultFile, self).__init__(content_type, filename, identifier)
        self.fp = fp

    @property
    def data(self):
        return fp.read()

    @property
    def data_file(self):
        return fp

    def chunked(self, chunksize):
        while True:
            data = fp.read(chunksize)
            if not data:
                break

            yield data

    def delete(self):
        os.remove(fp.filename)


class ResultBuffer(ResultItem):
    """ Class for results that are actually a subset of a larger context. 
        Usually a buffer
    """

    def __init__(self, buf, content_type=None, filename=None, identifier=None):
        super(ResultBuffer, self).__init__(content_type, filename, identifier)
        self.buf = buf

    @property
    def data(self):
        return self.buf

    @property
    def data_file(self):
        return StringIO(self.buf)

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
        its content type is used.
    """
    if len(result_set) == 1:
        return result_set[0].content_type
    else:
        return "multipart/related"


def get_headers(result_item):
    """ Yields content headers, if they are set in the result item.
    """
    yield "Content-Type", result_item.content_type or "application/octet-stream"
    if result_item.identifier:
        yield "Content-Id", result_item.identifier
    if result_item.filename:
        yield (
            "Content-Disposition", 'attachment; filename="%s"' 
            % result_item.filename
        )


def to_http_response(result_set, response_type=HttpResponse, boundary=None):
    """ Returns a response for a given result set. The ``response_type`` is the 
        class to be used. It must be capable to work with iterators.
    """
    
    if len(result_set) > 1:
        boundary = boundary or uuid4().hex
        content_type = "multipart/related; boundary=%s" % boundary
        headers = ()

    else:
        boundary = None
        content_type = result_set[0].content_type or "application/octet-stream"
        headers = get_headers(result_set[0])


    def response_iterator(items, boundary=None):
        if boundary:
            boundary_str = "%s--%s%s" % (mp.CRLF, boundary, mp.CRLF)
            boundary_str_end = "%s--%s--" % (mp.CRLF, boundary)

        for item in items:
            if boundary:
                yield boundary_str
                yield mp.CRLF.join(
                    "%s: %s" % (key, value) 
                    for key, value in get_headers(item)
                ) + mp.CRLFCRLF
            yield item.data
        if boundary:
            yield boundary_str_end

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
    content_type = headers.get("Content-Type", "application/octet-stream")
    _, params = mp.parse_parametrized_option(
        headers.get("Content-Disposition", "")
    )
    filename = params.get("filename")
    identifier = headers.get("Content-Id")
    return content_type, filename, identifier


def result_set_from_raw_data(data):
    return [
        ResultBuffer(data, *parse_headers(headers))
        for headers, data in mp.iterate(data)
        if not headers.get("Content-Type").startswith("multipart")
    ]