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


""" This module provides Python file-object like access to VSI files.
"""


import os
from uuid import uuid4

if os.environ.get('READTHEDOCS', None) != 'True':
    from eoxserver.contrib.gdal import (
        VSIFOpenL, VSIFCloseL, VSIFReadL, VSIFWriteL, VSIFSeekL, VSIFTellL,
        VSIStatL, Unlink, Rename, FileFromMemBuffer
    )

    rename = Rename

    unlink = remove = Unlink


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


class VSIFile(object):
    """ File-like object interface for VSI file API.

    :param filename: the path to the file; this might also be any VSI special
                     path like "/vsicurl/..." or "/vsizip/...". See the `GDAL
                     documentation
                     <http://trac.osgeo.org/gdal/wiki/UserDocs/ReadInZip>`_
                     for reference.
    :param mode: the file opening mode
    """

    def __init__(self, filename, mode="r"):
        self._handle = VSIFOpenL(filename, mode)
        self._filename = filename

        if self._handle is None:
            raise IOError("Failed to open file '%s'." % self._filename)

    @property
    def filename(self):
        """ Returns the filename referenced by this file
        """
        return self._filename

    def read(self, size=None):
        """ Read from the file. If no ``size`` is specified, read until the end
        of the file.

        :param size: the number of bytes to be read
        :returns: the bytes read as a string
        """

        if size is None:
            size = self.size - self.tell()
        return VSIFReadL(1, size, self._handle)

    def write(self, data):
        """ Write the buffer ``data`` to the file.

        :param data: the string buffer to be written
        """
        VSIFWriteL(data, 1, len(data), self._handle)

    def tell(self):
        """ Return the current read/write offset of the file.

        :returns: an integer offset
        """
        return VSIFTellL(self._handle)

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

    @property
    def size(self):
        """ Return the size of the file in bytes
        """
        stat = VSIStatL(self.filename)
        return stat.size

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
    def from_buffer(cls, buf, mode="w", filename=None):
        """ Creates a :class:`TemporaryVSIFile` from a string.

        :param buf: the supplied string
        :param mode: the file opening mode
        :param filename: the optional filename the file shall be stored under;
                         by default this is an in-memory location
        """
        if not filename:
            filename = "/vsimem/%s" % uuid4().hex()
        FileFromMemBuffer(filename, buf)
        return cls(mode)

    def close(self):
        """ Close the file. This also deletes it.
        """
        super(TemporaryVSIFile, self).close()
        remove(self.filename)
