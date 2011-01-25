#-----------------------------------------------------------------------
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from email.parser import Parser as MIMEParser
from email.message import Message

import logging

from eoxserver.lib.util import EOxSKVPDecoder, EOxSXMLDecoder

from eoxserver.contrib import mapscript

class EOxSOWSRequest(object):
    def __init__(self, params='', param_type='kvp', decoder=None):
        super(EOxSOWSRequest, self).__init__()
        
        self.params = params
        
        if decoder is None:
            if param_type == 'kvp':
                self.decoder = EOxSKVPDecoder(params)
            elif param_type == 'xml':
                self.decoder = EOxSXMLDecoder(params)
        else:
            self.decoder = decoder
        
        self.version = ""
        
        self.coverages = []
    
    def setSchema(self, schema):
        self.decoder.setSchema(schema)
    
    def getParamValue(self, key):
        return self.decoder.getValue(key)
    
    def getParams(self):
        return self.decoder.getParams()
    
    def getParamType(self):
        return self.decoder.getParamType()
        
    def setVersion(self, version):
        self.version = version
    
    def getVersion(self):
        return self.version

class EOxSMapServerRequest(EOxSOWSRequest):
    def __init__(self, req):
        super(EOxSMapServerRequest, self).__init__(params=req.params, decoder=req.decoder)
        
        self.version = req.version
        
        self.map = mapscript.mapObj()
        self.ows_req = mapscript.OWSRequest()

class EOxSResponse(object):
    def __init__(self, content='', content_type='text/xml', headers={}, status=None):
        super(EOxSResponse, self).__init__()
        self.content = content
        self.content_type = content_type
        self.headers = headers
        self.status = status
        
    def getContent(self):
        return self.content
        
    def getContentType(self):
        return self.content_type
        
    def getHeaders(self):
        return self.headers
        
    def getStatus(self):
        return self.status
        

class EOxSMapServerResponse(EOxSResponse):
    def __init__(self, ms_response, ms_content_type, ms_status, headers={}, status=None):
        super(EOxSMapServerResponse, self).__init__(content=ms_response, content_type=ms_content_type, headers=headers, status=status)
        self.ms_status = ms_status
        
        self.ms_response_data = None
        self.ms_response_xml = ''
        self.ms_response_xml_headers = {}
        
    def _isXML(self, content_type):
        return content_type.split(";")[0].lower() in ("text/xml", "application/xml")
            
    def _isMultipart(self, content_type):
        return content_type.split("/")[0].lower() == "multipart"
        
    def splitResponse(self):
        if self._isXML(self.content_type):
            self.ms_response_xml = self.content
            self.ms_response_xml_headers = {'Content-type': self.content_type}
        elif self._isMultipart(self.content_type):
            parts = MIMEParser().parsestr("Content-type:%s\n\n%s" % (self.content_type, self.content.rstrip("--wcs--\n\n"))).get_payload()
            for part in parts:
                if self._isXML(part.get_content_type()):
                    self.ms_response_xml = part.get_payload()
                    for header in part.keys():
                        self.ms_response_xml_headers[header] = part[header]
                else:
                    self.ms_response_data = part
        else:
            self.ms_response_data = self.content
    
    def getProcessedResponse(self, processed_xml, processed_xml_headers=None):
        if self.ms_response_data is not None:
            xml_msg = Message()
            xml_msg.set_payload(processed_xml)
            
            if processed_xml_headers is not None:
                xml_headers = processed_xml_headers
            else:
                xml_headers = self.ms_response_xml_headers
            for name, value in xml_headers.items():
                xml_msg.add_header(name, value)
            
            if isinstance(self.ms_response_data, Message):
                data_msg = self.ms_response_data
            else:
                data_msg = Message()
                
                data_msg.set_payload(self.ms_response_data)
                
                data_msg.add_header('Content-type', self.content_type)
                for name, value in self.headers.items():
                    data_msg.add_header(name, value)
                
            content = "--wcs\n%s\n--wcs\n%s\n--wcs--" % (xml_msg.as_string(), data_msg.as_string())
            content_type = "multipart/mixed; boundary=wcs"
            headers = {}
        else:
            content = processed_xml
            content_type = self.content_type
            if processed_xml_headers is None:
                headers = self.headers
            else:
                headers = processed_xml_headers
            
        return EOxSResponse(content, content_type, headers, self.getStatus())
        
    def getContentType(self):
        if "Content-type" in self.headers:
            return self.headers["Content-type"]
        else:
            return self.content_type # TODO: headers for multipart messages
        
    def getStatus(self):
        if self.status is None:
            if self.ms_status is not None and self.ms_status == 0:
                return 200
            else:
                return 400
        else:
            return self.status
