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
This module provides the implementation of the FTP remote file backend.
"""

import os.path
from fnmatch import fnmatch
from ftplib import (
    FTP, error_perm as ftplib_error_perm,
    error_temp as ftplib_error_temp
)
import logging

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.backends.interfaces import (
    StorageInterface, RemotePathInterface
)
from eoxserver.backends.models import FTPStorage as FTPStorageRecord
from eoxserver.backends.models import RemotePath
from eoxserver.backends.base import LocationWrapper
from eoxserver.backends.exceptions import DataAccessError

logger = logging.getLogger(__name__)

class FTPStorage(object):
    """
    This is an implementation of the :class:`~.StorageInterface` for
    accessing files on a remote FTP server.
    
    Note that internally, it creates a persistent connection that may
    be used for multiple requests on the same location or requests for
    multiple locations on the same server. DO NOT try to connect to
    different servers using the same :class:`FTPStorage` instance
    however, this will cause trouble and most definitely not work!
    """
    
    REGISTRY_CONF = {
        "name": "FTP Storage Interface",
        "impl_id": "backends.ftp.FTPStorage",
        "registry_values": {
            "backends.interfaces.storage_type": "ftp"
        }
    }
    
    def __init__(self):
        self.ftp = None
    
    def __del__(self):
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                self.ftp.close()

    def getType(self):
        """
        Returns ``"ftp"``.
        """
        
        return "ftp"
    
    def getStorageCapabilities(self):
        """
        Returns the storage capabilities, i.e. the names of the optional methods
        implemented by the storage. Currently
        ``("getSize", "getLocalCopy", "detect")``.
        """
        
        return ("getSize", "getLocalCopy", "detect")
    
    def getSize(self, location):
        """
        Returns the size of the object at ``location``. Note that not all
        FTP implementations are able to respond to this call. In that case
        ``None`` will be returned.
        """
        
        self._connect(location)
        
        return self.ftp.size(location.getPath())
        
    def getLocalCopy(self, location, target):
        """
        Copies the file at the remote ``location`` to the
        ``target`` path on the local file system. The parameter
        ``location`` is expected to be an instance of
        :class:`RemotePathWrapper`, ``target`` is expected to be a
        string denoting the destination path.
        
        The method raises :exc:`~.InternalError` in case the location is
        not of appropriate type and :exc:`~.DataAccessError` in case
        an error occurs while copying the resources.
        """
        
        # check location type
        if location.getType() != "ftp":
            raise InternalError(
                "Cannot open '%s' location with FTP storage." %\
                location.getType()
            )
        
        # determine the local path
        if os.path.exists(target) and os.path.isdir(target):
            dest_path = os.path.join(
                target, os.path.basename(location.getPath())
            )
        else:
            dest_path = target
        
        # create FTP connection
        self._connect(location)
        
        # retrieve the given file
        cmd = "RETR %s" % location.getPath()
        
        try:
            local_file = open(dest_path, 'wb')
        except Exception, e:
            raise DataAccessError(
                "Could not open destination file '%s'. Error message: '%s'" % (
                    dest_path, str(e)
                )
            )
        
        logger.info("Get remote file '%s'" % location.getPath())
        logger.info("Write to local path '%s'" % dest_path)
        
        try:
            self.ftp.retrbinary(cmd, local_file.write)
        except Exception, e:
            raise DataAccessError(
                "Retrieving data for file '%s' on '%s' via FTP failed. Error message: '%s'" % (
                    location.getPath(), location.getHost(), str(e)
                )
            )
        
        # we have successfully written the file; clean up
        local_file.close()
        
        # return the file location
        return System.getRegistry().bind(
            "backends.factories.LocationFactory"
        ).create(
            type="local", path=dest_path
        )
    
    def detect(self, location, search_pattern=None):
        """
        Recursively detects files in a directory tree and returns their
        locations. This will raise :exc:`~.DataAccessError` if the object at
        ``location`` is not a directory.
        """
        self._connect(location)
        
        paths = self._recursive_nlst(location.getPath(), search_pattern)
        
        factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        return [
            factory.create(
                type="ftp",
                host = location.getHost(),
                port = location.getPort(),
                user = location.getUser(),
                passwd = location.getPassword(),
                path = path
            )
            
            for path in paths
        ]
    
    def exists(self, location):
        """
        Checks the existance of a certain location within the storage.
        Returns `True` if the location exists and `False` if not or the
        location is not accessible.
        """
        try:
            if self.ftp.nlst(location.getPath()):
                return True
            else:
                return False
        except ftplib_error_temp:
            return False
            
        
    def _recursive_nlst(self, search_path, search_pattern=None):
        # this does a recursive search of an FTP directory
        #
        # raises :exc:`DataAccessError` if the NLST FTP command fails
        
        try:
            found_paths = self.ftp.nlst(search_path)
        except Exception, e:
            raise DataAccessError(
                "Could not list remote directory '%s'. Error message: '%s'" % (
                    search_path, str(e)
                )
            )
        
        file_paths = []
        
        for path in found_paths:
            # try to change to the directory called name; this will fail
            # if the object called name is not a directory.
            # Unfortunately this is the most straightforward way of
            # checking whether the object called name is a directory.
            #
            # if it is not a directory, check if it matches the search
            # pattern (if any) and append to the list of found paths.
            #
            # if another error occurred, raise :exc:`~.DataAccessError`
            try:
                cur_dir = self.ftp.pwd()
                self.ftp.cwd(path)
                self.ftp.cwd(cur_dir)
                
                file_paths.extend(
                    self._recursive_nlst(path, search_pattern)
                )
            except ftplib_error_perm:
                if (search_pattern and fnmatch(os.path.basename(path), search_pattern)) \
                   or not search_pattern:
                    file_paths.append(path)
            except Exception, e:
                raise DataAccessError(
                    "Could not search directory tree '%s'. Error message: '%s'" % (
                        search_path, str(e)
                    )
                )
                
        return file_paths
        
    def _connect(self, location):
        # This method establishes an FTP connection with the host the
        # location is situated on.
        #
        # see also the comment in the class's docstring
        
        if self.ftp:
            return self.ftp
        else:
            self.ftp = FTP()

            try:
                if location.getPort() is None:
                    self.ftp.connect(location.getHost())
                else:
                    self.ftp.connect(location.getHost(), location.getPort())
                
                if location.getUser() is None:
                    self.ftp.login()
                else:
                    if location.getPassword() is None:
                        self.ftp.login(location.getUser())
                    else:
                        self.ftp.login(location.getUser(), location.getPassword())
                
                self.ftp.sendcmd('TYPE I') # set to binary mode; needed for getSize
                self.ftp.set_pasv(False) # turn passive mode off; there seem to be problems with it
                
            except Exception, e:
                raise DataAccessError(
                    "Could not connect to FTP host '%s'. Error message: '%s'" % (
                        location.getHost(), str(e)
                    )
                )

FTPStorageImplementation = StorageInterface.implement(FTPStorage)

class RemotePathWrapper(LocationWrapper):
    """
    This is a wrapper class for remote paths. It inherits from
    :class:`~.LocationWrapper`.

    .. method:: setAttrs(**kwargs)
    
       This method is called to initialize the wrapper. The following attribute
       keyword arguments are accepted:
       
       * ``host`` (required): the FTP host name
       * ``port`` (optional): the FTP port number
       * ``user`` (optional): the user name to be used for login
       * ``passwd`` (optional): the password to be used for login
       * ``path`` (required): the path to the location on the remote server

    """
    
    REGISTRY_CONF = {
        "name": "Remote Path Wrapper",
        "impl_id": "backends.ftp.RemotePathWrapper",
        "factory_ids": (
            "backends.factories.LocationFactory",
        )
    }
    
    def __init__(self):
        super(RemotePathWrapper, self).__init__()
        
        self.host = None
        self.port = None
        self.user = None
        self.passwd = None
        self.path = None
    
    def getType(self):
        """
        Returns ``"ftp"``.
        """
        return "ftp"
    
    def getStorageType(self):
        """
        Returns ``"ftp"``.
        """
        return "ftp"
        
    def getHost(self):
        """
        Returns the FTP host name.
        """
        if self.record:
            return self.record.storage.host
        else:
            return self.host
        
    def getPort(self):
        """
        Returns the FTP port number or ``None`` if it has not been defined.
        """
        if self.record:
            return self.record.storage.port
        else:
            return self.port
    
    def getUser(self):
        """
        Returns the user name to be used for login to the remote server or
        ``None`` if it has not been defined.
        """
        if self.record:
            return self.record.storage.user
        else:
            return self.user
    
    def getPassword(self):
        """
        Returns the password to be used for login to the remote server or
        ``None`` if it has not been defined.
        """
        if self.record:
            return self.record.storage.passwd
        else:
            return self.passwd
    
    def getPath(self):
        """
        Returns the path on the remote server.
        """
        if self.record:
            return self.record.path
        else:
            return self.path

        
    def _bind_to_storage(self):
        return System.getRegistry().bind("backends.ftp.FTPStorage")
    
            
    def _validate_record(self, record):
        if record.location_type != "ftp":
            raise InternalError(
                "Cannot assign a '%s' type location record to remote path location." %\
                record.location_type
            )
            
    def _set_record(self, record):
        if isinstance(record, RemotePath):
            self.record = record
        else:
            self.record = record.remotepath
    
    def _validate_attrs(self, **kwargs):
        if "path" not in kwargs or "host" not in kwargs:
            raise InternalError(
                "The 'path' and 'host' keyword arguments must be submitted to create a remote path instance."
            )
    
    def _set_attrs(self, **kwargs):
        self.path = kwargs["path"]
        self.host = kwargs["host"]
        
        self.port = kwargs.get("port")
        self.user = kwargs.get("user")
        self.passwd = kwargs.get("passwd")
    
    def _fetch_unique_record(self):
        # no uniqueness constraints apply
        
        return None
    
    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "path" in fields:
            query["path"] = self.getPath()
        
        if fields is None or "host" in fields:
            query["storage__host"] = self.getHost()
            
        if fields is None or "port" in fields:
            query["storage__port"] = self.getPort()
            
        if fields is None or "user" in fields:
            query["storage__user"] = self.getUser()
        
        if fields is None or "passwd" in fields:
            query["storage__passwd"] = self.getPassword()
        
        return query
    
    def _get_query_set(self, query):
        return RemotePath.objects.filter(**query)
    
    def _create_record(self):
        storage_record = FTPStorageRecord.objects.get_or_create(
            storage_type = FTPStorageRecord.STORAGE_TYPE,
            host = self.host,
            port = self.port,
            user = self.user,
            passwd = self.passwd
        )[0]
        
        self.record = RemotePath.objects.create(
            location_type = RemotePath.LOCATION_TYPE,
            storage = storage_record,
            path = self.path
        )

RemotePathWrapperImplementation = \
RemotePathInterface.implement(RemotePathWrapper)
