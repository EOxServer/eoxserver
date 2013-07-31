
from os import makedirs, path
import hashlib
import logging

from eoxserver.backends.cache import CacheContext
from eoxserver.backends.component import BackendComponent, env


logger = logging.getLogger(__name__)

def generate_hash(location, format, hash_impl="sha1"):
    h = hashlib.new(hash_impl)
    if format is not None:
        h.update(format)
    h.update(location)
    return h.hexdigest()


def retrieve(data_item, cache=None):
    """ 
    """

    backend = BackendComponent(env)

    if cache is None:
        cache = CacheContext()

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

    component = backend.get_storage_component(
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
