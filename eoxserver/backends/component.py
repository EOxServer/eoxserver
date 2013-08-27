import itertools

from eoxserver.core import env, Component, implements, ExtensionPoint
from eoxserver.backends.interfaces import *


class BackendComponent(Component):
    data_readers = ExtensionPoint(DataReaderInterface)
    file_storages = ExtensionPoint(FileStorageInterface)
    connected_storages = ExtensionPoint(ConnectedStorageInterface)
    packages = ExtensionPoint(PackageInterface)


    @property
    def storages(self):
        """ Helper for all storages.
        """
        return itertools.chain(self.file_storages, self.connected_storages)
    

    def get_file_storage_component(self, storage_type):
        storage_type = storage_type.upper()
        result_component = None
        for storage_component in self.file_storages:
            if storage_component.name.upper() == storage_type:
                if result_component is not None:
                    raise Exception("Ambigouus storage component")
                result_component = storage_component

        return result_component


    def get_connected_storage_component(self, storage_type):
        storage_type = storage_type.upper()
        result_component = None
        for storage_component in self.connected_storages:
            if storage_component.name.upper() == storage_type:
                if result_component is not None:
                    raise Exception("Ambigouus storage component")
                result_component = storage_component

        return result_component


    def get_storage_component(self, storage_type):
        file_storage = self.get_file_storage_component(storage_type)
        connected_storage = self.get_connected_storage_component(storage_type)

        if file_storage is not None and connected_storage is not None:
            raise Exception("Ambigouus storage component")

        return file_storage or connected_storage


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
