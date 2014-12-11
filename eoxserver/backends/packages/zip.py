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


import shutil
from zipfile import ZipFile
import re

from eoxserver.core import Component, implements
from eoxserver.backends.interfaces import PackageInterface


class ZIPPackage(Component):
    """Implementation of the package interface for ZIP package files.
    """

    implements(PackageInterface)

    name = "ZIP"

    def extract(self, package_filename, location, path):
        zipfile = ZipFile(package_filename, "r")
        infile = zipfile.open(location)
        with open(path, "wb") as outfile:
            shutil.copyfileobj(infile, outfile)

    def list_files(self, package_filename, location_regex=None):
        zipfile = ZipFile(package_filename, "r")
        filenames = zipfile.namelist()
        if location_regex:
            filenames = [f for f in filenames if re.match(location_regex, f)]
        return filenames
