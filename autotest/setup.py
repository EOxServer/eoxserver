import os

from setuptools.command import sdist
del sdist.finders[:]

from setuptools import setup
from setuptools.command.install import install as _install

from eoxserver import get_version

class install(_install):
    def run(self):
        _install.run(self)
        
        self.prefix
version = get_version()

data_files = []
for dirpath, dirnames, filenames in os.walk('data'):
    data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='EOxServer Autotest',
    version=version.replace(' ', '-'),
    
    data_files=data_files,
    
    install_requires=['eoxserver'],
    
    # Metadata
    author="EOX IT Services GmbH",
    author_email="office@eox.at",
    
    description="",
    long_description="",

    cmdclass={'install': install},
)