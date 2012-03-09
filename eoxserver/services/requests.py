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

import email.generator
from cStringIO import StringIO

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
    
    def getHeader(self, header_name):
        META_WITHOUT_HTTP = (
            "CONTENT_LENGTH",
            "CONTENT_TYPE",
            "QUERY_STRING",
            "REMOTE_ADDR",
            "REMOTE_HOST",
            "REMOTE_USER",
            "REQUEST_METHOD",
            "SERVER_NAME",
            "SERVER_PORT"
        )
        
        tmp = header_name.upper().replace('-', '_')
        
        if tmp in META_WITHOUT_HTTP:
            header_key = tmp
        else:
            header_key = "HTTP_%s" % tmp
        
        return self.http_req.META.get(header_key)


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

class _Generator(email.generator.Generator):
    """ An adjusted version of the standard email.generator.Generator which adds
    a new-line character after a ';' character, which is not desired. 
    """
    def _write_headers(self, msg):
        for h, v in msg.items():
            print >> self._fp, '%s: %s' % (h, v)
        print >> self._fp

def encode_message(msg):
    """ Transform an email.message.Message to a string with out custom generator.
    """
    fp = StringIO()
    g = _Generator(fp)
    g.flatten(msg)
    return fp.getvalue()
