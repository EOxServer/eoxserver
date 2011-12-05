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
This module implements the rasdaman database backend for EOxServer.
"""

from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.backends.models import RasdamanStorage as RasdamanStorageRecord
from eoxserver.backends.models import RasdamanLocation
from eoxserver.backends.interfaces import (
    StorageInterface, DatabaseLocationInterface
)
from eoxserver.backends.base import LocationWrapper
from eoxserver.backends.exceptions import DataAccessError

class RasdamanStorage(object):
    """
    This class implements the rasdaman storage.
    """
    REGISTRY_CONF = {
        "name": "rasdaman Storage",
        "impl_id": "backends.rasdaman.RasdamanStorage",
        "registry_values": {
            "backends.interfaces.storage_type": "rasdaman"
        }
    }
    
    def getType(self):
        """
        Returns ``"rasdaman"``
        """
        return "rasdaman"
        
    def getStorageCapabilities(self):
        """
        Returns the storage capabilities, i.e. the names of the optional methods
        implemented by the storage. Currently none are supported.
        """
        return tuple()
        
    def getSize(self, location):
        """
        Not supported; raises :exc:`~.InternalError`.
        """
        raise InternalError(
            "The rasdaman storage does not support array size retrieval."
        )
        
    def getLocalCopy(self, location, target):
        """
        Not supported; raises :exc:`~.InternalError`.
        """
        raise InternalError(
            "The rasdaman storage does not support copies to the local file system."
        )
    
    def detect(self, location, search_pattern=None):
        """
        Not supported; raises :exc:`~.InternalError`.
        """
        raise InternalError(
            "The rasdaman storage does not support detection of datasets."
        )
        
    def exists(self, location):
        raise InternalError(
            "The rasdaman storage does not support detection of datasets."
        )
        
RasdamanStorageImplementation = \
StorageInterface.implement(RasdamanStorage)
        
class RasdamanArrayWrapper(LocationWrapper):
    """
    This is a wrapper for rasdaman database locations. It inherits from
    :class:`~.LocationWrapper`.
    
    .. method:: setAttrs(**kwargs)
    
        The following attribute keyword arguments are accepted:
        
        * ``host`` (required): the host name of the server rasdaman runs on
        * ``port`` (optional): the port number where to reach rasdaman
        * ``user`` (optional): the user name to be used for login
        * ``db_name`` (optional): the database name
        * ``passwd`` (optional): the password to be used for login
        * ``collection`` (required): the name of the collection in the database
        * ``oid`` (optional): the ``oid`` of the array within the collection
    """
    
    REGISTRY_CONF = {
        "name": "Rasdaman Array Wrapper",
        "impl_id": "backends.rasdaman.RasdamanArrayWrapper",
        "factory_ids": (
            "backends.factories.LocationFactory",
        )
    }
    
    
    def __init__(self):
        super(RasdamanArrayWrapper, self).__init__()
        
        self.host = None
        self.port = None
        self.db_name = None
        self.user = None
        self.passwd = None
        self.collection = None
        self.oid = None
        
    def getType(self):
        """
        Returns ``"rasdaman"``.
        """
        
        return "rasdaman"
        
    def getHost(self):
        """
        Returns the host name of the server rasdaman runs on.
        """
        if self.record:
            return self.record.storage.host
        else:
            return self.host
    
    def getPort(self):
        """
        Returns the port number where to reach rasdaman, or ``None`` if it
        has not been defined.
        """
        if self.record:
            return self.record.storage.port
        else:
            return self.port
            
    def getDBName(self):
        """
        Returns the rasdaman database name, or ``None`` if it has not been
        defined.
        """
        if self.record:
            return self.record.storage.db_name
        else:
            return self.db_name
            
    def getUser(self):
        """
        Returns the user name used to login to the database, or ``None`` if it
        has not been defined.
        """
        if self.record:
            return self.record.storage.user
        else:
            return self.user
    
    def getPassword(self):
        """
        Returns the password used to login to the database, or ``None`` if it
        has not been defined.
        """
        if self.record:
            return self.record.storage.passwd
        else:
            return self.passwd
    
    def getCollection(self):
        """
        Returns the collection name.
        """
        if self.record:
            return self.record.collection
        else:
            return self.collection
    
    def getOID(self):
        """
        Returns the oid of the array within the collection.
        """
        if self.record:
            return self.record.oid
        else:
            return self.oid
            
    def _bind_to_storage(self):
        return System.getRegistry().bind("backends.rasdaman.RasdamanStorage")
        
    def _validate_record(self, record):
        if record.location_type != "rasdaman":
            raise InternalError(
                "Cannot assign '%s' type location record to rasdaman location." %\
                record.location_type
            )
    
    def _set_record(self, record):
        if isinstance(record, RasdamanLocation):
            self.record = record
        else:
            self.record = record.rasdamanlocation
    
    def _validate_attrs(self, **kwargs):
        if "host" not in kwargs or "collection" not in kwargs:
            raise InternalError(
                "'host' and 'collection' are needed to initialize a rasdaman location instance."
            )
            
    def _set_attrs(self, **kwargs):
        self.host = kwargs["host"]
        self.collection = kwargs["collection"]
        self.oid = kwargs.get("oid")
            
        self.port = kwargs.get("port")
        self.db_name = kwargs.get("db_name")
        self.user = kwargs.get("user")
        self.passwd = kwargs.get("passwd")
    
    def _fetch_unique_record(self):
        # no uniqueness constraints apply
        
        return None
    
    def _get_query(self, fields=None):
        query = {}
        
        if fields is None or "collection" in fields:
            query["collection"] = self.getCollection()
        
        if fields is None or "oid" in fields:
            query["oid"] = self.getOID()
        
        if fields is None or "host" in fields:
            query["storage__host"] = self.getHost()
            
        if fields is None or "port" in fields:
            query["storage__port"] = self.getPort()
            
        if fields is None or "db_name" in fields:
            query["storage__db_name"] = self.getDBName()
        
        if fields is None or "user" in fields:
            query["storage__user"] = self.getUser()
            
        if fields is None or "passwd" in fields:
            query["storage__passwd"] = self.getPassword()
        
        return query
    
    def _get_query_set(self, query):
        return RasdamanLocation.objects.filter(**query)
    
    def _create_record(self):
        storage_record = RasdamanStorageRecord.objects.get_or_create(
            storage_type = RasdamanStorageRecord.STORAGE_TYPE,
            host = self.host,
            port = self.port,
            db_name = self.db_name,
            user = self.user,
            passwd = self.passwd
        )[0]
        
        self.record = RasdamanLocation.objects.create(
            location_type = RasdamanLocation.LOCATION_TYPE,
            storage = storage_record,
            collection = self.collection,
            oid = self.oid
        )
    
RasdamanArrayWrapperImplementation = \
DatabaseLocationInterface.implement(RasdamanArrayWrapper)
