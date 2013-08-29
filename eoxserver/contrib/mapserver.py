#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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


import logging

import mapscript

from eoxserver.core.util.multiparttools import mpUnpack, mpPack, capitalize
from eoxserver.core.util.multiparttools import getMimeType, getMultipartBoundary


logger = logging.getLogger(__name__)
is_xml = lambda ct: getMimeType(ct) in ("text/xml", "application/xml", "application/gml+xml")
is_multipart = lambda ct: getMimeType(ct).startswith("multipart/") 


class Request(mapscript.OWSRequest):
    """ Convenience wrapper class over mapscripts ``OWSRequest``. Provides a 
        more pythonic interface and adds some convenience functions.
    """

    def __init__(self, params, type=mapscript.MS_GET_REQUEST):
        self._used_keys = {}

        self.type = type
        self.set_parameters(params)


    def set_parameters(self, params):
        if self.type == mapscript.MS_GET_REQUEST:
            for key, value in params.items():
                self[key] = value
        else:
            self.postrequest = params


    def __getitem__(self, key): 
        if isinstance(key, int):
            return self.getValue(key)
        else:
            return self.getValueByName(key)


    def __setitem__(self, key, value):
        key = key.lower()
        self._used_keys.setdefault(key, 0)

        # addParameter() available in MapServer >= 6.2 
        # https://github.com/mapserver/mapserver/issues/3973
        try:
            self.addParameter(key.lower(), escape(value))
        # Workaround for MapServer 6.0
        except AttributeError:
            self._used_keys[key] += 1
            self.setParameter(
                "%s_%d" % (key, self._used_keys[key]), escape(value)
            )


    def __len__(self):
        return self.NumParams
        

class Response(object):
    """ Data class for mapserver results. 
    """

    def __init__(self, content, content_type, status):
        pass

    @property
    def multipart(self):
        return


    def _split(self, content, content_type):

        if is_multipart(content_type): 
        
            # extract multipart boundary  
            boundary = getMultipartBoundary(content_type)

            for headers, offset, size in mpUnpack(content, boundary, capitalize=True):

                if is_xml( headers['Content-Type'] ) : 
                    self.ms_response_xml = self.content[offset:(offset+size)]
                    self.ms_response_xml_headers = headers
                else : 
                    self.ms_response_data = self.content[offset:(offset+size)] 
                    self.ms_response_data_headers = headers

        else: # single part payload 
            
            headers = headcap(headers)
            headers['Content-Type'] = self.content_type 

            if is_xml( self.content_type ) : 
                self.ms_response_xml = self.content
                self.ms_response_xml_headers = headers
            else : 
                self.ms_response_data = self.content 
                self.ms_response_data_headers = headers




class MetadataMixIn(object):
    """ Mix-In for classes that wrap mapscript objects with associated metadata.
    """

    def __init__(self, metadata=None):
        super(MetadataMixIn, self).__init__()
        if metadata:
            self.setMetaData(metadata)

    def __getitem__(self, key):
        self.getMetaData(key)

    def __setitem__(self, key, value):
        self.setMetaData(key, value)

    def setMetaData(self, key_or_params, value=None, namespace=None):
        """ Convenvience method to allow setting multiple metadata values with 
            one call and optionally setting a 'namespace' for each entry.
        """
        if value is None:
            for key, value in key_or_params.items():
                if namespace:
                    key = "%s_%s" % (key, namespace)

                super(MetadataMixIn, self).setMetaData(key, value)
        else:
            if namespace:
                key = "%s_%s" % (key_or_params, namespace)
            else:
                key = key_or_params

            return super(MetadataMixIn, self).setMetaData(key, value)


class Map(mapscript.mapObj, MetadataMixIn):

    def dispatch(self, request):
        """ Wraps the ``OWSDispatch`` method. Perfoms all necessary steps for a 
            further handling of the result.
        """

        logger.debug("MapServer: Installing stdout to buffer.")
        mapscript.msIO_installStdoutToBuffer()
        
        try:
            logger.debug("MapServer: Dispatching.")
            ts = time.time()
            # Execute the OWS request by mapserver, obtain the status in 
            # dispatch_status (0 is OK)
            status = self.OWSDispatch(request)
            te = time.time()
            logger.debug("MapServer: Dispatch took %f seconds." % (te - ts))
        except Exception, e:
            raise InvalidRequestException(
                str(e),
                "NoApplicableCode",
                None
            )
        
        logger.debug("MapServer: Retrieving content-type.")
        try:
            content_type = mapscript.msIO_stripStdoutBufferContentType()
            mapscript.msIO_stripStdoutBufferContentHeaders()

        except mapscript.MapServerError:
            # degenerate response. Manually split headers from content
            result = mapscript.msIO_getStdoutBufferBytes()
            parts = result.split("\r\n")
            result = parts[-1]
            headers = parts[:-1]
            
            for header in headers:
                if header.lower().startswith("content-type"):
                    content_type = header[14:]
                    break
            else:
                content_type = None

        else:
            logger.debug("MapServer: Retrieving stdout buffer bytes.")
            result = mapscript.msIO_getStdoutBufferBytes()
        
        logger.debug("MapServer: Performing MapServer cleanup.")
        # Workaround for MapServer issue #4369
        msversion = mapscript.msGetVersionInt()
        if msversion < 60004 or (msversion < 60200 and msversion >= 60100):
            mapscript.msCleanup()
        else:
            mapscript.msIO_resetHandlers()
        
        return Response(result, content_type, dispatch_status)
    


class Layer(mapscript.layerObj, MetadataMixIn):
    def __init__(self, name, metadata=None, type=mapscript.MS_LAYER_RASTER, mapobj=None):
        mapscript.layerObj.__init__(self, mapobj)
        MetadataMixIn.__init__(self, metadata)
        self.status = mapscript.MS_ON
        if type == MS_LAYER_RASTER:
            self.dump = MS_TRUE
            self.setConnectionType(mapscript.MS_RASTER, "")
        self.type = type
