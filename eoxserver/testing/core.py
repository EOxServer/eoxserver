#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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
import re

from lxml import etree

from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner, get_tests
from django.db.models.loading import get_app 

from eoxserver.core.system import System

BASE_FIXTURES = ["initial_rangetypes.json", "testing_base.json", "testing_asar_base.json"]

class TestSchemaFactory(object):
    schemas = {}
    
    @classmethod
    def getSchema(cls, schema_location):
        logging.info("Opening schema: %s" % schema_location)
        f = open(schema_location)
        schema = etree.XMLSchema(etree.parse(f))
        f.close()
        
        return schema
    
class EOxServerTestCase(TestCase):
    fixtures = BASE_FIXTURES
    
    def setUp(self):
        System.init()

def _expand_regex_classes(module, regex):
    ret = []
    for item in dir(module):
        if re.match(regex, item):
            ret.append(item)
    if not ret:
        raise ValueError("Expression %s did not match any test." % regex)
    return ret

def _expand_regex_method(module, klass, regex):
    ret = []
    for item in dir(getattr(module, klass)):
        if re.match(regex, item):
            ret.append(item)
    if not ret:
        raise ValueError("Expression %s did not match any test." % regex)
    return ret

class EOxServerTestRunner(DjangoTestSuiteRunner):
    """ 
    Custom test runner. It extends the standard :class:`~.DjangoTestRunner` 
    with automatic test case search for a given regular expression.
    
    Activate by including ``TEST_RUNNER = 
    'eoxserver.testing.core.EOxServerTestRunner'`` in `settings.py`.
    
    For example `services.WCS20` would get expanded to all test cases of the 
    `service` app starting with `WCS20`.
    
    Note that we're using regex and thus `services.WCS20\*` would get expanded 
    to all test cases of the `services` app starting with `WCS2` and followed 
    by any number of `0`\ s.
    """
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        new_labels = []
        for test_label in test_labels:
            parts = test_label.split('.')
            
            if len(parts) > 3 or len(parts) < 1:
                new_labels.append(test_label)
                continue
            
            app_module = get_app(parts[0])
            test_module = get_tests(app_module)
            
            classes = None
            
            if len(parts) == 1:
                new_labels.append(parts[0])
            elif len(parts) == 2:
                classes = _expand_regex_classes(test_module, parts[1])
                new_labels.extend([".".join((parts[0], klass)) for klass in classes])
            else:
                classes = _expand_regex_classes(test_module, parts[1])
                for klass in classes:
                    methods = _expand_regex_method(test_module, klass, parts[2])
                    new_labels.extend([".".join((parts[0], klass, method)) for method in methods])
        
        return super(EOxServerTestRunner, self).build_suite(new_labels, extra_tests, **kwargs)
