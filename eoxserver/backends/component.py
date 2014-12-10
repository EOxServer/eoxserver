#-------------------------------------------------------------------------------
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


import itertools

from eoxserver.core import env, Component, ExtensionPoint
from eoxserver.backends.interfaces import *


class BackendComponent(Component):
    """ This :class:`Component <eoxserver.core.component.Component>` provides
    extension points and helpers to easily retrive Package and Storage
    components by their type names.
    """

    file_storages = ExtensionPoint(FileStorageInterface)
    connected_storages = ExtensionPoint(ConnectedStorageInterface)
    packages = ExtensionPoint(PackageInterface)

    @property
    def storages(self):
        """ Helper to retrieve components for all storage interfaces.
        """
        return itertools.chain(self.file_storages, self.connected_storages)

    def get_file_storage_component(self, storage_type):
        """ Retrieve a component implementing the
        :class:`eoxserver.backends.interfaces.FileStorageInterface` with the
        desired ``storage_type``.

        :param storage_type: the desired storage type
        :returns: the desired storage component or ``None``
        """

        storage_type = storage_type.upper()
        result_component = None
        for storage_component in self.file_storages:
            if storage_component.name.upper() == storage_type:
                if result_component is not None:
                    raise Exception("Ambigouus storage component")
                result_component = storage_component

        return result_component

    def get_connected_storage_component(self, storage_type):
        """ Retrieve a component implementing the
        :class:`eoxserver.backends.interfaces.ConnectedStorageInterface` with
        the desired ``storage_type``.

        :param storage_type: the desired storage type
        :returns: the desired storage component or ``None``
        """

        storage_type = storage_type.upper()
        result_component = None
        for storage_component in self.connected_storages:
            if storage_component.name.upper() == storage_type:
                if result_component is not None:
                    raise Exception("Ambigouus storage component")
                result_component = storage_component

        return result_component

    def get_storage_component(self, storage_type):
        """ Retrieve a component implementing the
        :class:`eoxserver.backends.interfaces.FileStorageInterface` or
        :class:`eoxserver.backends.interfaces.ConnectedStorageInterface` with
        the desired ``storage_type``.

        :param storage_type: the desired storage type
        :returns: the desired storage component or ``None``
        """

        file_storage = self.get_file_storage_component(storage_type)
        connected_storage = self.get_connected_storage_component(storage_type)

        if file_storage is not None and connected_storage is not None:
            raise Exception("Ambigouus storage component")

        return file_storage or connected_storage

    def get_package_component(self, format):
        """ Retrieve a component implementing the
        :class:`eoxserver.backends.interfaces.PackageInterface` with
        the desired ``format``.

        :param format: the desired package format
        :returns: the desired package component or ``None``
        """

        format = format.upper()
        result_component = None
        for package_component in self.packages:
            if package_component.name.upper() == format:
                if result_component is not None:
                    raise Exception("Ambigouus package component")
                result_component = package_component

        return result_component


BackendComponent(env)
