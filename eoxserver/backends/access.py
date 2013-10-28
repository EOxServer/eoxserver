#-------------------------------------------------------------------------------
# $Id$
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


from os import makedirs, path
import hashlib
import logging

from eoxserver.backends.cache import get_cache_context
from eoxserver.backends.component import BackendComponent, env


logger = logging.getLogger(__name__)

def generate_hash(location, format, hash_impl="sha1"):
    h = hashlib.new(hash_impl)
    if format is not None:
        h.update(format)
    h.update(location)
    return h.hexdigest()


def connect(data_item, cache=None):
    """ return a connection string, either for a local (cached) data or something 
        residing on a server of some kind
    """

    backend = BackendComponent(env)

    storage = data_item.storage

    if storage:
        component = backend.get_connected_storage_component(storage.storage_type)

    if not storage or not component:
        return retrieve(data_item, cache)

    return component.connect(storage.url, data_item.location)



def retrieve(data_item, cache=None):
    """ 
    """

    backend = BackendComponent(env)

    if cache is None:
        cache = get_cache_context()

    # compute a cache path where the file *would* be cached
    with cache:
        item_id = generate_hash(data_item.location, data_item.format)
        path = cache.relative_path(item_id)

        logger.debug("Retrieving %s (ID: %s)" % (data_item, item_id))

        if item_id in cache:
            logger.debug("Item %s is already in the cache." % item_id)
            return path
        
        if data_item.package is None and data_item.storage:
            return _retrieve_from_storage(
                backend, data_item, data_item.storage, item_id, path, cache
            )

        elif data_item.package:
            return _extract_from_package(
                backend, data_item, data_item.package, item_id, path, cache
            )

        else:
            return data_item.location



def _retrieve_from_storage(backend, data_item, storage, item_id, path, cache):
    """ Helper function to retrieve a file from a storage.
    """
    logger.debug("Accessing storage %s." % storage)

    component = backend.get_file_storage_component(
        storage.storage_type
    )

    actual_path = component.retrieve(
        storage.url, data_item.location, path
    )

    if actual_path and actual_path != path:
        cache.add_mapping(actual_path, item_id)

    return actual_path or path


def _extract_from_package(backend, data_item, package, item_id, path, cache):
    """ Helper function to extract a file from a package.
    """
    logger.debug("Accessing package %s." % package)

    package_location = retrieve(package, cache)

    component = backend.get_package_component(
        package.format
    )

    logger.debug(
        "Extracting from %s: %s and saving it at %s" 
        % (package_location, data_item.location, path)
    )

    actual_path = component.extract(
        package_location, data_item.location, path
    )

    if actual_path and actual_path != path:
        cache.add_mapping(actual_path, item_id)

    return actual_path or path


def open(data_item, cache_context=None):
    """ Returns a file object pointing to the given location.
    """
    return __builtins__.open(retrieve(data_item, cache_context))
