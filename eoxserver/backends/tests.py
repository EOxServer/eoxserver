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

import os.path
from glob import glob
import logging

from django.test import TestCase

from eoxserver.backends import testbase
from eoxserver.backends import models
from eoxserver.backends.cache import CacheContext
from eoxserver.backends.access import retrieve
from eoxserver.backends.component import BackendComponent, env

logger = logging.getLogger(__name__)


""" "New" data models
"""


def create(Model, *args, **kwargs):
    model = Model(*args, **kwargs)
    model.full_clean()
    model.save()
    return model



class RetrieveTestCase(TestCase):
    def setUp(self):
        pass


    def tearDown(self):
        pass


    def test_retrieve_http(self):
        storage = create(models.Storage,
            url="http://eoxserver.org/export/2523/downloads",
            storage_type="HTTP"
        )
        dataset = create(models.Dataset,
            location="EOxServer_documentation-0.3.0.pdf",
            storage=storage
        )

        with CacheContext() as c:
            cache_path = retrieve(dataset, c)
            self.assertTrue(os.path.exists(cache_path))


    def test_retrieve_ftp_zip(self):
        import storages, packages
        c  = BackendComponent(env)
        print c.storages

        storage = create(models.Storage,
            url="ftp://anonymous:@localhost:2121/",
            storage_type="FTP"
        )

        package = create(models.Package,
            location="package.zip",
            format="ZIP",
            storage=storage
        )

        dataset = create(models.Dataset,
            location="file.txt",
            package=package
        )

        with CacheContext() as c:
            cache_path = retrieve(dataset, c)
            self.assertTrue(os.path.exists(cache_path))
            with open(cache_path) as f:
                self.assertEqual(f.read(), "test")

        self.assertFalse(os.path.exists(cache_path))














# test local path wrapper: get() with record and check wrapper type and
# return values

class LocalPathGetWithRecordTestCase(testbase.LocalPathCreationTestCase):
    def _get_record(self):
        return LocalPath.objects.get(pk=1)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)

# test local path wrapper: get() with primary key and check wrapper type and
# return values

class LocalPathGetWithPrimaryKeyTestCase(testbase.LocalPathCreationTestCase):
    def _get_record(self):
        return LocalPath.objects.get(pk=1)
    
    def _get_wrapper(self):
        return self.factory.get(pk=1)

# test local path wrapper: initialize with attributes and check wrapper type
# and return values

class LocalPathCreateWithAttributesTestCase(testbase.LocalPathCreationTestCase):
    def _get_record(self):
        return None
    
    def _get_wrapper(self):
        return self.factory.create(type="local", path="some/path")
    
    def _get_values(self):
        return (
            ("getPath", "some/path"),
        )

# test local path wrapper: initialize with attributes and save to database

class LocalPathCreateAndSaveTestCase(testbase.LocalPathCreateAndSaveTestCase):
    def testValues(self):
        record = self.wrapper.getRecord()
        values = self._get_arguments()
        
        self.assertEqual(record.path, values["path"])
    
    def _get_arguments(self):
        return {
            "path": "some/path"
        }

# test access to local data: open

# test access to local data: getLocalCopy

# test access to local data: getSize

class LocalAccessTestCase(testbase.LocationWrapperTestCase):
    def _get_record(self):
        return LocalPath.objects.get(pk=1)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)
    
    def testOpen(self):
        f = self.wrapper.open()
        
        self.assert_(isinstance(f, file))
    
    def testLocalCopy(self):
        
        target = "/tmp"
        
        dest_path = os.path.join(target, os.path.basename(self.wrapper.getPath()))
        
        target_wrapper = self.wrapper.getLocalCopy(target)
        
        self.assertEqual(target_wrapper.getPath(), dest_path)
        
        self.assert_(os.path.exists(dest_path))
        
    def testSize(self):
        size = os.path.getsize(self.wrapper.getPath())
        
        self.assertEqual(self.wrapper.getSize(), size)

# test access to local data: detect (without search_pattern)

# test access to local data: detect (with search_pattern)

class LocalDetectionTestCase(testbase.LocationWrapperTestCase):
    def _get_record(self):
        return LocalPath.objects.get(pk=13)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)
    
    def testDetectWithoutSearchPattern(self):
        locations = self.wrapper.detect()
        
        paths = [location.getPath() for location in locations]
        
        dir_paths = glob(os.path.join(self.wrapper.getPath(), "*")) +\
                    glob(os.path.join(self.wrapper.getPath(), "*", "*"))
        
        logger.debug("found files: %s" % ", ".join(paths))
        
        logger.debug("files in dir: %s" % ", ".join(dir_paths))
        
        self.assertItemsEqual(paths, dir_paths)
    
    def testDetectWithSearchPattern(self):
        locations = self.wrapper.detect("*.tif")
        
        names = [os.path.basename(location.getPath()) for location in locations]
        
        dir_names = [
            os.path.basename(path)
            for path in glob(os.path.join(self.wrapper.getPath(), "*.tif"))
        ]
        
        self.assertItemsEqual(names, dir_names)

# test remote path wrapper: get with record and check return values

class RemotePathGetWithRecordTestCase(testbase.RemotePathCreationTestCase):
    def _get_record(self):
        return RemotePath.objects.get(pk=15)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)

# test remote path wrapper: get with primary key and check return values

class RemotePathGetWithPrimaryKeyTestCase(testbase.RemotePathCreationTestCase):
    def _get_record(self):
        return RemotePath.objects.get(pk=15)
    
    def _get_wrapper(self):
        return self.factory.get(pk=15)

# test remote path wrapper: initialize with attributes and check return values

class RemotePathCreateWithAttributesTestCase(testbase.RemotePathCreationTestCase):
    def _get_record(self):
        return None
    
    def _get_wrapper(self):
        return self.factory.create(
            type="ftp",
            host="ftp.example.org",
            port=21,
            user="anonymous",
            passwd="anonymous",
            path="some/path"
        )
    
    def _get_values(self):
        return (
            ("getHost", "ftp.example.org"),
            ("getPort", 21),
            ("getUser", "anonymous"),
            ("getPassword", "anonymous"),
            ("getPath", "some/path"),
        )

# test remote path wrapper: initialize with attributes and save to database

class RemotePathCreateAndSaveTestCase(testbase.RemotePathCreateAndSaveTestCase):
    def testValues(self):
        record = self.wrapper.getRecord()
        values = self._get_arguments()
        
        self.assertEqual(record.storage.host, values["host"]),
        self.assertEqual(record.storage.port, values["port"]),
        self.assertEqual(record.storage.user, values["user"]),
        self.assertEqual(record.storage.passwd, values["passwd"]),
        self.assertEqual(record.path, values["path"])
    
    def _get_arguments(self):
        return {
            "host": "ftp.example.org",
            "port": 21,
            "user": "anonymous",
            "passwd": "anonymous",
            "path": "some/path"
        }
        
# test access to remote data: getLocalCopy

# test access to remote data: getSize

class RemoteAccessTestCase(testbase.LocationWrapperTestCase):
    def _get_record(self):
        return RemotePath.objects.get(pk=15)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)
    
    def testLocalCopy(self):
        logger.debug("Retrieving remote file '%s'" % self.wrapper.getPath())
        
        target = "/tmp"
        
        dest_path = os.path.join(target, os.path.basename(self.wrapper.getPath()))
        
        target_wrapper = self.wrapper.getLocalCopy(target)
        
        self.assertEqual(target_wrapper.getPath(), dest_path)
        
        self.assert_(os.path.exists(dest_path))
        
    def testSize(self):
        size = 5992628
        
        self.assertEqual(self.wrapper.getSize(), size)

# test access to remote data: detect (without search_pattern)

# test access to remote data: detect (with search_pattern)

class RemoteDetectionTestCase(testbase.LocationWrapperTestCase):
    def _get_record(self):
        return RemotePath.objects.get(pk=27)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)
    
    def testDetectWithoutSearchPattern(self):
        locations = self.wrapper.detect()
        
        paths = [location.getPath() for location in locations]
        
        dir_paths = RemotePath.objects.filter(pk__in=range(15,24)).values_list(
            'path', flat=True
        )
        
        logger.debug("testDetectWithoutSearchPattern()")
        
        logger.debug("found files: %s" % ", ".join(paths))
        
        logger.debug("files in dir: %s" % ", ".join(dir_paths))
        
        self.assertItemsEqual(paths, dir_paths)
    
    def testDetectWithSearchPattern(self):
        locations = self.wrapper.detect("*.tif")
        
        paths = [location.getPath() for location in locations]
        
        dir_paths = RemotePath.objects.filter(pk__in=(15,18,21)).values_list(
            'path', flat=True
        )

        logger.debug("testDetectWithSearchPattern()")
        
        logger.debug("found files: %s" % ", ".join(paths))
        
        logger.debug("files in dir: %s" % ", ".join(dir_paths))
        
        self.assertItemsEqual(paths, dir_paths)
        

# test rasdaman location wrapper: get with record and check return values

class RasdamanLocationGetWithRecordTestCase(testbase.RasdamanLocationCreationTestCase):
    def _get_record(self):
        return RasdamanLocation.objects.get(pk=28)
    
    def _get_wrapper(self):
        return self.factory.get(record=self.record)

# test rasdaman location wrapper: get with primary key and check return values

class RasdamanLocationGetWithPrimaryKeyTestCase(testbase.RasdamanLocationCreationTestCase):
    def _get_record(self):
        return RasdamanLocation.objects.get(pk=28)
    
    def _get_wrapper(self):
        return self.factory.get(pk=28)
    

# test rasdaman location wrapper: initialize with attributes and check return values

class RasdamanLocationCreateWithAttributesTestCase(testbase.RasdamanLocationCreationTestCase):
    def _get_record(self):
        return None
    
    def _get_wrapper(self):
        return self.factory.create(
            type="rasdaman",
            host="rasdaman.example.org",
            port=7001,
            user="anonymous",
            passwd="anonymous",
            db_name="",
            collection="some_other_collection",
            oid=2.0
        )
    
    def _get_values(self):
        return (
            ("getHost", "rasdaman.example.org"),
            ("getPort", 7001),
            ("getUser", "anonymous"),
            ("getPassword", "anonymous"),
            ("getCollection", "some_other_collection"),
            ("getOID", 2.0)
        )

# test rasdaman location wrapper: initialize with attributes and save to database

class RasdamanLocationCreateAndSaveTestCase(testbase.RasdamanLocationCreateAndSaveTestCase):
    def testValues(self):
        record = self.wrapper.getRecord()
        values = self._get_arguments()
        
        self.assertEqual(record.storage.host, values["host"]),
        self.assertEqual(record.storage.port, values["port"]),
        self.assertEqual(record.storage.user, values["user"]),
        self.assertEqual(record.storage.passwd, values["passwd"]),
        self.assertEqual(record.collection, values["collection"])
        self.assertEqual(record.oid, values["oid"])
    
    def _get_arguments(self):
        return {
            "host": "rasdaman.example.org",
            "port": 7001,
            "user": "anonymous",
            "passwd": "anonymous",
            "db_name": "",
            "collection": "some_other_collection",
            "oid": 2.0,
            "location_type": "rasdaman"
        }

# test access to rasdaman data -> resources.coverages.tests (the rasdaman storage offers no low-level access capabilities)
