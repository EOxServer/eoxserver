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

from eoxserver.core.system import System
from eoxserver.core.records import RecordWrapper
from eoxserver.core.exceptions import InternalError

class LocationWrapper(RecordWrapper):
    """
    This is the base class for location wrappers. It inherits from 
    :class:`~.RecordWrapper`. It should not be instantiated
    directly, but one of its subclasses should be used.
    """
    
    def __init__(self):
        super(LocationWrapper, self).__init__()
        
        self.storage = self._bind_to_storage()
        
    def _bind_to_storage(self):
        # While a working implementation this method should be overridden
        # by subclasses for efficiency's sake
        
        return System.getRegistry().findAndBind(
            intf_id = "backends.interfaces.StorageInterface",
            params =  {
                "backends.interfaces.storage_type": self.getType()
            }
        )
        
    def getStorageCapabilities(self):
        """
        Returns the capabilities of the corresponding storage. See
        :meth:`.StorageInterface.getStorageCapabilities` for details. 
        """
        return self.storage.getStorageCapabilities()
        
    def getSize(self):
        """
        Returns the size (in bytes) of the object at the location. Raises
        :exc:`~.InternalError` if the corresponding storage is not capable of
        retrieving the size. See :meth:`.StorageInterface.getSize` for details.
        """
        return self.storage.getSize(self)
        
    def getLocalCopy(self, target):
        """
        Copies the resource to the path ``target`` on the local file system.
        Raises :exc:`~.InternalError` if the corresponding storage is not
        capable of copying data. See :meth:`.StorageInterface.getLocalCopy` for
        details.
        """
        return self.storage.getLocalCopy(self, target)
        
    def detect(self, search_pattern=None):
        """
        Searches the location for objects that match ``search_pattern``. If the
        parameter is omitted, all found objects are returned. It returns a list
        of locations of the same type that point to these objects. Raises
        :exc:`~.InternalError` if the corresponding storage is not capable of
        auto-detection. See :meth:`.StorageInterface.detect` for details.
        """
        return self.storage.detect(self, search_pattern)
    
    def exists(self):
        return self.storage.exists(self)
    
