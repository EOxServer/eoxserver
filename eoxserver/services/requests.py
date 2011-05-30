#-----------------------------------------------------------------------
# $Id$
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



import logging

from eoxserver.core.util.xmltools import XMLDecoder
from eoxserver.core.util.kvptools import KVPDecoder

class OWSRequest(object):
    def __init__(self, http_req, params='', param_type='kvp', decoder=None):
        super(OWSRequest, self).__init__()
        
        self.http_req = http_req
        
        self.params = params
        
        if decoder is None:
            if param_type == 'kvp':
                self.decoder = KVPDecoder(params)
            elif param_type == 'xml':
                self.decoder = XMLDecoder(params)
        else:
            self.decoder = decoder
        
        self.version = ""
        
        self.coverages = []
    
    def setSchema(self, schema):
        self.decoder.setSchema(schema)
    
    def getParamValue(self, key, default=None):
        return self.decoder.getValue(key, default)
    
    def getParamValueStrict(self, key):
        return self.decoder.getValueStrict(key)
    
    def getParams(self):
        return self.decoder.getParams()
    
    def getParamType(self):
        return self.decoder.getParamType()
        
    def setVersion(self, version):
        self.version = version
    
    def getVersion(self):
        return self.version


class Response(object):
    def __init__(self, content='', content_type='text/xml', headers={}, status=None):
        super(Response, self).__init__()
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
        

