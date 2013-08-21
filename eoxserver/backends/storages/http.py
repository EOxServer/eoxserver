
from urllib import urlretrieve
from urlparse import urljoin

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import FileStorageInterface


class HTTPStorage(Component):
    implements(FileStorageInterface)


    name = "HTTP"

    def validate(self, url):
        pass

    def retrieve(self, url, location, path):
        urlretrieve(urljoin(url, location), path)
