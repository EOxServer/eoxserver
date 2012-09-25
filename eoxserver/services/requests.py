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

"""
This module defines basic classes for OWS requests and responses to
OWS requests.
"""

from eoxserver.core.util.xmltools import XMLDecoder
from eoxserver.core.util.kvptools import KVPDecoder

class OWSRequest(object):
    """
    This class is used to encapsulate information about an OWS request.
    
    The constructor expects one required parameter, a Django
    :class:`~django.http.HttpRequest` object ``http_req``.
    
    The ``params`` argument shall contain the parameters sent with the
    request. For GET requests, this can either contain a Django
    :class:`~django.http.QueryDict` object or the query string itself. For POST requests,
    the argument shall contain the message body as a string.
    
    The ``param_type`` argument shall be set to ``kvp`` for GET
    requests and ``xml`` for POST requests.
    
    Optionally, a decoder (either a :class:`~.KVPDecoder` or
    :class:`~.XMLDecoder` instance initialized with the parameters) can already 
    be conveyed to the request. If it is not present, the appropriate decoder 
    type will be chosen and initialized based on the values of ``params`` and
    ``param_type``.
    """
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
        """
        Set the decoding schema for the parameter decoder (see
        :mod:`eoxserver.core.util.decoders`)
        """
        self.decoder.setSchema(schema)
    
    def getParamValue(self, key, default=None):
        """
        Returns the value of a parameter named ``key``. The name relates to
        the schema set for the decoder. You can provide a default value which
        will be returned if the parameter is not present.
        """
        return self.decoder.getValue(key, default)
    
    def getParamValueStrict(self, key):
        """
        Returns the value of a parameter named ``key``. The name relates to
        the schema set for the decoder. A :exc:`~.DecoderException` will be
        raised if the parameter is not present.
        """
        return self.decoder.getValueStrict(key)
    
    def getParams(self):
        """
        Returns the parameters. This method calls the :class:`~.KVPDecoder` or
        :class:`~.XMLDecoder` method of the same name. In case of KVP data,
        this means that a dictionary with the parameter values will be returned
        instead of the query string, even if the :class:`OWSRequest` object
        was initially configured with the query string.
        """
        return self.decoder.getParams()
    
    def getParamType(self):
        """
        Returns ``kvp`` or ``xml``.
        """
        return self.decoder.getParamType()
        
    def setVersion(self, version):
        """
        Sets the version for the OGC Web Service. This method is used
        for version negotiation, in which case the appropriate version cannot
        simply be read from the request parameters.
        """
        self.version = version
    
    def getVersion(self):
        """
        Returns the version for the OGC Web Service. This method is used
        for version negotiation, in which case the appropriate version cannot
        simply be read from the request parameters.
        """
        return self.version
    
    def getHeader(self, header_name):
        """
        Returns the value of the HTTP header ``header_name``, or ``None`` if not
        found.
        """
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
    """
    This class encapsulates the data needed for an HTTP response to an OWS
    request.
    
    The ``content`` argument contains the content of the response message. The
    ``content_type`` argument is set to the MIME type of the response content.
    The ``headers`` argument is expected to be a dictionary of additional
    HTTP headers to be sent with the response. The ``status`` parameter is
    used to set the HTTP status of the response.
    """
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
