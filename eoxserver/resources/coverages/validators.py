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
from cStringIO import StringIO

from lxml import etree

from django.conf import settings
from django.core.exceptions import ValidationError

class EOOMSchema(object):
    # TODO: Change to online schema once available. 
    # Alternatively add configuration parameter to eoxserver.conf
    SCHEMA_LOCATION = os.path.join(settings.PROJECT_DIR, "..", "schemas", "omeo", "eop.xsd")
    schema = None
    
    @classmethod
    def getSchema(cls):
        if cls.schema is None:
            f = open(cls.SCHEMA_LOCATION)
            cls.schema = etree.XMLSchema(etree.parse(f))
            f.close()
        
        return cls.schema
        
def validateEOOM(xml):
    schema = EOOMSchema.getSchema()
    
    try:
        schema.assertValid(etree.fromstring(xml))
    except etree.Error as e:
        raise ValidationError(str(e))
    
def validateCoverageIDnotInEOOM(coverageID, xml):
    if xml is None or len(xml) == 0:
        return
    
    f = StringIO(xml)
    for _, element in etree.iterparse(f, events=("end",)):
        if element.get("{http://www.opengis.net/gml/3.2}id") == coverageID:
            raise ValidationError("The XML element '%s' contains a gml:id "
                                  "which is equal to the coverage ID '%s'." % 
                                  (element.tag, coverageID))
    
