#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

from lxml import etree
from django.utils.dateparse import parse_datetime

XML_OPTS = {"pretty_print": True, "encoding": 'UTF-8', "xml_declaration": True}

class WPS10ExecuteMixIn(object):
    def prepareXMLData(self, xml_data):
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.fromstring(xml_data, parser)

        if xml.find('.').tag != "{http://www.opengis.net/wps/1.0.0}ExecuteResponse":
            return xml_data

        # Check the variable time-stamp and set it to a predefined constant.
        elm_status = xml.find("{http://www.opengis.net/wps/1.0.0}Status")
        creation_time = elm_status.get("creationTime")
        elm_status.set("creationTime", "2000-01-01T00:00:00.000000Z")
        if None is parse_datetime(creation_time):
            raise ValueError("Invalid creation time attribute of the execute"
                " response status! creationTime=%r"%creation_time)

        return etree.tostring(xml, **XML_OPTS)

class ContentTypeCheckMixIn(object):
    def testContentType(self):
        if hasattr(self, 'expectedContentType'):
            content_type = self.getResponseHeader('Content-Type')
            self.assertEqual(self.expectedContentType, content_type)

class ContentDispositionCheckMixIn(object):
    def testContentDisposition(self):
        if hasattr(self, 'expectedContentDisposition'):
            content_disposition = self.getResponseHeader('Content-Disposition')
            self.assertEqual(
                self.expectedContentDisposition, content_disposition
            )
