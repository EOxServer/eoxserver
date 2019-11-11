# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2017 EOX IT Services GmbH
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

from django.conf import settings
from django.utils.module_loading import import_string

from eoxserver.resources.coverages.metadata.config import (
    DEFAULT_EOXS_PRODUCT_METADATA_FORMAT_READERS
)

PRODUCT_METADATA_FORMAT_READERS = None


def _setup_readers():
    global PRODUCT_METADATA_FORMAT_READERS

    specifiers = getattr(
        settings, 'EOXS_PRODUCT_METADATA_FORMAT_READERS',
        DEFAULT_EOXS_PRODUCT_METADATA_FORMAT_READERS
    )

    PRODUCT_METADATA_FORMAT_READERS = [
        import_string(specifier)
        for specifier in specifiers
    ]


def get_readers():
    if PRODUCT_METADATA_FORMAT_READERS is None:
        _setup_readers()
    return PRODUCT_METADATA_FORMAT_READERS


# def get_reader_by_test(path, obj):
#     if PRODUCT_METADATA_FORMAT_READERS is None:
#         _setup_readers()

#     for reader in PRODUCT_METADATA_FORMAT_READERS:
#         if hasattr(reader, 'test_path') and reader.test_path(path):
#             return reader
#         elif hasattr(reader, 'test') and reader.test(obj):
#             return reader
