
from os import path
from ftplib import FTP
from urlparse import urlparse

from django.core.exceptions import ValidationError

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import StorageInterface


class FTPStorage(Component):
    implements(StorageInterface)

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
        parsed = urlparse(url)
        ftp = FTP()
        ftp.connect(parsed.hostname, parsed.port)
        # TODO: default username/password?
        ftp.login(parsed.username, parsed.password)

        try:
            cmd = "RETR %s" % path.join(parsed.path, location)
            with open(result_path, 'wb') as local_file:
                ftp.retrbinary(cmd, local_file.write)

        finally:
            ftp.quit()
