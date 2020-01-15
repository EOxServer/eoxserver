#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

"""
This module contains implementation of MIME multipart packing and unpacking
utilities.

The main benefit of the utilities over other methods of mutipart handling
is that the functions of this module do not manipulate the input data
buffers and especially avoid any unnecessary data copying.
"""
from django.utils.six import b

def capitalize(header_name):
    """ Capitalize header field name. Eg., 'content-type' is capilalized to
    'Content-Type'.

    .. deprecated:: 0.4
    """
    return "-".join([f.capitalize() for f in header_name.split("-")])

# local alias to prevent conflict with local variable
__capitalize = capitalize


def getMimeType(content_type):
    """ Extract MIME-type from Content-Type string and convert it to
    lower-case.

    .. deprecated:: 0.4
    """
    return content_type.partition(";")[0].strip().lower()


def getMultipartBoundary(content_type):
    """ Extract boundary string from mutipart Content-Type string.

    .. deprecated:: 0.4
    """

    for opt in content_type.split(";")[1:]:
        key, _, val = opt.partition("=")
        if key.strip().lower() == "boundary":
            return val.strip()

    raise ValueError(
        "failed to extract the mutipart boundary string! content-type: %s"
        % content_type
    )


def mpPack(parts, boundary):
    """
Low-level memory-friendly MIME multipart packing.

Note: The data payload is passed untouched and no transport encoding
of the payload is performed.

Inputs:

 - parts - list of part-tuples, each tuple shall have two elements
    the header list and (string) payload. The header itsels should be
    a sequence of key-value pairs (tuples).

 - boundary - boundary string

Ouput:

 - list of strings (which can be directly passsed as a Django response content)

.. deprecated:: 0.4
    """

    # empty multipart package
    pack = ["--%s" % boundary]

    for header, data in parts:

        # pack header
        for key, value in header:
            pack.append("\r\n%s: %s" % (key, value))

        # terminate header
        pack.append("\r\n\r\n")

        # append data
        pack.append(data)

        # terminate partition
        pack.append("\r\n--%s" % boundary)

    #terminate package
    pack.append("--")

    # return package
    return pack


def mpUnpack(cbuffer, boundary, capitalize=False):
    """
Low-level memory-friendly MIME multipart unpacking.

Note: The payload of the multipart package data is neither modified nor copied.
No decoding of the transport encoded payload is performed.

Note: The subroutine does not unpack any nested mutipart content.

Inputs:

 - ``cbuffer`` - character buffer (string) containing the
   the header list and (string) payload. The header itsels should be
   a sequence of key-value pairs (tuples).

 - ``boundary`` - boundary string

 - ``capitalize`` - by default the header keys are converted to lower-case
   (e.g., 'content-type').
   To capitalize the names (e.g., 'Content-Type') set this option to true.

Output:

 - list of parts - each part is a tuple of the header dictionary,
   payload ``cbuffer`` offset and payload size.

.. deprecated:: 0.4
    """

    def findBorder(offset=0):

        delim = "--%s" % boundary if offset == 0 else "\n--%s" % boundary

        # boundary offset (end of last data)
        idx0 = cbuffer.find(delim, offset)

        if idx0 < 0:
            raise ValueError("Boundary cannot be found!")

        # header offset
        idx1 = idx0 + len(delim)

        # nescessary check to be able to safely check two following characters
        if len(cbuffer[idx1:]) < 2:
            raise ValueError("Buffer too short!")

        # check the leading CR character
        if idx0 > 0 and cbuffer[idx0-1] == "\r":
            idx0 -= 1

        # check the terminating sequence
        if cbuffer[idx1:(idx1+2)] == "--":
            return idx0, idx1+2, -1

        # look-up double endl-line (data offset)
        tmp = idx1

        while True:

            tmp = 1 + cbuffer.find("\n", tmp)

            if tmp < 1:
                raise ValueError(
                    "Cannot find payload's a double new-line separator!"
                )

            # is it followed by new line?

            elif cbuffer[tmp:(tmp+2)] == "\r\n":
                idx2 = tmp + 2
                break

            elif cbuffer[tmp:(tmp+1)] == "\n":
                idx2 = tmp + 1
                break

            # otherwise continue to lookup
            continue

        # adjust the data offset (separator must be followed by new-line)
        if cbuffer[idx1:(idx1+2)] == "\r\n":
            idx1 += 2
        elif cbuffer[idx1:(idx1+1)] == "\n":
            idx1 += 1
        else:
            raise ValueError("Boundary is not followed by a new-line!")

        return idx0, idx1, idx2

    #--------------------------------------------------------------------------
    # auxiliary nested functions formating header names

    # capitalize header name
    def unpackCC(v):
        key, _, val = v.partition(b(":"":"))
        return __capitalize(key.strip()), val.strip()

    # header name all lower
    def unpackLC(v):
        key, _, val = v.partition(b(":"))
        return key.strip().lower(), val.strip()

    # filter function rejecting entries with blank keys
    def noblank(tup):
        (k, v) = tup
        return bool(k)

    #--------------------------------------------------------------------------

    # get the offsets
    # off = (<last payload end>,<header start>,<payload start>)
    # negative <payload start> means terminating boundary

    try:

        off = findBorder()
        offsets = [off]

        while off[1] < off[2]:
            off = findBorder(off[2])
            offsets.append(off)

    except ValueError as e:
        raise Exception(
            "The buffer is not a valid MIME multi-part message! Reason: %s"
            % e.message
        )

    # process the parts
    parts = []
    for of0, of1 in zip(offsets[:-1], offsets[1:]):

        # get the http header with <LF> line ending
        tmp = cbuffer[of0[1]:of0[2]].replace("\r\n", "\n")[:-2].split("\n")

        # unpack header
        header = dict(
            filter(noblank,
                map((unpackLC, unpackCC)[capitalize], tmp)
            )
        )

        # get the header and payload offset and size
        parts.append((header, of0[2], of1[0]-of0[2]))

    return parts


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
