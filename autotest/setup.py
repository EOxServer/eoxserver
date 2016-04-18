#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

import os

# Hack to remove setuptools "feature" which resulted in
# ignoring MANIFEST.in when code is in an svn repository.
# TODO find a nicer solution
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
for dirpath, dirnames, filenames in os.walk('autotest/data'):
    data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup(
    name='EOxServer_autotest',
    version=version.replace(' ', '-'),
    # TODO: packages
    data_files=data_files,
    
    install_requires=['eoxserver'],
    
    # Metadata
    author="EOX IT Services GmbH",
    author_email="office@eox.at",
    maintainer="EOX IT Services GmbH",
    maintainer_email="packages@eox.at",
    
    description="Autotest instance for EOxServer",
    long_description="",
    
    license="EOxServer Open License (MIT-style)",
    keywords="Earth Observation, EO, OGC, WCS, WMS",
    url="http://eoxserver.org/",
    
    cmdclass={'install': install},
)
