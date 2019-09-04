# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2019 EOX IT Services GmbH
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

from eoxserver.backends import models
from eoxserver.backends.storages import (
    get_handler_by_test, get_handler_class_by_name
)


def resolve_storage(storage_paths, save=True):
    parent = None
    for locator in storage_paths:
        # try to get a storage by name, if it exists:
        try:
            parent = models.Storage.objects.get(
                name=locator, parent=parent
            )
        except models.Storage.DoesNotExist:
            handler = get_handler_by_test(locator)
            if handler:
                parent = models.Storage(
                    name=None,
                    url=locator, storage_type=handler.name,
                    parent=parent,
                )
            else:
                name, _, url = locator.partition(':')
                handler_cls = get_handler_class_by_name(name)
                if handler_cls:
                    parent = models.Storage(
                        name=None,
                        url=url, storage_type=name,
                        parent=parent,
                    )
                else:
                    raise Exception(
                        'No storage handler found for locator %r' % locator
                    )
            if save:
                parent.full_clean()
                parent.save()

    return parent


def resolve_storage_and_path(storage_paths, save=True):
    last = storage_paths[-1]
    name, _, _ = last.partition(':')
    handler_cls = get_handler_class_by_name(name)
    if handler_cls:
        return resolve_storage(storage_paths, save), None
    else:
        return resolve_storage(storage_paths[:-1], save), last
