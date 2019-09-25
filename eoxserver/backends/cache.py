#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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

import os
import os.path
import shutil
import tempfile
import errno
import logging
import threading

from eoxserver.core.config import get_eoxserver_config
from eoxserver.backends.config import CacheConfigReader


logger = logging.getLogger(__name__)


# global instance of the cache context
cache_context_storage = threading.local()


class CacheException(Exception):
    pass


def setup_cache_session(config=None):
    """ Initialize the cache context for this session. If a cache context was
        already present, an exception is raised.
    """
    if not config:
        config = CacheConfigReader(get_eoxserver_config())

    set_cache_context(
        CacheContext(config.retention_time, config.directory, True)
    )


def shutdown_cache_session():
    """ Shutdown the cache context for this session and trigger any pending
        cleanup actions required.
    """
    try:
        cache_context = get_cache_context()
        cache_context.cleanup()
    except CacheException:
        # it seems that the cache was already shut down.
        pass
    set_cache_context(None)


def set_cache_context(cache_context):
    """ Sets the cache context for this session. Raises an exception if there
        was already a cache context associated.
    """
    if cache_context is not None:
        if getattr(cache_context_storage, "cache_context", None) is not None:
            raise CacheException(
                "The cache context for this session was already initialized."
            )

    cache_context_storage.cache_context = cache_context


def get_cache_context():
    """ Get the thread local cache context for this session. Raises an exception
        if the session was not initialized.
    """
    cache_context = getattr(cache_context_storage, "cache_context", None)
    if not cache_context:
        raise CacheException(
            "The cache context for this session was not initialized."
        )
    return cache_context


class CacheContext(object):
    """ Context manager to manage cached files.
    """
    def __init__(self, retention_time=None, cache_directory=None, managed=False):
        self._cached_objects = set()

        if not cache_directory:
            cache_directory = tempfile.mkdtemp(prefix="eoxs_cache")
            self._temporary_dir = True
        else:
            self._temporary_dir = False

        self._cache_directory = cache_directory
        self._retention_time = retention_time
        self._level = 0
        self._mappings = {}

        self._managed = managed

    @property
    def cache_directory(self):
        """ Returns the configured cache directory.
        """
        return self._cache_directory

    def relative_path(self, cache_path):
        """ Returns a path relative to the cache directory.
        """
        return os.path.join(self._cache_directory, cache_path)

    def add_mapping(self, path, item):
        """ Add an external file to this context. Those files will be treated as
            if they are "within" the caches directory, but will not be clead up
            afterwards.
        """
        self._mappings[path] = item

    def add_path(self, cache_path):
        """ Add a path to this cache context. Also creates necessary
            sub-directories.
        """
        self._cached_objects.add(cache_path)
        relative_path = self.relative_path(cache_path)

        try:
            # create all necessary subdirectories
            os.makedirs(os.path.dirname(relative_path))
        except OSError as e:
            # it's only ok if the dir already existed
            if e.errno != errno.EEXIST:
                raise

        return relative_path

    def cleanup(self):
        """ Perform cache cleanup.
        """
        if self._retention_time and not self._temporary_dir:
            # no cleanup required
            return

        elif not self._temporary_dir:
            for path in self._cached_objects:
                os.remove(path)
            self._cached_objects.clear()

        else:
            shutil.rmtree(self._cache_directory)
            self._cached_objects.clear()

    def contains(self, cache_path):
        """ Check whether or not the path is contained in this cache.
        """
        if cache_path in self._cached_objects:
            return True

        return os.path.exists(self.relative_path(cache_path))

    def __contains__(self, cache_path):
        """ Alias for method `contains`.
        """
        return self.contains(cache_path)

    def __enter__(self):
        """ Context manager protocol, for recursive use. Each time the a context
            is entered, the internal level is raised by one.
        """
        self._level += 1
        return self

    def __exit__(self, etype=None, evalue=None, tb=None):
        """ Exit of context manager protocol. Performs cache cleanup if
            the level drops to zero.
        """
        self._level -= 1
        if self._level == 0 and not self._managed:
            self.cleanup()
