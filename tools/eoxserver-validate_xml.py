#!/usr/bin/env python
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

import sys, os
from lxml import etree

"""
    Validate given XML document(s) against schema(s) referenced in 
    schemaLocation attribute of root element.
    
    Usage: validate_xml.py <xml-filename>
    
    Basically same as: xmllint --noout --schema <schema-filename> <xml-filename>
"""
if __name__ == "__main__" :
    # Validate all given files
    for name in sys.argv:
        # but not script itself
        if name == sys.argv[0]:
            continue
        # Check if file exists
        if not os.path.exists(name):
            print ("Usage: %s <xml-filename>" % sys.argv[0])
            sys.exit(1)

        print ("Validating XML document: %s" % name)
        doc = etree.parse(name).getroot()
        schema_locations = doc.get("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation")
        locations = schema_locations.split()
        
        # Create schema importing all referenced schemas
        schema_def = etree.Element("schema", attrib={
                "elementFormDefault": "qualified",
                "version": "1.0.0",
            }, nsmap={
                None: "http://www.w3.org/2001/XMLSchema"
            }
        )
        for ns, location in zip(locations[::2], locations[1::2]):
            etree.SubElement(schema_def, "import", attrib={
                    "namespace": ns,
                    "schemaLocation": location
                }
            )
            print ("Schema: Namespace: %s, Location: %s" % (ns, location))
        
        # TODO: Workaround, but otherwise the doc is not recognized as schema
        schema = etree.XMLSchema(etree.XML(etree.tostring(schema_def)))
        
        # Validate file against schema
        try:
            schema.assertValid(doc)
            print ("%s validates" % name)
        except etree.Error as e:
            print ("%s doesn't validate" % name)
            print ("Error was: %s" % str(e))
