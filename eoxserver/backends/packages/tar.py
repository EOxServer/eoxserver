
from tarfile import TarFile
from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import PackageInterface


class TARPackage(Component):
    implements(PackageInterface)


    name = "TAR"

    def extract(self, package_filename, location, path):
        tarfile = TarFile(package_filename, "r")
        tarfile.extract(location, path)

    
    def list_files(self, package_filename):
        tarfile = TarFile(package_filename, "r")
        # TODO: get list
