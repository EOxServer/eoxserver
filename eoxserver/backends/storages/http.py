
from urllib import urlretrieve
from urlparse import urljoin
from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import StorageInterface


class HTTPStorage(Component):
    implements(StorageInterface)


    name = "HTTP"

    def retrieve(self, url, location, path):
        urlretrieve(urljoin(url, location), path)
