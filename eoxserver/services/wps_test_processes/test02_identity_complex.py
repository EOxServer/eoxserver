#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

import json
from lxml import etree
from StringIO import StringIO
from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import (
    ComplexData, CDObject, CDTextBuffer,
    FormatText, FormatXML, FormatJSON, #FormatBinaryRaw, FormatBinaryBase64,
)

class TestProcess02(Component):
    """ Test identity process (the ouptuts are copies of the inputs)
        demonstrating various features of the complex data inputs
        and outputs.
    """
    implements(ProcessInterface)

    identifier = "TC02:identity:complex"
    title = "Test Case 02: Complex data identity."
    metadata = {"test-metadata":"http://www.metadata.com/test-metadata"}
    profiles = ["test_profile"]

    inputs = [
        ("input00",
            ComplexData('TC02:input00',
                title="Test case #02: Complex input #00",
                abstract="Demonstrating use of the text-based complex input.",
                formats=(FormatText('text/plain'), FormatXML('text/xml'),
                          FormatJSON())
            )
        ),
    ]

    outputs = [
        ("output00",
            ComplexData('TC02:output00',
                title="Test case #02: Complex output #00",
                abstract="Copy of the input00.",
                formats=(FormatText('text/plain'), FormatXML('text/xml'),
                          FormatJSON())
            )
        ),
        ("output01",
            ComplexData('TC02:output01',
                title="Test case #02: Complex output #01",
                abstract="String representation of the input00.",
                formats=FormatText('text/plain')
            )
        ),
    ]

    @staticmethod
    def execute(input00):
        outputs = {}

        if input00.mime_type == "text/plain":
            # CDTextBuffer object inherited from StringIO - works with unicode
            outputs['output00'] = CDTextBuffer(input00.read()) # default format
            # provides 'data' propery for convenience (equivalent of 'read()')
            outputs['output01'] = StringIO(input00.data) # text also accepts StringIO

        elif input00.mime_type == "text/xml":
            # CDObject - generic object container - holds the xml.etree._Element
            # the etree._ElementTree object is accessible via the 'data' property
            outputs['output00'] = CDObject(input00.data, mime_type="text/xml")
            tmp = unicode(etree.tostring(input00.data, encoding='utf-8',
                    pretty_print=True), 'utf-8')
            outputs['output01'] = tmp # text also accepts unicode strings

        elif input00.mime_type == "application/json":
            # CDObject - generic object container - holds the parsed JSON # object
            outputs['output00'] = CDObject(input00.data, format=FormatJSON())
            # file-like text output
            tmp = CDTextBuffer()
            tmp.write(json.dumps(input00.data, ensure_ascii=False,
                                    indent=4, separators=(',', ': ')))
            outputs['output01'] = tmp

        return outputs
