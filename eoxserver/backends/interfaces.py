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
This module defines interfaces for the Data Access Layer.
"""

from eoxserver.core.interfaces import *
from eoxserver.core.registry import RegisteredInterface
from eoxserver.core.records import RecordWrapperInterface

class StorageInterface(RegisteredInterface):
    """
    This is the interface for any kind of storage (local file system,
    remote repositories, databases, ...). It defines three methods:
    
    .. method:: getType
    
       This method shall return a string designating the type of the
       storage wrapped by the implementation. Current choices are:
       
       * ``local``
       * ``ftp``
       * ``rasdaman``
       
       Additional modules may add more choices in the future.
    
    .. method:: getStorageCapabilities
    
       This method shall return which of the optional methods a storage
       implements.
       
    The following methods are optional in the sense that they are not needed
    to be implemented in a meaningful way, either because the storage type
    does not support it, or because it is not needed. Even in this case, they
    need to be present and should raise :exc:`~.InternalError`.
    
    .. method:: getSize(location)
    
       This method shall return the size in bytes of the object at ``location``
       or ``None`` if it cannot be retrieved (e.g. for some FTP server
       implementations).
    
    .. method:: getLocalCopy(location, target)
    
       This method shall make a local copy of the object at
       ``location`` at the path ``target``.
       
       The method shall return the location of the local copy,
       i.e. an implementation of a descendant of
       :class:`LocationInterface`.
       
       In case the type of ``location`` cannot be handled by the
       specific storage :exc:`~.InternalError` shall be raised. In case
       the copying of resources fails :exc:`~.DataAccessError` shall
       be raised.
       
    .. method:: detect(location, search_pattern=None)
    
       This method shall return a list of object locations found at the
       given ``location`` (which may designate some kind of collection,
       like a directory) that match the given ``search_pattern``. If
       ``search_pattern`` is omitted any object location shall be
       returned.
    """
    
    REGISTRY_CONF = {
        "name": "Storage Interface",
        "intf_id": "backends.interfaces.Storage",
        "binding_method": "kvp",
        "registry_keys": (
            "backends.interfaces.storage_type",
        )
    }
    
    getType = Method(
        returns = StringArg("@return")
    )
    
    getStorageCapabilities = Method(
        returns = ListArg("@return")
    )
    
    getLocalCopy = Method(
        ObjectArg("location"),
        StringArg("target"),
        returns = ObjectArg("@return")
    )
    
    getSize = Method(
        ObjectArg("location"),
        returns = IntArg("@return", default=None)
    )
    
    
    detect = Method(
        ObjectArg("location"),
        StringArg("search_pattern", default=None),
        returns = ListArg("@return")
    )

class LocationInterface(RecordWrapperInterface):
    """
    This is the base interface for locations where to find data,
    metadata or resources in general. It is not intended to be
    instantiated directly, but rather through its descendant interfaces.
    It inherits from :class:`~.RecordWrapperInterface`.
    
    .. method:: getStorageCapabilities
    
       This method shall return the capabilities of the underlying storage
       implementation. See :meth:`StorageInterface.getStorageCapabilities`.
       
    .. method:: getSize
    
       This method shall return the size of the object at the location or
       ``None`` if it cannot be retrieved.  Note that :exc:`~.InternalError`
       will be raised if this operation is not supported by the underlying
       storage implementation. See :meth:`StorageInterface.getSize`.
       
    .. method:: getLocalCopy(target)
    
       This method shall retrieve a local copy of the object at the location
       and save it to ``target``. This parameter may be a path to a file or
       directory. The method shall return the location of the local copy, i.e.
       an implementation of :class:`LocalPathInterface`.
       
    .. method:: detect(search_pattern=None):
    
       This method shall return a list of locations of objects matching the
       given ``search_pattern`` to be found under the location, which is
       expected to be a tree-like object, most commonly a directory. If 
       ``search_pattern`` is omitted all the locations shall be returned.
    """
    
    REGISTRY_CONF = {
        "name": "Location Interface",
        "intf_id": "backends.interfaces.Location",
        "binding_method": "factory"
    }
    
    getStorageCapabilities = Method(
        returns = ListArg("@return")
    )
    
    getSize = Method(
        returns = IntArg("@return", default=None)
    )
    
    getLocalCopy = Method(
        StringArg("target"),
        returns = ObjectArg("@return")
    )
    
    detect = Method(
        StringArg("search_pattern", default=None),
        returns = ListArg("@return")
    )
    
    exists = Method(
        returns = BoolArg("@return")
    )
    
class LocalPathInterface(LocationInterface):
    """
    This is the interface for locations on the local file system. It
    inherits from :class:`LocationInterface`.
    
    .. method:: getPath
    
       This method shall return the path to the resource on the local
       file system.
    
    .. method:: open
    
       This method shall attempt to open the file at this location and return
       a :class:`file` object. It accepts one optional parameter ``mode``
       which is passed on to the builtin :func:`open` command (defaults to
       ``'r'``). The method shall raise :exc:`~.DataAccessError` if the file
       cannot be opened, or if the object at the location is not a file.
    """
    
    REGISTRY_CONF = {
        "name": "Local Path Interface",
        "intf_id": "backends.interfaces.LocalPath",
        "binding_method": "factory"
    }
    
    getPath = Method(
        returns = StringArg("@return")
    )
    
    open = Method(
        StringArg("mode", default='r'),
        returns = ObjectArg("@return", arg_class=file)
    )
    
class RemotePathInterface(LocationInterface):
    """
    This is the interface for data and metadata files stored on a
    remote server. It inherits from :class:`LocationInterface`.
    
    .. method:: getStorageType
    
       This method shall return the type of the remote storage, e.g.
       ``"ftp"``.
       
    .. method:: getHost
    
       This method shall return the host name of the remote storage.
       
    .. method:: getPort
    
       This method shall return the port number of the remote storage,
       or ``None`` if it is not defined.
       
    .. method:: getUser
    
       This method shall return the user name to be used for access to
       the remote storage, or ``None`` if it is not defined.
       
    .. method:: getPasswd
    
       This method shall return the password to be used for access to
       the remote storage, or ``None`` if it is not defined.
       
    .. method:: getPath
    
       This method shall return the path to the resource on the remote
       storage.
    """
    
    REGISTRY_CONF = {
        "name": "Remote Path Interface",
        "intf_id": "backends.interfaces.RemotePath",
        "binding_method": "factory"
    }
    
    getStorageType = Method(
        returns = StringArg("@return")
    )
    
    getHost = Method(
        returns = StringArg("@return")
    )
    
    getPort = Method(
        returns = IntArg("@return", default=None)
    )
    
    getUser = Method(
        returns = StringArg("@return", default=None)
    )
    
    getPassword = Method(
        returns = StringArg("@return", default=None)
    )

    getPath = Method(
        returns = StringArg("@return")
    )

class DatabaseLocationInterface(LocationInterface):
    """
    This is the interface for raster data stored in a database. It
    inherits from :class:`LocationInterface` and adds some methods.
    
    .. method:: getHost
    
       This method shall return the hostname of the database manager.
    
    .. method:: getPort
    
       This method shall return the number of the port where the
       database manager listens for connections, or ``None`` if the
       port is undefined.
    
    .. method:: getDBName
    
       This method shall return the database name, or ``None`` if it
       is undefined.
       
    .. method:: getUser
    
       This method shall return the user name to be used for opening
       database connections, or ``None`` if it is undefined.
       
    .. method:: getPassword
    
       This method shall return the password to be used for opening
       database connections, or ``None`` if it is undefined.
       
    """
    
    REGISTRY_CONF = {
        "name": "Database Package Interface",
        "intf_id": "backends.interfaces.DatabaseLocation",
        "binding_method": "factory"
    }
    
    getHost = Method(
        returns = StringArg("@return")
    )
    
    getPort = Method(
        returns = IntArg("@return")
    )
    
    getDBName = Method(
        returns = StringArg("@return")
    )
    
    getUser = Method(
        returns = StringArg("@return")
    )
    
    getPassword = Method(
        returns = StringArg("@return")
    )
