#-------------------------------------------------------------------------------
# $Id$
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

from gdal import (
    VSIFOpenL, VSIFCloseL, VSIFReadL, VSIFWriteL, VSIFSeekL, VSIFTellL,
    VSIFTruncateL, VSIStatL, Unlink, Rename, FileFromMemBuffer
)


def open(filename, mode="r"):
    return VSIFile(filename)

rename = Rename

unlink = remove = Unlink


class VSIFile(object):
    """ File-like object interface for VSI file API.
    """

    def __init__(self, filename, mode="r"):
        self._handle = VSIFOpenL(filename, mode)
        self._filename = filename


    @property
    def filename(self):
        return self._filename


    def read(self, size=None):
        if size is None:
            size = self.size - self.tell()
        return VSIFReadL(1, size, self._handle)


    def write(self, data):
        VSIFWriteL(len(data), 1, data, self._handle)


    def tell(self):
        return VSIFTellL(self._handle)


    def seek(self, offset, whence=os.SEEK_SET):
        VSIFSeekL(self._handle, offset, whence)


    def close(self):
        if self._handle is not None:
            VSIFCloseL(self._handle)
        self._handle = None


    @property
    def closed(self):
        return (self._handle is None)


    @property
    def size(self):
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
        if not filename:
            filename = "/vsimem/%s" % uuid4().hex()
        gdal.FileFromBuffer(filename, buf)
        return cls(mode)

    def close(self):
        super(TemporaryVSIFile, self).close()
        remove(self.filename)
