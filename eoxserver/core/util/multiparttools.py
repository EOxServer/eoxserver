# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

"""
This module contains implementation of MIME multipart packing and unpacking
utilities.

The main benefit of the utilities over other methods of mutipart handling
is that the functions of this module do not manipulate the input data
buffers and especially avoid any unnecessary data copying.
"""

CRLF = b"\r\n"
CRLFCRLF = b"\r\n\r\n"


def get_substring(data, boundary, offset, end):
    """ Retrieves the substring of ``data`` until the next ``boundary`` from a
    given offset to a until ``end``.
    """
    index = data.find(boundary, offset, end)
    if index == -1:
        return None, None
    return data[offset:index], index + len(boundary)


def parse_parametrized_option(string):
    """ Parses a parametrized options string like
    'base;option=value;otheroption=othervalue'.

    :returns: the base string and a :class:`dict` with all parameters
    """
    parts = string.split(b";")
    params = dict(
        param.strip().split(b"=", 1) for param in parts[1:]
    )
    return parts[0], params


def capitalize_header(key):
    """ Returns a capitalized version of the header line such as
    'content-type' -> 'Content-Type'.
    """

    return b"-".join([
        item
        if item.decode()[0].isupper() else
        (item.decode()[0].upper() + item.decode()[1:]).encode('ascii')
        for item in key.split(b"-")
    ])


def iterate(data, offset=0, end=None, headers=None):
    """ Efficient generator function to iterate over a single- or multipart
        message. I yields tuples in the shape (``headers``, ``data``), where
        headers is a ``dict`` and data a buffer object, referencing the subset
        of the original content. In case of multipart messages, the multipart
        headers are yielded beforehand, with an empty string as data.

        The `offset` parameter specifies the offset index to the start of the
        data. This is mostly used in the recursive call. The same applies to the
        `end` parameter.

        The `headers` parameter specifies that the header section of the
        response was already read, and the headers are now entailed in the given
        dict. If this parameter is omitted, the headers are read from the
        stream.
    """

    # check if the headers need to be parsed.
    if not headers:
        # read the header bytes from the string and get the new offset.
        header_bytes, offset = get_substring(data, CRLFCRLF, offset, end)

        # check if no data could be extracted
        if (header_bytes, offset) == (None, None):
            return

        # parse the headers into a dict
        headers = {}
        for line in header_bytes.split(CRLF):
            key, _, value = line.partition(b":")
            headers[capitalize_header(key.strip())] = value.strip()

    # get the content type
    content_type, params = parse_parametrized_option(
        headers.get(b"Content-Type", b"")
    )

    # check if this is a multipart
    if content_type.startswith(b"multipart"):
        # if this is a multipart, yield only its headers and an empty string
        yield headers, memoryview(b"")

        # parse the boundary and find the final index of all multiparts
        boundary = b"%s--%s" % (CRLF, params[b"boundary"])
        end_boundary = b"%s--" % boundary

        sub_end = data.find(end_boundary)
        if sub_end == -1:
            raise ValueError("Could not find multipart end.")

        # get the first part of this multipart
        sub_offset = data.find(boundary, offset, sub_end)
        if sub_offset == -1:
            raise ValueError("Could not find boundary.")

        # iterate over all parts until we reach the end of the multipart
        while sub_offset < sub_end:
            sub_offset += len(boundary) + 1
            sub_stop = data.find(boundary, sub_offset, sub_end)

            sub_stop = sub_stop if sub_stop > -1 else sub_end

            # recursive function call
            for sub_headers, sub_data in iterate(data, sub_offset, sub_stop):
                yield sub_headers, sub_data

            sub_offset = sub_stop

    else:
        # in case we have a single part, just yield the headers and a buffer
        # pointing to a substring of the original data stream.
        if end is not None:
            yield headers, memoryview(data)[offset:end]
        else:
            yield headers, memoryview(data)[offset:]
