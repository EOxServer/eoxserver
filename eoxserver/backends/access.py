
from os import path
import hashlib

from eoxserver.backends.cache import CacheContext
from eoxserver.backends.component import BackendComponent, env


def construct_cache_path(data_item):
    ""

    print "...... ", data_item, data_item.package, data_item.storage

    location = data_item.location[1:] if path.isabs(data_item.location) else data_item.location

    if data_item.storage:
        # create unique dirname
        storage = data_item.storage

        urlhash = hashlib.new("sha1")
        urlhash.update(storage.storage_type)
        urlhash.update(storage.url)
        digest = urlhash.hexdigest()

        return path.join(digest, location)

    elif data_item.package:
        return path.join(construct_cache_path(data_item.package), data_item.location)

    else:
        return data_item.location



def retrieve(data_item, cache_context=None):
    ""

    if not cache_context:
        cache_context = CacheContext() # TODO: read cache context config

    with cache_context:
        backend_component = BackendComponent(env)
        location = data_item.location

        cache_path = construct_cache_path(data_item)

        if data_item.package is None:
            storage = data_item.storage

            if storage is None:
                return cache_context.cache_path

            storage_component = backend_component.get_storage_component(
                storage.storage_type
            )

            if cache_path not in cache_context:
                # create a cache location
                cache_context.add_path(cache_path)

                # retrieve file and store it under 
                storage_component.retrieve(
                    storage.url, location, cache_context.relative_path(cache_path)
                )

            return cache_path

        elif data_item.package:
            # recursively retrieve packages
            package = data_item.package

            if cache_path not in cache_context:
                package_filename = retrieve(package, cache_context)
                cache_path = path.join(package_filename, location)
                
                cache_context.add_path(cache_path)

                # extract location from package
                package_component = backend_component.get_package_component(
                    package.format
                )
                print cache_context.relative_path(cache_path)
                package_component.extract(
                    cache_context.relative_path(package_filename), location, 
                    cache_context.relative_path(cache_path)
                )

            return cache_path

        else:
            # local file
            return location



def open(data_item, cache_context=None):
    "Returns a file object pointing to the given location."
    return __builtins__.open(retrieve(data_item, cache_context))
