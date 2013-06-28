
from eoxserver.core import env, Component, implements, ExtensionPoint
from eoxserver.backends.interfaces import *


class BackendComponent(Component):
    data_readers = ExtensionPoint(DataReaderInterface)
    storages = ExtensionPoint(StorageInterface)
    packages = ExtensionPoint(PackageInterface)

    def get_storage_component(self, storage_type):
        storage_type = storage_type.upper()
        result_component = None
        for storage_component in self.storages:
            if storage_component.name.upper() == storage_type:
                if result_component is not None:
                    raise Exception("Ambigouus storage component")
                result_component = storage_component

        return result_component


    def get_package_component(self, format):
        format = format.upper()
        result_component = None
        for package_component in self.packages:
            if package_component.name.upper() == format:
                if result_component is not None:
                    raise Exception("Ambigouus package component")
                result_component = package_component

        return result_component






BackendComponent(env)

