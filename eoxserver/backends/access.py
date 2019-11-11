# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

import os
import hashlib
import logging
from fnmatch import fnmatch

from eoxserver.core.util.iteratortools import pairwise_iterative
from eoxserver.contrib import vsi, gdal
from eoxserver.backends.cache import get_cache_context
from eoxserver.backends.storages import get_handler_class_for_model
from eoxserver.backends import storage_auths


logger = logging.getLogger(__name__)


class AccessError(Exception):
    pass


def _generate_hash(location, format, hash_impl="sha1"):
    h = hashlib.new(hash_impl)
    if format is not None:
        h.update(format)
    h.update(location)
    return h.hexdigest()


def _linearize_storages(data_item):
    """ Retrieve a list of all storages.
    """
    chain = []
    storage = data_item.storage
    while storage:
        handler_cls = get_handler_class_for_model(storage)
        if not handler_cls:
            raise AccessError(
                'Unsupported storage type %r' % storage.storage_type
            )

        chain.append((storage, handler_cls))
        storage = storage.parent
    return reversed(chain)


def retrieve(data_item, cache=None):
    """ Retrieves the :class:`eoxserver.backends.models.DataItem` and makes the
        file locally available if necessary.
        When the data item is not associated with a storage, then the data items
        location will be returned. Otherwise, the storage  handlers ``retrieve``
        method will be called to make the data item locally available.

        :param data_item: data item to retrieve
        :type data_item: :class:`eoxserver.backends.models.DataItem`
        :param cache: the optional cache context
        :type cache: eoxserver.backends.cache.CacheContext
        :returns: the path to the localized file
        :rtype: str
    """
    cache = cache or get_cache_context()

    # use shortcut here, when no storage is provided
    if not data_item.storage:
        return data_item.location

    storage_handlers = _linearize_storages(data_item)
    with cache:
        handler = None
        path = None
        for current, child in pairwise_iterative(storage_handlers):
            storage, handler_cls = current
            child_storage, _ = child

            item_id = _generate_hash(data_item.location, data_item.format)
            tmp_path = cache.relative_path(item_id)
            if not cache.contains(item_id):
                # actually retrieve the item when not in the cache
                handler = handler_cls(path or storage.url)
                use_cache, path = handler.retrieve(
                    path or child_storage.url, tmp_path
                )
                if not use_cache:
                    cache.add_mapping(path)
            else:
                path = tmp_path

        if storage_handlers:
            storage, handler_cls = storage_handlers[-1]
            handler = handler_cls(path)
            return handler.retrieve(data_item.location)[1]


def open(data_item, cache=None):
    """ Returns a file object pointing to the given location. This function
    works like the builtin function :func:`open() <__builtins__.open>` but on
    a :class:`DataItem <eoxserver.backends.models.DataItem>` and performs a
    :func:`retrieve` first.

    :param data_item: the :class:`DataItem <eoxserver.backends.models.DataItem>`
                      to open
    :param cache: an instance of :class:`CacheContext
                  <eoxserver.backends.cache.CacheContext>` or ``None``
                  if the caching shall be handled internally
    """

    return __builtins__.open(retrieve(data_item, cache))


def get_vsi_path(data_item):
    """ Get the VSI path to the given :class:`eoxserver.backends.models.DataItem`

        :param data_item: the data item to get the path to
        :type data_item: :class:`eoxserver.backends.models.DataItem`
        :returns: the VSI file path which is can be used with GDAL-related APIs
        :rtype: str
    """
    location = data_item.location
    storage = data_item.storage

    return get_vsi_storage_path(storage, location)


def get_vsi_storage_path(storage, location=None):
    while storage:
        handler_cls = get_handler_class_for_model(storage)
        if handler_cls:
            handler = handler_cls(storage.url)
            location = handler.get_vsi_path(location or '')
        else:
            raise AccessError(
                'Unsupported storage type %r' % storage.storage_type
            )
        storage = storage.parent

    return location



def get_vsi_env(storage):
    """
    """
    env = {}
    while storage:
        handler_cls = get_handler_class_for_model(storage)
        if handler_cls:
            handler = handler_cls(storage.url)
            env.update(handler.get_vsi_env())
        else:
            raise AccessError(
                'Unsupported storage type %r' % storage.storage_type
            )

        if storage.storage_auth:
            handler = storage_auths.get_handler_for_model(
                storage.storage_auth
            )
            if handler:
                env.update(handler.get_vsi_env())
            else:
                raise AccessError(
                    'Unsupported storage auth type %r'
                    % storage.storage_auth.storage_auth_type
                )

        storage = storage.parent

    return env


def vsi_open(data_item):
    """ Opens a :class:`eoxserver.backends.models.DataItem` as a
        :class:`eoxserver.contrib.vsi.VSIFile`. Uses :func:`get_vsi_path`
        internally to get the path.

        :param data_item: the data item to open as a VSI file
        :type data_item: :class:`eoxserver.backends.models.DataItem`
        :rtype: :class:`eoxserver.contrib.vsi.VSIFile`
    """
    with gdal.config_env(get_vsi_env(data_item.storage)):
        return vsi.open(get_vsi_path(data_item))


def gdal_open(data_item, shared=True):
    """ Opens a :class:`eoxserver.backends.models.DataItem` as a
        :class:`eoxserver.contrib.gdal.Dataset`. Uses :func:`get_vsi_path`
        internally to get the path.

        :param data_item: the data item to open as a dataset.
        :type data_item: :class:`eoxserver.backends.models.DataItem`
        :rtype: :class:`eoxserver.contrib.gdal.Dataset`
    """
    return gdal.open_with_env(
        get_vsi_path(data_item),
        get_vsi_env(data_item.storage),
        shared
    )


def vsi_list_storage(storage, location=None, pattern=None):
    """
    """
    with gdal.config_env(get_vsi_env(storage)):
        path = get_vsi_storage_path(storage, location)
        files = gdal.ReadDir(path)

        if files is None:
            raise Exception('No such path "%s"' % path)

        if pattern:
            files = [
                filename
                for filename in files
                if fnmatch(filename, pattern)
            ]

        return files
