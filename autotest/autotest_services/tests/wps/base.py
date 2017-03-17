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
# pylint: disable=invalid-name, missing-docstring, too-few-public-methods

from lxml import etree
from django.utils.dateparse import parse_datetime

XML_OPTS = {"pretty_print": True, "encoding": 'UTF-8', "xml_declaration": True}

WPS10_ExecuteResponse = "{http://www.opengis.net/wps/1.0.0}ExecuteResponse"
WPS10_Status = "{http://www.opengis.net/wps/1.0.0}Status"
WPS10_Capabilities = "{http://www.opengis.net/wps/1.0.0}Capabilities"
WPS10_ProcessOfferings = "{http://www.opengis.net/wps/1.0.0}ProcessOfferings"
WPS10_Process = "{http://www.opengis.net/wps/1.0.0}Process"
OWS11_Identifier = "{http://www.opengis.net/ows/1.1}Identifier"

class WPS10ExecuteMixIn(object):
    """ Mix-in class setting WPS 1.0 ExecuteResponse status time stamp
    to "2000-01-01T00:00:00.000000Z" in order to allow XML file comparison.
    """

    def prepareXMLData(self, xml_data):
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.fromstring(xml_data, parser)

        if xml.find('.').tag != WPS10_ExecuteResponse:
            return xml_data

        # Check the variable time-stamp and set it to a predefined constant.
        elm_status = xml.find(WPS10_Status)
        creation_time = elm_status.get("creationTime")
        elm_status.set("creationTime", "2000-01-01T00:00:00.000000Z")
        if None is parse_datetime(creation_time):
            raise ValueError(
                "Invalid creation time attribute of the execute"
                " response status! creationTime=%r" % creation_time
            )

        return etree.tostring(xml, **XML_OPTS)


class WPS10CapabilitiesMixIn(object):
    """ Mix-in class filtering the WPS 1.0 Capabilities and optionally removing
    process offerings which should not be included in XML file comparison.
    """

    def prepareXMLData(self, xml_data):
        parser = etree.XMLParser(remove_blank_text=True)
        xml = etree.fromstring(xml_data, parser)

        if xml.find('.').tag != WPS10_Capabilities:
            return xml_data

        process_offerings_elm = xml.find(WPS10_ProcessOfferings)
        if process_offerings_elm is None:
            return xml_data

        def _process_id(elm):
            " Extract process identifier from the given wps:Process element. "
            id_elm = elm.find(OWS11_Identifier)
            return None if id_elm is None else id_elm.text

        # filter out process offerings not listed in the allowed processes
        if hasattr(self, 'allowedProcesses'):
            allowed_processes = set(self.allowedProcesses)

            for process_elm in process_offerings_elm.findall(WPS10_Process):
                if _process_id(process_elm) not in allowed_processes:
                    # remove non-listed process offering
                    process_elm.getparent().remove(process_elm)

        # sort process offerings to get a predictable element order
        process_offerings_elm[:] = sorted(
            process_offerings_elm, key=lambda elm: (elm.tag, _process_id(elm))
        )

        return etree.tostring(xml, **XML_OPTS)


class ContentTypeCheckMixIn(object):
    """ Mix-in class adding test of the response Content-Type header. """

    def testContentType(self):
        if hasattr(self, 'expectedContentType'):
            content_type = self.getResponseHeader('Content-Type')
            self.assertEqual(self.expectedContentType, content_type)


class ContentDispositionCheckMixIn(object):
    """ Mix-in class adding test of the response Content-Disposition header. """

    def testContentDisposition(self):
        if hasattr(self, 'expectedContentDisposition'):
            content_disposition = self.getResponseHeader('Content-Disposition')
            self.assertEqual(
                self.expectedContentDisposition, content_disposition
            )
