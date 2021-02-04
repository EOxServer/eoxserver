# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------

import os.path
import shutil
import tarfile
import zipfile
import fnmatch
from django.utils.six.moves.urllib import parse, request

import ftplib
import glob

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.contrib import vsi
from eoxserver.backends.config import DEFAULT_EOXS_STORAGE_HANDLERS


class BaseStorageHandler(object):
    """ Storage Handlers must conform to the context manager protocol
    """

    name = None  # short name of the storage handler

    allows_child_storages = False
    allows_parent_storage = False

    is_local = False

    def __enter__(self):
        """ Perform setup actions. Will be called before ``retrieve`` and
            ``list_files``.
        """
        return self

    def __exit__(self, type, value, traceback):
        """ Perform teardown actions. Will be called when the storage is no
            longer used.
        """
        pass

    def retrieve(self, location, path):
        """ Retrieve the file specified by `location` under the given local
            `path`. The path is only a hint, when a string is returned, this
            indicates that the file was instead stored in that location.
            Should be implemented by storage handlers that deal with
            files or similar objects.
        """
        raise NotImplementedError

    def list_files(self, glob_pattern=None):
        """ List the files in that storage, optionally filtered by a glob. Should
            be implemented for storages dealing with files, when possible.
        """
        raise NotImplementedError

    def get_vsi_path(self, location):
        """ Get the VSI file path for the file specified by location. This path
            can be used in GDAL based APIs to directly adress files.
        """
        raise NotImplementedError

    def get_vsi_env(self):
        """
        """
        return {}

    @classmethod
    def test(cls, locator):
        """ Check if a locator refers to a storage that can be handled by this
            handler class.
        """
        raise NotImplementedError


class ZIPStorageHandler(BaseStorageHandler):
    """Implementation of the storage interface for ZIP storages.
    """

    name = "ZIP"

    allows_child_storages = True
    allows_parent_storage = True

    is_local = True

    def __init__(self, package_filename):
        self.package_filename = package_filename
        self.zipfile = None

    def __enter__(self):
        self.zipfile = zipfile.ZipFile(self.package_filename, "r")
        return self

    def __exit__(self, type, value, traceback):
        self.zipfile.close()
        self.zipfile = None

    def retrieve(self, location, path):
        infile = self.zipfile.open(location)
        with open(path, "wb") as outfile:
            shutil.copyfileobj(infile, outfile)
        return True, path

    def list_files(self, glob_pattern=None):
        filenames = self.zipfile.namelist()
        if glob_pattern:
            filenames = fnmatch.filter(filenames, glob_pattern)
        return filenames

    def get_vsi_path(self, location):
        return '/vsizip/%s/%s' % (self.package_filename, location)

    @classmethod
    def test(cls, locator):
        return zipfile.is_zipfile(locator)


class TARStorageHandler(BaseStorageHandler):
    """Implementation of the storage interface for ZIP storages.
    """

    name = "TAR"

    allows_child_storages = True
    allows_parent_storage = True

    is_local = True

    def __init__(self, package_filename):
        self.package_filename = package_filename
        self.tarfile = None

    def __enter__(self):
        self.tarfile = tarfile.TarFile(self.package_filename, "r")
        return self

    def __exit__(self, type, value, traceback):
        self.tarfile.close()
        self.tarfile = None

    def retrieve(self, location, path):
        self.tarfile.extract(location, path)
        return True, path

    def list_files(self, glob_pattern=None):
        filenames = self.tarfile.getnames()
        if glob_pattern:
            filenames = fnmatch.filter(filenames, glob_pattern)
        return filenames

    def get_vsi_path(self, location):
        return '/vsitar/%s/%s' % (self.package_filename, location)

    @classmethod
    def test(cls, locator):
        try:
            return tarfile.is_tarfile(locator)
        except IOError:
            return False


class DirectoryStorageHandler(BaseStorageHandler):
    """
    """

    name = 'directory'

    allows_child_storages = True
    allows_parent_storage = True

    is_local = True

    def __init__(self, dirpath):
        self.dirpath = dirpath

    def retrieve(self, location, path):
        return False, os.path.join(self.dirpath, location)

    def list_files(self, glob_pattern=None):
        glob_pattern = glob_pattern or '*'
        return glob.glob(os.path.join(self.dirpath, glob_pattern))

    def get_vsi_path(self, location):
        return os.path.join(self.dirpath, location)

    @classmethod
    def test(cls, locator):
        return os.path.isdir(locator)


class HTTPStorageHandler(BaseStorageHandler):
    """
    """

    name = 'HTTP'

    allows_child_storages = True
    allows_parent_storage = False

    def __init__(self, url):
        self.url = url

    def retrieve(self, location, path):
        request.urlretrieve(parse.urljoin(self.url, location), path)
        return True, path

    def get_vsi_path(self, location):
        return '/vsicurl/%s' % parse.urljoin(self.url, location)

    @classmethod
    def test(cls, locator):
        try:
            return urlparse(locator).scheme.lower() in ('http', 'https')
        except:
            return False


class FTPStorageHandler(BaseStorageHandler):
    """
    """

    name = 'FTP'

    allows_parent_storage = True
    allows_parent_storage = False

    def __init__(self, url):
        self.url = url
        self.parsed_url = urlparse(url)
        self.ftp = None

    def __enter__(self):
        self.ftp = ftplib.FTP()
        self.ftp.connect(self.parsed_url.hostname, self.parsed_url.port)
        self.ftp.login(self.parsed_url.username, self.parsed_url.password)
        return self

    def __exit__(self, type, value, traceback):
        self.ftp.quit()
        self.ftp = None

    def retrieve(self, location, path):
        cmd = "RETR %s" % os.path.join(self.parsed_url.path, location)
        with open(path, 'wb') as local_file:
            self.ftp.retrbinary(cmd, local_file.write)
        return True, path

    def list_files(self, location, glob_pattern=None):
        try:
            filenames = self.ftp.nlst(location)
        except ftplib.error_perm as resp:
            if str(resp).startswith("550"):
                filenames = []
            else:
                raise
        if glob_pattern:
            filenames = fnmatch.filter(filenames, glob_pattern)
        return filenames

    def get_vsi_path(self, location):
        return '/vsicurl/%s' % parse.urljoin(self.url, location)

    @classmethod
    def test(cls, locator):
        try:
            return urlparse(locator).scheme.lower() == 'ftp'
        except:
            return False


class SwiftStorageHandler(BaseStorageHandler):
    name = 'swift'

    allows_parent_storage = False
    allows_child_storages = True

    def __init__(self, url):
        self.container = url

    def retrieve(self, location, path):
        pass

    def list_files(self, location, glob_pattern=None):
        return []

    def get_vsi_path(self, location):
        return vsi.join('/vsiswift/%s' % self.container, location)

    @classmethod
    def test(cls, locator):
        return False


class S3StorageHandler(BaseStorageHandler):
    name = 'S3'

    allows_parent_storage = False
    allows_child_storages = True

    def __init__(self, url):
        self.bucket = url

    def retrieve(self, location, path):
        pass

    def list_files(self, location, glob_pattern=None):
        return []

    def get_vsi_path(self, location):
        import logging
        logger = logging.getLogger(__name__)

        # logger.debug()


        base_path = '/vsis3/%s' % self.bucket if self.bucket else '/vsis3'
        return vsi.join(base_path, location)

    @classmethod
    def test(cls, locator):
        return False


# API to setup and retrieve the configured storage handlers

STORAGE_HANDLERS = None


def _setup_storage_handlers():
    """ Setup the storage handlers. Uses the ``EOXS_STORAGE_HANDLERS`` setting
        which falls back to the ``DEFAULT_EOXS_STORAGE_HANDLERS``
    """
    global STORAGE_HANDLERS
    specifiers = getattr(
        settings, 'EOXS_STORAGE_HANDLERS', DEFAULT_EOXS_STORAGE_HANDLERS
    )
    STORAGE_HANDLERS = [import_string(specifier) for specifier in specifiers]


def get_handlers():
    if STORAGE_HANDLERS is None:
        _setup_storage_handlers()

    return STORAGE_HANDLERS


def get_handler_by_test(locator):
    """ Test the given locator with the configured storage handlers and return the stora
    """
    if STORAGE_HANDLERS is None:
        _setup_storage_handlers()

    for storage_handler_cls in STORAGE_HANDLERS:
        try:
            if storage_handler_cls.test(locator):
                return storage_handler_cls(locator)
        except AttributeError:
            pass


def get_handler_class_by_name(name):
    if STORAGE_HANDLERS is None:
        _setup_storage_handlers()

    for storage_handler_cls in STORAGE_HANDLERS:
        try:
            if storage_handler_cls.name == name:
                return storage_handler_cls
        except AttributeError:
            pass


def get_handler_class_for_model(storage_model):
    return get_handler_class_by_name(storage_model.storage_type)


def get_handler_for_model(storage_model):
    return get_handler_class_for_model(storage_model)(storage_model.url)
