#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011-2025 EOX IT Services GmbH
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

"""
This module contains implementation of MIME multipart packing and unpacking
utilities.

The main benefit of the utilities over other methods of mutipart handling
is that the functions of this module do not manipulate the input data
buffers and especially avoid any unnecessary data copying.
"""
from django.utils.six import b

CRLF = b"\r\n"
CRLFCRLF = b"\r\n\r\n"


def get_multipart_related_root(data, headers, **options):
    """ Parse multipart/related compound payload and return the "root" part
    as a (``data``, ``headers``) tuple, where data is a buffer object
    referencing the subset of the original content (memoryview) and headers
    is a text dictionary of the part's headers.

    This function raises an error if the message is properly formatted
    multipart/related object. See https://www.ietf.org/rfc/rfc2387.txt

    This function is meant for quick extraction of of the "root" part.
    For the parsing of the whole pyload use ``parse_multipart_related()``.

    Requires the global payload headers.
    """
    mime_type, params = parse_parametrized_option(headers.get("Content-Type", ""))

    if mime_type != "multipart/related":
        raise ValueError(
            f"Expected multipart/related data, received {mime_type} instead!"
        )

    if not (boundary := params.get("boundary")):
        raise ValueError("Failed to extract multipart boundary!")

    root_cid = params.get("start")

    for part_data, part_headers in _iterate_parts(data, boundary, **options):
        part_cid = part_headers.get("Content-Id")
        if not root_cid or root_cid == part_cid:
            return part_data, part_headers

    raise ValueError("Failed to find the multipart/related root part!")


def parse_multipart_related(data, headers, **options):
    """ Parse multipart/related compound payload and return the "root" part
    as a (``data``, ``headers``) tuple and a dictionary mapping related parts'
    content identifier to the (``data``, ``headers``) tuples, where data is
    a buffer object referencing the subset of the original content (memoryview)
    and headers is a text dictionary of the part's headers.

    multipart/related object. See https://www.ietf.org/rfc/rfc2387.txt

    Requires the global payload headers.
    """
    mime_type, params = parse_parametrized_option(headers.get("Content-Type", ""))

    if mime_type != "multipart/related":
        raise ValueError(
            f"Expected multipart/related data, received {mime_type} instead!"
        )

    if not (boundary := params.get("boundary")):
        raise ValueError("Failed to extract multipart boundary!")

    root_cid = params.get("start")

    root_part, related_parts = None, {}

    for part_data, part_headers in _iterate_parts(data, boundary, **options):
        part_cid = part_headers.get("Content-Id")
        if not root_part and not root_cid or root_cid == part_cid:
            root_part = part_data, part_headers
        else:
            related_parts[part_cid] = part_data, part_headers

    if not root_part:
        raise ValueError("Failed to find the multipart/related root part!")

    return root_part, related_parts


def iterate_multipart_data(data, headers, **options):
    """ Efficient generator function to iterate over a single- or multipart
    message. It yields tuples in the shape (``data``, ``headers``),
    where data a buffer object referencing the subset of the original content
    (memoryview) and headers is a text dictionary of the part's headers.

    Requires the global payload headers.

    Compared to `eoxserver.core.util.multiparttools.iter()` this generator
    works with string headers and does not insert the extra part with
    global headers.

    This iterator also does not implement recursive parsing of nested
    multipart content.

    The parsing speed of larger dataset is ~2x faster.
    """
    mime_type, params = parse_parametrized_option(headers.get("Content-Type", ""))

    if not mime_type.startswith("multipart/"):
        # in case we have a single part, just yield the headers and a buffer
        # pointing to a substring of the original data stream.
        yield memoryview(data), headers
        return

    if not (boundary := params.get("boundary")):
        raise ValueError("Failed to extract multipart boundary!")

    yield from _iterate_parts(data, boundary, **options)


def parse_headers(data, **kwargs):
    """ Parse HTTP headers from the given message. """
    headers, _ = _parse_headers(data, 0, **kwargs)
    return headers


def _iterate_parts(data, boundary, **kwargs):
    """ Efficient generator function to iterate over a multipart message
    and yields tuples in the shape (``data``, ``headers``), where headers is
    a string ``dict`` and data a reas``memoryview`` object, referencing the subset of the original
    content.
    """
    boundary = b"%s--%s" % (CRLF, boundary.encode("ascii"))

    if (offset := data.find(boundary)) == -1:
        raise ValueError("Could not find multipart delimiter.")
    offset += len(boundary)

    while data[offset:offset + 2] == CRLF:
        offset += 2

        if (end_offset := data.find(boundary, offset)) == -1:
            raise ValueError("Could not find multipart delimiter.")

        headers, offset = _parse_headers(data, offset, **kwargs)

        yield memoryview(data)[offset:end_offset], headers

        offset = end_offset + len(boundary)

    if data[offset:offset + 2] != b"--":
        raise ValueError("Could not find multipart close-delimiter.")


def _parse_headers(data, offset, header_size_limit=4069):
    """ Parse headers. """

    headers = {}
    start_offset = offset
    while (end_offset := data.find(CRLF, offset)) > offset:
        if end_offset - start_offset > header_size_limit:
            raise ValueError(
                "Size of the multipart body headers exceeds the allowed "
                f"{header_size_limit} bytes limit."
            )
        line = data[offset:end_offset].decode("ascii")
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError("Malformed multipart body headers.")
        headers[capitalize_header(key.strip())] = value.strip()
        offset = end_offset + 2
    if end_offset == -1:
        raise ValueError("Malformed multipart body headers.")
    offset += len(CRLF)
    return headers, offset


def get_substring(data, boundary, offset, end):
    """ Retrieves the substring of ``data`` until the next ``boundary`` from a
    given offset to a until ``end``.
    """
    index = data.find(boundary, offset, end)
    if index == -1:
        return None, None
    return data[offset:index], index + len(boundary)


def parse_parametrized_option(string, delimiter=";", assignment="=", quote="\""):
    """ Parses a parametrized options string like
    'base; option=value; other_option="other.value"', such the one found
    in the Content-Type header.
    See https://www.w3.org/Protocols/rfc1341/4_Content-Type.html

    :returns: the base string and a :class:`dict` with all parameters
    """
    quote = quote[0]
    def _parse_parameter(raw_value):
        key, _, value = raw_value.strip().partition(assignment)
        if value and value[0] == quote and value[-1] == quote:
            value = value[1:-1]
        return key, value
    base, *parts = string.split(delimiter)
    parameters = dict(_parse_parameter(param) for param in parts)
    return base, parameters


def capitalize_header(key):
    """ Returns a capitalized version of the header line such as
    'content-type' -> 'Content-Type'.
    """
    return "-".join(
        item[0].upper() + item[1:]
        for item in key.split("-")
    )


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
            key = capitalize_header(
                key.strip().decode("ascii")
            ).encode("ascii")
            headers[key] = value.strip()

    # get the content type
    content_type, params = parse_parametrized_option(
        headers.get(b"Content-Type", b""),
        delimiter=b";", assignment=b"=", quote=b"\""
    )

    # check if this is a multipart
    if content_type.startswith(b"multipart"):
        # if this is a multipart, yield only its headers and an empty string
        yield headers, memoryview(b"")

        # parse the boundary and find the final index of all multiparts
        boundary = b"%s--%s%s" % (CRLF, params[b"boundary"], CRLF)
        end_boundary = b"%s--%s--" % (CRLF, params[b"boundary"])

        sub_end = data.find(end_boundary)
        if sub_end == -1:
            raise ValueError("Could not find multipart end.")

        # get the first part of this multipart
        sub_offset = data.find(boundary, offset, sub_end)
        if sub_offset == -1:
            raise ValueError("Could not find boundary.")

        # iterate over all parts until we reach the end of the multipart
        while sub_offset < sub_end:
            sub_offset += len(boundary)
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
