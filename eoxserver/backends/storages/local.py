
from os import path
from urlparse import urlparse

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import StorageInterface


class LocalStorage(Component):
    implements(StorageInterface)


    name = "local"

    def retrieve(self, url, location, path):
        # TODO: implement! ;)
        # should not be too hard
        pass
