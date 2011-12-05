#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""
This module implements the local storage backend for EOxServer.
"""

import os.path
import shutil

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.core.util.filetools import findFiles
from eoxserver.backends.interfaces import (
    StorageInterface, LocalPathInterface
)
from eoxserver.backends.models import LocalPath
from eoxserver.backends.base import LocationWrapper
from eoxserver.backends.exceptions import DataAccessError

class LocalStorage(object):
    """
    This is a wrapper for the storage on the local file system.
    """
    
    REGISTRY_CONF = {
        "name": "Local Storage",
        "impl_id": "backends.local.LocalStorage",
        "registry_values": {
            "backends.interfaces.storage_type": "local"
        }
    }
    
    def getType(self):
        """
        Returns ``"local"``.
        """
        return "local"
        
    def getStorageCapabilities(self):
        """
        Returns the names of the optional methods implemented by the storage.
        Currently ``("getSize", "getLocalCopy", "detect")``.
        """
        return ("getSize", "getLocalCopy", "detect")

    def getSize(self, location):
        """
        Returns the size (in bytes) of the object at the location or ``None``
        if it cannot be retrieved.
        """
        try:
            return os.path.getsize(location.getPath())
        except:
            return None

    def getLocalCopy(self, location, target):
        """
        Makes a local copy of the file at ``location`` at the path ``target``
        and returns the location of the copy (i.e. a :class:`LocalPathWrapper`
        instance). Raises :exc:`~.InternalError` if the location does not refer
        to an object on the local file system or :exc:`~.DataAccessError` if
        copying fails.
        """
        if location.getType() != "local":
            raise InternalError(
                "Location type '%s' not supported by local storage." %\
                location.getType()
            )
        
        try:
            shutil.copy(location.getPath(), target)
        except:
            raise DataAccessError(
                "Could not copy object at '%s' to '%s'" % (
                    location.getPath(),
                    target
                )
            )
        
        if os.path.isdir(target):
            return System.getRegistry().bind("backends.factories.LocationFactory").create(
                type = "local",
                path = os.path.join(
                    target, os.path.basename(location.getPath())
                )
            )
        else:
            return System.getRegistry().bind("backends.factories.LocationFactory").create(
                type = "local",
                path = target
            )
    
    def detect(self, location, search_pattern=None):
        """
        Recursively detects files whose name matches ``search_pattern`` in the
        directory tree under ``location`` and returns their locations as a list
        of :class:`LocalPathWrapper` instances. If ``search_pattern`` is omitted
        all files found are returned.
        """
        if location.getType() != "local":
            raise InternalError(
                "Location type '%s' not supported by local storage." %\
                location.getType()
            )
        
        if search_pattern is None:
            _pattern = "*"
        else:
            _pattern = search_pattern
        
        paths = findFiles(location.getPath(), _pattern)
        
        factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        return [
            factory.create(type="local", path=path) for path in paths
        ]
    
    def exists(self, location):
        return os.path.exists(location.getPath())
        
LocalStorageImplementation = StorageInterface.implement(LocalStorage)

class LocalPathWrapper(LocationWrapper):
    """
    This a wrapper for locations on the local file system. It inherits from
    :class:`~.LocationWrapper`.
    
    .. method:: setAttrs(**kwargs)

       The ``path`` keyword argument is mandatory; it is expected to contain
       the path to the location on the local file system.
    """
    
    REGISTRY_CONF = {
        "name": "Local Path Wrapper",
        "impl_id": "backends.local.LocalPathWrapper",
        "factory_ids": (
            "backends.factories.LocationFactory",
        )
    }
    
    def __init__(self):
        super(LocalPathWrapper, self).__init__()
        
        self.path = None

    def getType(self):
        """
        Returns ``"local"``.
        """
        return "local"
    
    def getPath(self):
        """
        Returns the path to the location on the local file system.
        """
        if self.record:
            return self.record.path
        else:
            return self.path
    
    def open(self, mode='r'):
        """
        Opens the file at the location on the local file system and return
        the :class:`file` object. The ``mode`` flag is passed to the builtin
        :func:`open` function and defaults to ``'r'`` read only. Raises
        :exc:`~.DataAccessError` if the object at the location is not a file
        or cannot be opened for some other reason.
        """
        path = self.getPath()
        
        if os.path.exists(path):
            if os.path.isfile(path):
                try:
                    return open(path, 'r')
                except Exception, e:
                    raise DataAccessError(
                        "Could not open file '%s'. Error message: '%s'" % (
                            path, str(e)
                        )
                    )
            else:
                raise DataAccessError(
                    "Object at path '%s' is not a file and cannot be opened." %\
                    path
                )
        else:
            raise DataAccessError(
                "Could not open file '%s'. Path does not exist." % path
            )
    
    def _bind_to_storage(self):
        return System.getRegistry().bind("backends.local.LocalStorage")
        
    def _validate_record(self, record):
        if record.location_type != "local":
            raise InternalError(
                "Cannot assign a '%s' record to a local path wrapper." %\
                record.location_type
            )

    def _set_record(self, record):
        if isinstance(record, LocalPath):
            self.record = record
        else:
            self.record = record.localpath
            
    def _validate_attrs(self, **kwargs):
        if "path" not in kwargs:
            raise InternalError(
                "The 'path' keyword argument is required to initialize a local path wrapper."
            )
    
    def _set_attrs(self, **kwargs):
        self.path = kwargs["path"]
        
    def _fetch_unique_record(self):
        # no uniqueness constraints apply
        
        return None
    
    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "path" in fields:
            query["path"] = self.getPath()
        
        return query
    
    def _get_query_set(self, query):
        return LocalPath.objects.filter(**query)
        
    def _create_record(self):
        self.record = LocalPath.objects.create(
            location_type = LocalPath.LOCATION_TYPE,
            path = self.path
        )

LocalPathImplementation = \
LocalPathInterface.implement(LocalPathWrapper)
