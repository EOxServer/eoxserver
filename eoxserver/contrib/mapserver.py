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

import time
import logging
from cgi import escape
import tempfile
import os

from mapscript import *

from eoxserver.core.util.multiparttools import mpUnpack, mpPack, capitalize
from eoxserver.core.util.multiparttools import getMimeType, getMultipartBoundary
from eoxserver.contrib import gdal


logger = logging.getLogger(__name__)
is_xml = lambda ct: getMimeType(ct) in ("text/xml", "application/xml", "application/gml+xml")
is_multipart = lambda ct: getMimeType(ct).startswith("multipart/") 


class MapServerException(Exception):
    def __init__(self, message, locator):
        super(MapServerException, self).__init__(message)
        self.locator = locator


class Response(object):
    """ Data class for mapserver results. 
    """

    def __init__(self, content, content_type, status):
        self.content = content
        self.content_type = content_type

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
                    key = "%s_%s" % (namespace, key)

                super(MetadataMixIn, self).setMetaData(key, value)
        else:
            if namespace:
                key = "%s_%s" % (namespace, key_or_params)
            else:
                key = key_or_params

            return super(MetadataMixIn, self).setMetaData(key, value)


class Map(MetadataMixIn, mapObj):

    def dispatch(self, request):
        """ Wraps the ``OWSDispatch`` method. Perfoms all necessary steps for a 
            further handling of the result.
        """

        logger.debug("MapServer: Installing stdout to buffer.")
        msIO_installStdoutToBuffer()

        # write the map if debug is enabled
        if logger.isEnabledFor(logging.DEBUG):
            fd, filename = tempfile.mkstemp(text=True)
            try:
                with os.fdopen(fd) as f:
                    self.save(filename)
                    logger.debug(f.read())
            finally:
                os.remove(filename)
        
        try:
            logger.debug("MapServer: Dispatching.")
            ts = time.time()
            # Execute the OWS request by mapserver, obtain the status in 
            # dispatch_status (0 is OK)
            status = self.OWSDispatch(request)
            te = time.time()
            logger.debug("MapServer: Dispatch took %f seconds." % (te - ts))
        except Exception, e:
            raise MapServerException(str(e), "NoApplicableCode")
        
        logger.debug("MapServer: Retrieving content-type.")
        try:
            content_type = msIO_stripStdoutBufferContentType()
            msIO_stripStdoutBufferContentHeaders()

        except MapServerError:
            # degenerate response. Manually split headers from content
            result = msIO_getStdoutBufferBytes()
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
            result = msIO_getStdoutBufferBytes()
        
        logger.debug("MapServer: Performing MapServer cleanup.")
        # Workaround for MapServer issue #4369
        msversion = msGetVersionInt()
        if msversion < 60004 or (msversion < 60200 and msversion >= 60100):
            msCleanup()
        else:
            msIO_resetHandlers()
        
        return Response(result, content_type, status)


class Layer(MetadataMixIn, layerObj):
    def __init__(self, name, metadata=None, type=MS_LAYER_RASTER, mapobj=None):
        layerObj.__init__(self, mapobj)
        MetadataMixIn.__init__(self, metadata)
        self.name = name
        self.status = MS_ON
        if type == MS_LAYER_RASTER:
            self.dump = MS_TRUE
            self.setConnectionType(MS_RASTER, "")
        self.type = type


def create_request(values, request_type=MS_GET_REQUEST):
    used_keys = {}

    request = OWSRequest()
    request.type = request_type

    if request_type == MS_GET_REQUEST:
        for key, value in values:
            key = key.lower()
            used_keys.setdefault(key, 0)
            # addParameter() available in MapServer >= 6.2 
            # https://github.com/mapserver/mapserver/issues/3973
            try:
                request.addParameter(key.lower(), escape(value))
            # Workaround for MapServer 6.0
            except AttributeError:
                used_keys[key] += 1
                request.setParameter(
                    "%s_%d" % (key, used_keys[key]), escape(value)
                )
    elif request_type == MS_POST_REQUEST:
        request.postrequest = value

    return request


def gdalconst_to_imagemode(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a MapScript image mode constant.
    """
    if const == gdal.GDT_Byte:
        return MS_IMAGEMODE_BYTE
    elif const in (gdal.GDT_Int16, gdal.GDT_UInt16):
        return MS_IMAGEMODE_INT16
    elif const == GDT_Float32:
        return MS_IMAGEMODE_FLOAT32
    else:
        raise InternalError(
            "MapServer is not capable to process the datatype '%s' (%d)." 
            % gdal.GetDataTypeName(const), const
        )


def gdalconst_to_imagemode_string(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a string as used in the MapServer map file
    to denote an image mode.
    """
    if const == gdal.GDT_Byte:
        return "BYTE"
    elif const in (gdal.GDT_Int16, gdal.GDT_UInt16):
        return "INT16"
    elif const == gdal.GDT_Float32:
        return "FLOAT32"
