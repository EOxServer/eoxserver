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
This module provides an implementation of a cache, intended primarily
for caching content from remote backends.

.. warning:: The current implementation of the :class:`Cache` class is not
   functional and shall not be used. A future implementation must be able to
   work properly in a multi-process multi-threaded environment (i.e. provide
   some kind of data access synchronization). This requires inter-process
   communication to be implemented and is thus too much of an effort for the
   time being.
"""


import os.path
from datetime import datetime
from time import sleep
from threading import Thread, RLock

from eoxserver.core.system import System
from eoxserver.core.readers import ConfigReaderInterface
from eoxserver.backends.models import (
    CacheFile, LocalPath
)
from eoxserver.backends.exceptions import DataAccessError
from eoxserver.core.exceptions import ConfigError

class Cache(object):
    # IMPORTANT: DO NOT USE THIS IMPLEMENTATION!
    # It is essentially crap, useless and potentially harmful
    
    _size = None
    _size_lock = RLock()
    
    _free_size = None
    _free_thread = None
    _free_lock = RLock()
    
    @classmethod
    def addFile(cls, cache_file):
        """
        This method registers that a file is added to the cache and
        updates the cache size accordingly. 
        """
        file_size = cache_file.getSize()
        
        if file_size is not None:
            cls._size_lock.acquire()
            cls._size += file_size
            cls._size_lock.release()
        
        if not cls.check(0):
            self.free()
        
    @classmethod
    def removeFile(cls, cache_file):
        file_size = cache_file.getSize()
        
        if file_size is not None:
            cls._size_lock.acquire()
            cls._size -= file_size
            cls._size_lock.release()
    
    @classmethod
    def synchronizeSize(cls):
        cls._size_lock.acquire()
        cls._size = CacheFile.objects.aggregate(cache_size=Sum('size'))["cache_size"]
        cls._size_lock.release()
                
    @classmethod
    def check(cls, file_size):
        cls._size_lock.acquire()
        preview_size = cls._size + file_size
        cls._size_lock.release()
        
        return preview_size < CacheConfigReader.getMaxSize()
        
    @classmethod
    def free(cls, free_size=None, defensive=False):
        """
        This method frees cache space. It takes two optional arguments:
        
        * ``free_size`` denotes the free cache space that shall be
          available (at least) after the operation
        * ``defensive``: a boolean which determines if the operation
          shall be defensive (i.e. only free cache space until the
          cache can accomodate for a file of ``free_size`` bytes) or
          offensive (i.e. free cache space until there are no more
          cache files left to discard). It defaults to ``False``, i.e.
          offensive cache freeing.
          
        If ``free_size`` is omitted and ``defensive`` is set to
        ``False`` (the default) every cache file that may be discarded
        will be purged. If ``free_size`` is omitted and ``defensive``
        is set to ``True`` the method will return immediately.
        
        Note that when freeing in "offensive" mode a separate thread
        will be created that purges files from the cache. Execution of
        the calling thread is halted until the free cache space is
        big enough to accomodate for ``free_size`` bytes. The cache
        freeing thread will then continue in the background, while the
        calling thread can resume its work.
        """
        
        if not free_size and defensive:
            pass
        else:
            cls._free_lock.acquire()
            
            try:
                if cls._free_thread and cls._free_thread.isAlive():
                    if not cls._free_size == "max":
                        if free_size is None:
                            cls._free_size = "max"
                        else:
                            cls._free_size += free_size
                else:
                    if free_size is None:
                        cls._free_size = "max"
                    else:
                        cls._free_size = free_size
                
                    cls._free_thread = Thread(
                        target=cls._free_background,
                        kwargs={"defensive": defensive}
                    )
                    
                    cls._free_thread.start()
                    
                cls._free_lock.release()
                
            except:
                cls._free_lock.release()
                
                raise
            
            while not cls._free_size_reached():
                sleep(0.001)
                
    @classmethod
    def _free_background(cls, defensive=False):
        # this method is run in a separate thread of execution and
        # loops over all removable cache files. It will stop when there
        # are no more files left to discard
        
        before = datetime.now() - timedelta(
            hours=CacheConfigReader().getRetentionTime()
        )
        
        cache_file_records = list(CacheFile.objects.filter(
            access_timestamp__lt = before
        ).order_by('access_timestamp'))
        
        while len(cache_file_records) > 0 and ((defensive and not cls._free_size_reached()) or not defensive):
            cache_file = CacheFile(cache_file_records.pop())
            
            cache_file.purge()
        
        cls._free_lock.acquire()
        cls._free_size = None
        cls._free_lock.release()
        
    @classmethod
    def _free_size_reached(cls):
        cls._free_lock.acquire()
        if cls._free_size == "max":
            ret_val = False
        else:
            ret_val = cls.check(cls._free_size)
        cls._free_lock.release()
        
        return ret_val
    
class CacheFileWrapper(object):
    """
    This class wraps :class:`~.CacheFile` records and adds the logic to handle
    them to the database model.
    """
    
    def __init__(self, model):
        self.__model = model
    
    @classmethod
    def create(cls, filename):
        """
        This class method creates a :class:`CacheFileWrapper` instance for the
        given file name. It makes a database record for the cache file, but
        does NOT copy it from its location to the cache. You have to call
        :meth:`copy` on the instance for that.
        """
        #=======================================================================
        # provisional solution
        
        cache_dir = System.getRegistry().bind("backends.cache.CacheConfigReader").getCacheDir()
        
        if cache_dir is None:
            raise ConfigError("Cache directory is not configured.")
        
        target_dir = os.path.join(
            cache_dir, "cache_%s" % datetime.now().strftime("%Y%m%d")
        )
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        #-----------------------------------------------------------------------
        # use this when viable cache implementation is finished
        #target_dir = Cache.getTargetDir()
        
        #=======================================================================
        
        dest_path = os.path.join(target_dir, filename)
        
        location_record = LocalPath.objects.create(
            location_type = LocalPath.LOCATION_TYPE,
            path = dest_path
        )
        
        model = CacheFile.objects.create(
            location = location_record,
            size = None,
            access_timestamp = datetime.now()
        )
        
        cache_file = cls(model)
        
        return cache_file
    
    def getModel(self):
        """
        Returns the model record wrapped by the implementation.
        """
        
        return self.__model

    def getLocation(self):
        """
        Returns the a :class:`~.LocalPathWrapper` object pointing to the
        location of the cache file.
        """
        return System.getRegistry().getFromFactory(
            "backends.factories.LocationFactory",
            {
                "record": self.__model.location
            }
        )
    
    def getSize(self):
        """
        Returns the size of the cache file in bytes. Note that the return value
        is ``None`` if the :class:`CacheFileWrapper` instance has been
        initialized already, but :meth:`copy` has not been called yet.
        """
        return self.__model.size
        
    def copy(self, location):
        """
        Copy the file from its current ``location`` to the cache. This may
        raise :exc:`~.InternalError` if the storage implementation for the 
        location does not support the :meth:`~.StorageInterface.getSize` and/or
        :meth:`~.StorageInterface.getLocalCopy` methods or
        :exc:`~.DataAccessError` if there was a fault when retrieving the 
        original file.
        """
        
        # this may raise InternalError
        size = location.getSize()
    
        # make cache space for the file; this is disabled at the
        # moment due to insufficiencies in the cache implementation
        #if size is not None:
        #    if not Cache.check(size):
        #        Cache.free(size)
        
        # this may raise InternalError or DataAccessError; just pass
        # them on
        location.getLocalCopy(self.__model.location.path)
        
        self.__model.access_timestamp = datetime.now()
        
        self.__model.size = \
            os.path.getsize(self.__model.location.path)
    
        self.__model.save()
        
        # register the file at the cache; this is disabled at the
        # moment due to insufficiencies in the cache implementation
        #Cache.addFile(self)
    
    def access(self):
        """
        This method shall be called every time a cache file is accessed. It
        updates the access timestamp of the model that should be used by cache
        implementations to determine which cache files can be removed.
        """
        self.__model.access_timestamp = datetime.now()
        
        self.__model.save()
    
    def purge(self):
        """
        Delete the cache file from the local file system and delete the
        associate :class:`~.CacheFile` database record. Raises
        :exc:`~.DataAccessError` if the file could not be deleted.
        """
        path = self.__model.location.path
        
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception, e:
                raise DataAccessError(
                    "Could not remove file '%s' from cache. Error message: '%s'" % (
                        path, str(e)
                    )
                )
        
        # remove the file from the cache; this is disabled at the
        # moment due to insufficiencies in the cache implementation
        #Cache.removeFile(self)
        
        self.__model.delete()

#class CacheStartupHandler(object):
#    def startup(self):
#        Cache.synchronizeSize()
#    
#    def reset(self):
#        Cache.synchronizeSize()

class CacheConfigReader(object):
    """
    This is the configuration reader for the cache configuration. It should be
    used by cache implementations.
    
    The cache can be configured by config file entries in the section
    ``backends.cache``. There are three of them:

    * ``cache_dir``: if you want to use the cache you have to define this
      setting; it tells under which directory tree the cache files shall be
      stored. Note that if you change this setting, the cached files at the
      old location will not be forgotten.
    * ``max_size``: the maximum size of the cache in bytes; be sure to set
      this to a value that exceeds maximum traffic within the given
      retention time, otherwise you will get :exc:`~.CacheOverflow` errors
      at runtime
    * ``retention_time``: the minimum time cache files will be kept
      expressed in hours. At your own risk you can set it to 0, but strange
      things may occur then due to one thread deleting the data another one
      needs. A minimum of 1 hour is recommended, the default is 168
      (a week).
    """
    REGISTRY_CONF = {
        "name": "Cache Config Reader",
        "impl_id": "backends.cache.CacheConfigReader"
    }
    
    def validate(self, config):
        """
        Returns ``True``.
        """
        return True
    
    def getCacheDir(self):
        """
        Returns the ``cache_dir`` config file setting.
        """
        return System.getConfig().getConfigValue("backends.cache", "cache_dir")
        
    def getMaxSize(self):
        """
        Returns the ``max_size`` config file setting.
        """
        return System.getConfig().getConfigValue("backends.cache", "max_size")
        
    def getRetentionTime(self):
        """
        Returns the ``retention_time`` config file setting.
        """
        return System.getConfig().getConfigValue("backends.cache", "retention_time")

CacheConfigReaderImplementation = \
ConfigReaderInterface.implement(CacheConfigReader)
