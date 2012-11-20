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

import logging

from eoxserver.core.system import System
from eoxserver.testing.core import EOxServerTestCase, BASE_FIXTURES

logger = logging.getLogger(__name__)

BACKEND_FIXTURES = ["testing_coverages.json", "testing_backends.json"]

class BackendTestCase(EOxServerTestCase):
    fixtures = BASE_FIXTURES + BACKEND_FIXTURES

class LocationWrapperTestCase(BackendTestCase):
    def setUp(self):
        super(LocationWrapperTestCase,self).setUp()
        
        logger.info("Starting test case: %s" % self.__class__.__name__)
        
        self.record = self._get_record()
        
        self.factory = System.getRegistry().bind(
            "backends.factories.LocationFactory"
        )
        
        self.wrapper = self._get_wrapper()

    def _get_record(self):
        raise NotImplemented()

    def _get_wrapper(self):
        raise NotImplemented()

class LocationWrapperCreationTestCase(LocationWrapperTestCase):
    def testType(self):
        self.assertEqual(self.wrapper.getType(), self._get_type())
    
    def testValues(self):
        for method, value in self._get_values():
            self.assertEqual(getattr(self.wrapper, method)(), value)
    
    def _get_type(self):
        raise NotImplementedError()
    
    def _get_values(self):
        raise NotImplementedError()

class LocationWrapperCreateAndSaveTestCase(LocationWrapperTestCase):
    def setUp(self):
        super(LocationWrapperCreateAndSaveTestCase, self).setUp()
        self.wrapper.sync()

    def testType(self):
        self.assertEqual(
            self.wrapper.getType(), self.wrapper.getRecord().location_type
        )
    
    def testValues(self):
        raise NotImplementedError()

    def _get_record(self):
        return None
    
    def _get_wrapper(self):
        return self.factory.create(type=self._get_type(), **self._get_arguments())
    
    def _get_type(self):
        raise NotImplementedError()
    
    def _get_arguments(self):
        raise NotImplementedError()
    

# Specialized test cases for local, remote and rasdaman locations

# local

class LocalPathCreationTestCase(LocationWrapperCreationTestCase):
    def _get_type(self):
        return "local"
    
    def _get_values(self):
        return (
            ("getPath", self.record.path),
        )
    
class LocalPathCreateAndSaveTestCase(LocationWrapperCreateAndSaveTestCase):
    def _get_type(self):
        return "local"
        
# remote

class RemotePathCreationTestCase(LocationWrapperCreationTestCase):
    def _get_type(self):
        return "ftp"
    
    def _get_values(self):
        return (
            ("getHost", self.record.storage.host),
            ("getPort", self.record.storage.port),
            ("getUser", self.record.storage.user),
            ("getPassword", self.record.storage.passwd),
            ("getPath", self.record.path)
        )
        
class RemotePathCreateAndSaveTestCase(LocationWrapperCreateAndSaveTestCase):
    def _get_type(self):
        return "ftp"

# rasdaman

class RasdamanLocationCreationTestCase(LocationWrapperCreationTestCase):
    def _get_type(self):
        return "rasdaman"
    
    def _get_values(self):
        return (
            ("getCollection", self.record.collection),
            ("getOID", self.record.oid),
            ("getHost", self.record.storage.host),
            ("getPort", self.record.storage.port),
            ("getUser", self.record.storage.user),
            ("getPassword", self.record.storage.passwd)
        )

class RasdamanLocationCreateAndSaveTestCase(LocationWrapperCreateAndSaveTestCase):
    def _get_type(self):
        return "rasdaman"

