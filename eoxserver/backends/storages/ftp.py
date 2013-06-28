
from os import path
from ftplib import FTP
from urlparse import urlparse

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import StorageInterface


class FTPStorage(Component):
    implements(StorageInterface)


    name = "FTP"

    def retrieve(self, url, location, result_path):
        parsed = urlparse(url)
        ftp = FTP()
        print parsed.hostname, parsed.port, parsed.username, parsed.password
        ftp.connect(parsed.hostname, parsed.port)
        ftp.login(parsed.username, parsed.password)



        try:
            cmd = "RETR %s" % path.join(parsed.path, location)
            print cmd

            with open(result_path, 'wb') as local_file:
                ftp.retrbinary(cmd, local_file.write)

        finally:
            ftp.quit()
