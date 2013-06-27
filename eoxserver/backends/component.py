
from eoxserver.core import env, Component, implements, ExtensionPoint
from eoxserver.backends.interfaces import *

class BackendComponent(Component):
    data_readers = ExtensionPoint(DataReaderInterface)

    storages = ExtensionPoint(StorageInterface)

    packages = ExtensionPoint(PackageInterface)




BackendComponent(env)

