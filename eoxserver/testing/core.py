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

import sys
import logging
import re
from StringIO import StringIO

from lxml import etree

from django.test import TestCase, TransactionTestCase
from django.test.simple import DjangoTestSuiteRunner, get_tests
from django.db.models.loading import get_app 
from django.core.management import execute_from_command_line

from eoxserver.core.system import System


logger = logging.getLogger(__name__)

BASE_FIXTURES = ["initial_rangetypes.json", "testing_base.json", "testing_asar_base.json"]

class TestSchemaFactory(object):
    schemas = {}
    
    @classmethod
    def getSchema(cls, schema_location):
        logger.info("Opening schema: %s" % schema_location)
        f = open(schema_location)
        schema = etree.XMLSchema(etree.parse(f))
        f.close()
        
        return schema
    

class EOxServerTestCase(TestCase):
    """Test are carried out in a transaction which is rolled back after each
    test."""
    fixtures = BASE_FIXTURES
    
    def setUp(self):
        System.init()

class CommandTestCase(EOxServerTestCase):
    """ Base class for testing CLI tools.
    """
    
    name = ""
    args = ()
    kwargs = {}
    expect_failure = False  
    
    def setUp(self):
        super(CommandTestCase, self).setUp()
        
        # construct command line parameters
        
        args = ["manage.py", self.name]
        if isinstance(args, (list, tuple)):
            args.extend(self.args)
        elif isinstance(args, basestring):
            #pylint: disable=E1101
            args.extend(self.args.split(" "))
        
        for key, value in self.kwargs.items():
            args.append("-%s" % key if len(key) == 1 else "--%s" % key)
            if isinstance(value, (list, tuple)):
                args.extend(value)
            else: 
                args.append(value)
        
        # redirect stderr to buffer
        sys.stderr = StringIO()
        
        # execute command
        self.execute_command(args)
        
        # reset stderr
        sys.stderr = sys.__stderr__    


    def execute_command(self, args):
        """ This function actually executes the given command. It raises a
        failure if the command prematurely quits.
        """
        
        try:
            execute_from_command_line(args)
        except SystemExit:
            if not self.expect_failure:
                self.fail("Command '%s' failed and exited. Message was: '%s'" % ( 
                          " ".join( args ) , 
                          "".join(sys.stderr.getvalue().rsplit("\n", 1)) ) ) 
        

class CommandFaultTestCase(CommandTestCase):
    """ Base class for CLI tool tests that expect failures (CommandErrors) to
    be raised.
    """
    
    expected_error = None
    
    def execute_command(self, args):
        """ Specialized implementation of the command execution. A failure is
        raised if no error occurs.
        """
        
        failure = False
        try:
            execute_from_command_line(args)
        except SystemExit:
            failure = True
        
        if not failure:
            self.fail("Command did not fail as expected.")
        
        if self.expected_error:
            self.assertEqual(sys.stderr.getvalue(), self.expected_error)
    
    def testFault(self):
        pass

def _expand_regex_classes(module, regex):
    ret = []
    for item in dir(module):
        cls = getattr(module, item)
        try:
            if ((issubclass(cls, TestCase) or 
                 issubclass(cls, TransactionTestCase)) 
                and re.match(regex, item)):
                ret.append(item)
        except TypeError:
            pass
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
    Custom test runner. It extends the standard 
    :class:`django.test.simple.DjangoTestSuiteRunner` 
    with automatic test case search for a given regular expression.
    
    Activate by including ``TEST_RUNNER = 
    'eoxserver.testing.core.EOxServerTestRunner'`` in `settings.py`.
    
    For example `services.WCS20` would get expanded to all test cases of the 
    `service` app starting with `WCS20`.
    
    Note that we're using regex and thus `services.WCS20\*` would get expanded 
    to all test cases of the `services` app starting with `WCS2` and followed 
    by any number of `0`\ s.
    
    Add test cases to exclude after a "|" character 
    e.g. services.WCS20GetCoverage|WCS20GetCoverageReprojectedEPSG3857DatasetTestCase,WCS20GetCoverageOutputCRSotherUoMDatasetTestCase
    """
    def build_suite(self, test_labels, extra_tests=None, **kwargs):
        new_labels = []
        for test_label in test_labels:
            parts = test_label.split('|')
            test_labels_exclude = None
            if len(parts) == 2:
                test_label = parts[0]
                test_labels_exclude = parts[1].split(',')
            
            parts = test_label.split('.')
            
            if len(parts) > 3 or len(parts) < 1:
                new_labels.append(test_label)
                continue
            
            app_module = get_app(parts[0])
            test_module = get_tests(app_module)
            
            classes = None
            
            if len(parts) == 1:
                classes = _expand_regex_classes(test_module, '')
                new_labels.extend([".".join((parts[0], klass)) for klass in classes])
            elif len(parts) == 2:
                classes = _expand_regex_classes(test_module, parts[1])
                new_labels.extend([".".join((parts[0], klass)) for klass in classes])
            else:
                classes = _expand_regex_classes(test_module, parts[1])
                for klass in classes:
                    methods = _expand_regex_method(test_module, klass, parts[2])
                    new_labels.extend([".".join((parts[0], klass, method)) for method in methods])
            
            if test_labels_exclude is not None:
                for test_label_exclude in test_labels_exclude:
                    try:
                        new_labels.remove(".".join((parts[0], test_label_exclude)))
                    except ValueError:
                        raise ValueError("Test '%s' to exclude not found." % test_label_exclude)
        
        return super(EOxServerTestRunner, self).build_suite(new_labels, extra_tests, **kwargs)
