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


from os import path
from ftplib import FTP
from urlparse import urlparse

from django.core.exceptions import ValidationError

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import FileStorageInterface


class FTPStorage(Component):
    implements(FileStorageInterface)

    name = "FTP"

    def validate(self, url):
        parsed = urlparse(url)
        if not parsed.hostname:
            raise ValidationError(
                "Invalid FTP URL: could not determine hostname."
            )
        if parsed.scheme and parsed.scheme.upper() != "FTP":
            raise ValidationError(
                "Invalid FTP URL: invalid scheme 's'." % parsed.scheme
            )

    def retrieve(self, url, location, result_path):
        """ Retrieves the file referenced by `location` from the server 
            specified by its `url` and stores it under the `result_path`.
        """
        
        ftp, parsed_url = self._open(url)

        try:
            cmd = "RETR %s" % path.join(parsed_url.path, location)
            with open(result_path, 'wb') as local_file:
                ftp.retrbinary(cmd, local_file.write)

        finally:
            ftp.quit()


    def list_files(self, url, location):
        ftp, parsed_url = self._open(url)

        try:
            return ftp.nlst(location)
        except ftplib.error_perm, resp:
            if str(resp).startswith("550"):
                return []
            else:
                raise
        finally:
            ftp.quit()


    def _open(self, url):
        parsed_url = urlparse(url)
        ftp = FTP()
        ftp.connect(parsed_url.hostname, parsed_url.port)
        # TODO: default username/password?
        ftp.login(parsed_url.username, parsed_url.password)

        return ftp, parsed_url
