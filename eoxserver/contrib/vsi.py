# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------


""" This module provides Python file-object like access to VSI files.
"""


import os
from uuid import uuid4
from functools import wraps
import mimetypes
from urllib.parse import quote

from django.http import StreamingHttpResponse


if os.environ.get('READTHEDOCS', None) != 'True':
    import numpy

    from eoxserver.contrib.gdal import (
        VSIFOpenL, VSIFCloseL, VSIFReadL, VSIFWriteL, VSIFSeekL, VSIFTellL,
        VSIStatL, VSIFTruncateL, Unlink, Rename, FileFromMemBuffer
    )

    UINT32_MAX = numpy.iinfo('uint32').max

    rename = Rename

    unlink = remove = Unlink
else:
    UINT32_MAX = 0xffffffff


def open(filename, mode="r"):
    """ A function mimicking the builtin function
    :func:`open <__builtins__.open>` but returning a :class:`VSIFile` instead.

    :param filename: the path to the file; this might also be any VSI special
                     path like "/vsicurl/..." or "/vsizip/...". See the `GDAL
                     documentation
                     <http://trac.osgeo.org/gdal/wiki/UserDocs/ReadInZip>`_
                     for reference.
    :param mode: the file opening mode
    :returns: a :class:`VSIFile`
    """
    return VSIFile(filename, mode)


def _ensure_open(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._handle is None:
            raise ValueError('I/O operation on closed file')
        return func(self, *args, **kwargs)
    return wrapper


class VSIFile(object):
    """ File-like object interface for VSI file API.

    :param filename: the path to the file; this might also be any VSI special
                     path like "/vsicurl/..." or "/vsizip/...". See the `GDAL
                     documentation
                     <http://trac.osgeo.org/gdal/wiki/UserDocs/ReadInZip>`_
                     and `manuals
                     <http://www.gdal.org/gdal_virtual_file_systems.html>`_
                     for reference.
    :param mode: the file opening mode
    """

    def __init__(self, filename, mode="r"):
        self._handle = VSIFOpenL(filename, mode)
        self._filename = filename

        if self._handle is None:
            raise IOError("Failed to open file '%s'." % self._filename)

    @property
    def name(self):
        """ Returns the filename referenced by this file
        """
        return self._filename

    @_ensure_open
    def read(self, size=UINT32_MAX):
        """ Read from the file. If no ``size`` is specified, read until the end
        of the file.

        :param size: the number of bytes to be read
        :returns: the bytes read as a string
        """

        value = VSIFReadL(1, size, self._handle)
        if isinstance(value, bytes):
            return value
        elif isinstance(value, bytearray):
            return bytes(value)
        elif value is None:
            return b''
        else:
            raise ValueError(value)

    @_ensure_open
    def write(self, data):
        """ Write the buffer ``data`` to the file.

        :param data: the string buffer to be written
        """
        VSIFWriteL(data, 1, len(data), self._handle)

    @_ensure_open
    def tell(self):
        """ Return the current read/write offset of the file.

        :returns: an integer offset
        """
        return VSIFTellL(self._handle)

    @_ensure_open
    def seek(self, offset, whence=os.SEEK_SET):
        """ Set the new read/write offset in the file.

        :param offset: the new offset
        :param whence: how the offset shall be interpreted; possible options are
                       :const:`os.SEEK_SET`, :const:`os.SEEK_CUR` and
                       :const:`os.SEEK_END`
        """
        VSIFSeekL(self._handle, offset, whence)

    def close(self):
        """ Close the file.
        """
        if self._handle is not None:
            VSIFCloseL(self._handle)
        self._handle = None

    @property
    def closed(self):
        """ Return a boolean value to indicate whether or not the file is
        already closed.
        """
        return (self._handle is None)

    def __iter__(self):
        """ Iterate over the lines within the file.
        """
        return self

    @_ensure_open
    def next(self):
        """ Satisfaction of the iterator protocol. Return the next line in the
            file or raise `StopIteration`.
        """
        line = self.readline()
        if not line:
            raise StopIteration
        return line

    @_ensure_open
    def readline(self, length=None, windowsize=1024):
        """ Read a single line from the file and return it.

        :param length: the maximum number of bytes to read to look for a whole
                       line.
        :param windowsize: the windowsize to search for a newline character.
        """
        line = ""
        while True:
            # read amount and detect for EOF
            string = self.read(length or windowsize)
            if not string:
                break

            try:
                position = string.index('\n')
                line += string[:position]

                # retun the cursor for the remainder of the string
                self.seek(-(len(string) - (position + 1)), os.SEEK_CUR)
                break
            except ValueError:
                line += string

            # also break when a specific size was requested but no newline was
            # found
            if length:
                break

        return line

    def readlines(self, sizehint=0):
        """ Read the remainder of the file (or up to `sizehint` bytes) and return
            the lines.

        :param sizehint: the number of bytes to scan for lines.
        :return: the lines
        :rtype: list of strings
        """
        # TODO: take sizehint into account
        lines = [line for line in self]
        return lines

    @property
    @_ensure_open
    def size(self):
        """ Return the size of the file in bytes
        """
        stat = VSIStatL(self.name)
        return stat.size

    @_ensure_open
    def flush(self):
        pass
        # VSIFlushL(self._handle)  # TODO: not available?

    @_ensure_open
    def truncate(self, size=None):
        """ Truncates the file to the given size or to the size until the current
            position.

        :param size: the new size of the file.
        """
        size = size or self.tell()
        VSIFTruncateL(self._handle, size)

    def isatty(self):
        """ Never a TTY """
        return False

    def __enter__(self):
        return self

    def __exit__(self, etype=None, evalue=None, tb=None):
        self.close()

    def __del__(self):
        self.close()


class TemporaryVSIFile(VSIFile):
    """ Subclass of VSIFile, that automatically deletes the physical file upon
        deletion.
    """

    @classmethod
    def from_buffer(cls, buf, mode="wb", filename=None):
        """ Creates a :class:`TemporaryVSIFile` from a string.

        :param buf: the supplied string
        :param mode: the file opening mode
        :param filename: the optional filename the file shall be stored under;
                         by default this is an in-memory location
        """
        if not filename:
            filename = "/vsimem/%s" % uuid4().hex
        f = cls(filename, mode)
        f.write(buf)
        f.seek(0)
        return f

    def close(self):
        """ Close the file. This also deletes it.
        """
        if not self.closed:
            super(TemporaryVSIFile, self).close()
            remove(self.name)


def join(first, *paths):
    """ Joins the given VSI path specifiers. Similar to :func:`os.path.join` but
        takes care of the VSI-specific handles such as `vsicurl`, `vsizip`, etc.
    """
    parts = first.split('/')
    for path in paths:
        new = path.split('/')
        if path.startswith('/vsi'):
            parts = new[0:2] + (parts if parts[0] else parts[1:]) + new[2:]
        else:
            parts.extend(new)
    return '/'.join(parts)


class VSIFileResponse(StreamingHttpResponse):
    """ Subclass of StreamingHttpResponse, a replacement for Django's
        FileResponse which does not work for VSIFiles in Django v3.2.15
    """
    # inspired from https://github.com/django/django/blob/bd062445cffd3f6cc6dcd20d13e2abed818fa173/django/http/response.py#L500

    block_size = 4096

    def __init__(self, *args, as_attachment=False, filename='', **kwargs):
        self.as_attachment = as_attachment
        self.filename = filename
        super().__init__(*args, **kwargs)

    def _set_streaming_content(self, value):
        filelike = value
        self._resource_closers.append(filelike.close)
        value = iter(lambda: filelike.read(self.block_size), b'')
        self.set_headers(filelike)
        super()._set_streaming_content(value)

    def set_headers(self, filelike):
        self.headers["Content-Length"] = filelike.size
        content_type, encoding = mimetypes.guess_type(filelike.name)
        content_type = {
            "bzip2": "application/x-bzip",
            "gzip": "application/gzip",
            "xz": "application/x-xz",
        }.get(encoding, content_type)
        self.headers["Content-Type"] = (
            content_type or "application/octet-stream"
        )

        filename = self.filename or filelike.name
        disposition = "attachment" if self.as_attachment else "inline"
        try:
            filename.encode("ascii")
            file_expr = 'filename="{}"'.format(
                filename.replace("\\", "\\\\").replace('"', r"\"")
            )
        except UnicodeEncodeError:
            file_expr = "filename*=utf-8''{}".format(quote(filename))
        self.headers["Content-Disposition"] = "{}; {}".format(
            disposition, file_expr
        )
