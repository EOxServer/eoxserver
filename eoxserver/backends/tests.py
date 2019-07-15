#-------------------------------------------------------------------------------
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

import os.path
from glob import glob
import logging
from unittest import skip

from django.test import TestCase

from eoxserver.backends import testbase
from eoxserver.backends import models
from eoxserver.backends.cache import CacheContext
from eoxserver.backends.access import retrieve
from eoxserver.backends.component import BackendComponent, env
from eoxserver.backends.testbase import withFTPServer


logger = logging.getLogger(__name__)


""" "New" data models
"""


def create(Model, *args, **kwargs):
    model = Model(*args, **kwargs)
    model.full_clean()
    model.save()
    return model


# class RetrieveTestCase(TestCase):
#     def setUp(self):
#         pass

#     def tearDown(self):
#         pass

#     def test_retrieve_http(self):
#         import storages, packages

#         storage = create(models.Storage,
#             url="http://eoxserver.org/export/2523/downloads",
#             storage_type="HTTP"
#         )
#         dataset = create(models.DataItem,
#             location="EOxServer_documentation-0.3.0.pdf",
#             storage=storage,
#             semantic="pdffile"
#         )

#         with CacheContext() as c:
#             cache_path = retrieve(dataset, c)
#             self.assertTrue(os.path.exists(cache_path))

#         self.assertFalse(os.path.exists(cache_path))

#     @skip("not yet implemented")
#     @withFTPServer()
#     def test_retrieve_ftp_zip(self):
#         import storages
#         import packages

#         storage = create(models.Storage,
#             url="ftp://anonymous:@localhost:2121/",
#             storage_type="FTP"
#         )

#         package = create(models.Package,
#             location="package.zip",
#             format="ZIP",
#             storage=storage
#         )

#         dataset = create(models.DataItem,
#             location="file.txt",
#             package=package,
#             semantic="textfile"
#         )

#         dataset2 = create(models.DataItem,
#             location="file2.txt",
#             package=package,
#             semantic="textfile"
#         )

#         with CacheContext() as c:
#             cache_path = retrieve(dataset, c)
#             cache_path2 = retrieve(dataset2, c)
#             self.assertTrue(os.path.exists(cache_path))
#             self.assertTrue(os.path.exists(cache_path2))

#             with open(cache_path) as f:
#                 self.assertEqual(f.read(), "test\n")

#             with open(cache_path2) as f:
#                 self.assertEqual(f.read(), "test 2\n")

#         self.assertFalse(os.path.exists(cache_path))
#         self.assertFalse(os.path.exists(cache_path2))
