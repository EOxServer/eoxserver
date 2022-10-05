# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
#
# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

from django.db import models
from django.core.exceptions import ValidationError

from eoxserver.backends.storages import get_handler_class_by_name


optional = dict(null=True, blank=True)
mandatory = dict(null=False, blank=False)


# ==============================================================================
# Models
# ==============================================================================


class StorageAuth(models.Model):
    """ Model to symbolize authorization for storages.
    """
    url = models.CharField(max_length=1024, **mandatory)
    storage_auth_type = models.CharField(max_length=32, **mandatory)
    name = models.CharField(max_length=1024, null=True, blank=True, unique=True)
    auth_parameters = models.TextField()

    def __str__(self):
        return "%s: %s" % (self.storage_auth_type, self.url)

    def clean(self):
        validate_storage_auth(self)


class Storage(models.Model):
    """ Model to symbolize storages that provide file or other types of access
        to data items.
    """
    url = models.CharField(max_length=1024, **mandatory)
    storage_type = models.CharField(max_length=32, **mandatory)
    name = models.CharField(max_length=1024, null=True, blank=True, unique=True)
    storage_auth = models.ForeignKey(StorageAuth, on_delete=models.CASCADE, **optional)

    parent = models.ForeignKey("self", on_delete=models.CASCADE, **optional)

    def __str__(self):
        return "%s: %s" % (self.storage_type, self.url)

    def clean(self):
        validate_storage(self)


class DataItem(models.Model):
    """ Abstract model for locateable data items contributing to a dataset.
    """

    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, **optional)
    location = models.CharField(max_length=1024, **mandatory)
    format = models.CharField(max_length=64, **optional)

    class Meta:
        abstract = True

    def __str__(self):
        if self.format:
            return "%s (%s)" % (self.location, self.format)
        return self.location


# ==============================================================================
# Validators
# ==============================================================================


def validate_storage(storage):
    parent = storage.parent

    handler = get_handler_class_by_name(storage.storage_type)
    if not handler:
        raise ValidationError(
            'Storage type %r is not supported.' % storage.storage_type
        )

    if parent:
        parent_handler = get_handler_class_by_name(parent.storage_type)
        if not handler.allows_parent_storage:
            raise ValidationError(
                'Storage type %r does not allow parent storages'
                % storage.storage_type
            )
        elif not parent_handler.allows_child_storages:
            raise ValidationError(
                'Parent storage type %r does not allow child storages'
                % parent.storage_type
            )

    while parent:
        if parent == storage:
            raise ValidationError('Circular reference detected')
        parent = parent.parent


def validate_storage_auth(storage_auth):
    pass
