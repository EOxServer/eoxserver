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
import logging
from lxml import etree
from xml.dom import minidom
import tempfile
import mimetypes
from osgeo import gdal, gdalconst

import email

from django.test import TestCase, Client

from eoxserver.core.system import System
from eoxserver.core.util.xmltools import XMLDecoder, DOMtoXML
#from eoxserver.resources.coverages.synchronize import DatasetSeriesSynchronizer,\
#    RectifiedStitchedMosaicSynchronizer

BASE_FIXTURES = ["initial_rangetypes.json", "testing_base.json"]

class TestSchemaFactory(object):
    schemas = {}
    
    @classmethod
    def getSchema(cls, schema_location):
#        # Singleton version for usage with remote schemas:
#        # This version provides hugh performance advantages but 
#        # also random segfaults in libxml2.
#        if schema_location in cls.schemas:
#            return cls.schemas[schema_location]
#        else:
#            logging.info("Opening schema: %s" % schema_location)
#            f = open(schema_location)
#            schema = etree.XMLSchema(etree.parse(f))
#            f.close()
#            
#            cls.schemas[schema_location] = schema
#            
#            return schema
        # Non singleton version for usage with locally stored schemas:
        logging.info("Opening schema: %s" % schema_location)
        f = open(schema_location)
        schema = etree.XMLSchema(etree.parse(f))
        f.close()
        
        return schema
    
class EOxServerTestCase(TestCase):
    fixtures = BASE_FIXTURES
    
    def setUp(self):
        System.init()
        
