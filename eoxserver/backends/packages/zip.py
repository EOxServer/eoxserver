
from zipfile import ZipFile
from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import PackageInterface


class ZIPPackage(Component):
    """Implementation of the package interface for ZIP package files.
    """
    
    implements(PackageInterface)

    name = "ZIP"

    def extract(self, package_filename, location, path):
        zipfile = ZipFile(package_filename, "r")
        zipfile.extract(location, path)

    
    def list_files(self, package_filename):
        zipfile = ZipFile(package_filename, "r")
        # TODO: get list
