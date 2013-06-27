

""" This module provides Python file-object like access to VSI files.
"""


import os

from gdal import (
    VSIFOpenL, VSIFCloseL, VSIFReadL, VSIFWriteL, VSIFSeekL, VSIFTellL
)


def open(filename, mode="r"):
    return VSIFile(filename)


class VSIFile(object):
    def __init__(self, filename, mode):
        self._handle = VSIFOpenL(filename, mode)
        self.filename = filename


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
        VSIFCloseL(self._handle)
        self._handle = None


    @property
    def closed(self):
        return (self._handle is None)

    @property
    def size(self):
        stat = VSIStatL(self.filename)
        return stat.size
