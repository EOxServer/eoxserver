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


import tarfile
import io


gzip_mimes = ("application/gzip", "application/x-gzip")
bzip_mimes = ("application/bzip", "application/x-bzip")
mime_list = ("application/tar", "application/x-tar") + gzip_mimes + bzip_mimes


class TarPackageWriter(object):
    """ Package writer for compressed and uncompressed tar files.
    """

    def supports(self, format, params):
        return format.lower() in mime_list

    def create_package(self, filename, format, params):
        if format in gzip_mimes:
            mode = "w:gz"
        elif format in bzip_mimes:
            mode = "w:bz2"
        else:
            mode = "w"

        return tarfile.open(filename, mode)

    def cleanup(self, package):
        package.close()

    def add_to_package(self, package, data, size, location):
        info = tarfile.TarInfo(location)
        info.size = size
        package.addfile(info, io.BytesIO(data))

    def get_mime_type(self, package, format, params):
        return "application/x-compressed-tar"

    def get_file_extension(self, package, format, params):
        if format in gzip_mimes:
            return ".tar.gz"

        elif format in bzip_mimes:
            return ".tar.bz2"

        return ".tar"
