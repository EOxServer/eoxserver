from os import path
from urlparse import urlparse

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import FileStorageInterface


class LocalStorage(Component):
    implements(FileStorageInterface)


    name = "local"

    def retrieve(self, url, location, path):
        return path.join(url, location)
