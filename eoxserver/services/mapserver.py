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
This module contains the abstract base classes for request handling.
"""

import logging
import os.path
from cgi import escape
import time

from django.conf import settings
import mapscript

from eoxserver.core.interfaces import Method, ObjectArg, ListArg
from eoxserver.core.registry import RegisteredInterface
from eoxserver.core.exceptions import InternalError
from eoxserver.contrib.gdal import GDT_Byte, GDT_Int16, GDT_UInt16, GDT_Float32 
from eoxserver.services.base import BaseRequestHandler
from eoxserver.services.requests import OWSRequest, Response
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.core.util.multiparttools import mpUnpack, mpPack, capitalize
from eoxserver.core.util.multiparttools import getMimeType, getMultipartBoundary


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# utilities 

# content-type parsing  
is_xml       = lambda ct : getMimeType(ct) in ("text/xml","application/xml","application/gml+xml")
is_multipart = lambda ct : getMimeType(ct).startswith("multipart/") 

# capilatize header names 
_headcap = lambda p : ( capitalize(p[0]) , p[1] ) 
headcap  = lambda h : dict( map( _headcap , h.items() ) )  

#-------------------------------------------------------------------------------

class MapServerRequest(OWSRequest):
    """
    This class inherits from :class:`~.OWSRequest`.
    
    The constructor expects a single argument ``req`` which is expected to
    contain an :class:`~.OWSRequest` instance. The parameters and decoder
    will be taken from that instance.
    
    :class:`MapServerRequest` objects add two properties: first a ``map``
    property which contains a :class:`mapscript.mapObj`, and second an
    ``ows_req`` property which contains a :class:`mapscript.OWSRequest`
    object. These properties are not configured at the beginning.
    """
    def __init__(self, req):
        super(MapServerRequest, self).__init__(req.http_req, params=req.params, decoder=req.decoder)
        
        self.version = req.version
        
        self.map = mapscript.mapObj()
        self.ows_req = mapscript.OWSRequest()

class MapServerResponse(Response):
    """
    This class inherits from :class:`~.Response`. It adds methods to handle
    with response data obtained from MapServer, including methods for
    multipart messages.
    
    The constructor takes several arguments. In ``ms_response``, the response
    buffer as returned by MapServer is expected. The ``ms_content_type``
    argument shall be set to the MIME type of the response content.
    ``ms_status`` shall contain the MapServer status as returned by the
    call to :meth:`mapscript.mapObj.OWSDispatch`. ``headers`` and ``status``
    are optional and have the same meaning as in :class:`~.Response`.
    """
    
    def __init__(self, ms_response, ms_content_type, ms_status, headers={}, status=None):
        super(MapServerResponse, self).__init__(content=ms_response, content_type=ms_content_type, headers=headers, status=status)
        self.ms_status = ms_status
        
        self.ms_response_data = None
        self.ms_response_data_headers = {} 
        self.ms_response_xml = None 
        self.ms_response_xml_headers = {}
        
    def splitResponse(self):
        """
        This method splits a multipart response into its different parts.
        
        The XML part is stored in the ``ms_response_xml`` property of the
        object. The coverage data is stored in the ``ms_response_data``
        property of the object. The headers of the parts are stored in
        the ``ms_response_xml_headers`` and ``ms_response_data_headers``
        properties respectively.
        """

        if is_multipart( self.content_type ) : 
        
            # extract multipart boundary  
            boundary = getMultipartBoundary( self.content_type ) 

            for headers,offset,size in mpUnpack(self.content,boundary,capitalize=True) :

                if is_xml( headers['Content-Type'] ) : 
                    self.ms_response_xml = self.content[offset:(offset+size)]
                    self.ms_response_xml_headers = headers
                else : 
                    self.ms_response_data = self.content[offset:(offset+size)] 
                    self.ms_response_data_headers = headers

        else : # single part payload 
            
            headers = headcap( self.headers )
            headers['Content-Type'] = self.content_type 

            if is_xml( self.content_type ) : 
                self.ms_response_xml = self.content
                self.ms_response_xml_headers = headers
            else : 
                self.ms_response_data = self.content 
                self.ms_response_data_headers = headers

    
    def getProcessedResponse(self, response_xml, headers_xml=None, boundary="wcs", subtype="mixed"):
        """
        This method returns a :class:`~.Response` object that contains the
        coverage data generated by the original MapServer call and the
        XML data contained in the ``response_xml`` argument.
        
        The ``headers_xml`` parameter may contain a dictionary of headers
        to be tagged on the XML part of the multipart response. The
        ``boundary`` argument shall contain the boundary string used for
        delimiting the different parts of the message and defaults to ``wcs``.
        The ``subtype`` argument relates to the second part of the MIME type
        statement and defaults to ``mixed`` for a complete MIME type of
        ``multipart/mixed``.
        """
        if self.ms_response_data is not None: # mutipart response   

            if headers_xml is None: headers_xml = self.ms_response_xml_headers

            # normalize header content 
            headers_xml  = headcap( headers_xml )
            headers_data = headcap( self.ms_response_data_headers ) 

            # prepare multipart package 
            parts = [ 
                  ( headers_xml.items() , response_xml ) , 
                  ( headers_data.items() , self.ms_response_data ) ,
                ] 
           
            content_type = "multipart/%s; boundary=%s"%(subtype,boundary) 

            return Response(mpPack(parts,boundary),content_type,{},self.getStatus())
 
        else : # pure XML response - currently not in use - possibly harmfull as there is no way to test it!  

            if headers_xml is None: headers_xml = self.headers

            return Response(response_xml,self.content_type,headcap(headers_xml),self.getStatus()) 

    def getContentType(self):
        """
        Returns the content type of the response.
        """
        if "Content-type" in self.headers: #MP: Is the 'Content-type' case correct?
            return self.headers["Content-type"]
        else:
            return self.content_type # TODO: headers for multipart messages
        
    def getStatus(self):
        """
        Returns the HTTP status code of the response.
        """
        if self.status is None:
            if self.ms_status is not None and self.ms_status == 0:
                return 200
            else:
                return 400
        else:
            return self.status

class MapServerLayerGeneratorInterface(RegisteredInterface):
    """
    This interface is not in use.
    """
    REGISTRY_CONF = {
        "name": "MapServer Layer Generator Interface",
        "intf_id": "services.mapserver.MapServerLayerGeneratorInterface",
        "binding_method": "kvp",
        "registry_keys": (
            "services.mapserver.service",
            "services.mapserver.version",
            "services.mapserver.eo_object_type",
        )
    }
    
    configure = Method(
        ObjectArg("ms_req", arg_class=MapServerRequest),
        ObjectArg("eo_object"),
        returns=ObjectArg("@return", arg_class=mapscript.layerObj)
    )

class MapServerDataConnectorInterface(RegisteredInterface):
    """
    This interface is intended for objects that configure the input data for
    a MapServer layer. The basic rationale for this is that there are at
    least three different types of data sources that need differentt
    treatment:
    
    * data stored in single plain files
    * tiled data with references in a tile index (a shape file)
    * rasdaman arrays
    
    Others might be added in the course of development of EOxServer.
    
    .. method:: congigure(layer, eo_object)
    
        This method takes a :class:`mapscript.layerObj` object and an ``eo_object``
        as input and configures the MapServer layer according to the type of
        data package used by the ``eo_object`` (RectifiedDataset,
        ReferenceableDataset or RectifiedStitchedMosaic).
    """
    REGISTRY_CONF = {
        "name": "MapServer Data Connector Interface",
        "intf_id": "services.mapserver.MapServerDataConnectorInterface",
        "binding_method": "kvp",
        "registry_keys": (
            "services.mapserver.data_structure_type",
        )
    }
    
    configure = Method(
        ObjectArg("layer", arg_class=mapscript.layerObj),
        ObjectArg("eo_object"),
        ListArg("filter_exprs", default=None),
        returns=ObjectArg("@return", arg_class=mapscript.layerObj)
    )
        
class MapServerOperationHandler(BaseRequestHandler):
    """
    MapServerOperationHandler serves as parent class for all operations
    involving calls to MapServer. It is not an abstract class, but implements
    the most basic functionality, i.e. simply passing on a request to
    MapServer as it comes in.

    This class implements a workflow for request handling that
    involves calls to MapServer using its Python binding (mapscript).
    Requests are processed in six steps:
    
    * retrieve coverage information (:meth:`createCoverages` method)
    * configure a MapServer ``OWSRequest`` object with
      parameters from the request (:meth:`configureRequest` method)
    * configure a MapServer ``mapObj`` object with
      parameters from the request and the config
      (:meth:`configureMapObj` method)
    * add layers to the MapServer ``mapObj`` (:meth:`addLayers` method)
    * dispatch the request, i.e. let MapServer actually do its
      work; return the result (:meth:`dispatch` method)
    * postprocess the MapServer response (:meth:`postprocess` method)
    
    Child classes may override the configureRequest, configureMap,
    postprocess and postprocessFault methods in order to customize
    functionality. If possible, the handle and dispatch methods should
    not be overridden.
    """
    
    PARAM_SCHEMA = {
        "service": {"xml_location": "/@service", "xml_type": "string", "kvp_key": "service", "kvp_type": "string"},
        "version": {"xml_location": "/@version", "xml_type": "string", "kvp_key": "version", "kvp_type": "string"},
        "operation": {"xml_location": "/", "xml_type": "localName", "kvp_key": "request", "kvp_type": "string"}
    }
    
    def __init__(self):
        super(MapServerOperationHandler, self).__init__()
        
        self.req = None
        self.map = mapscript.mapObj(os.path.join(settings.PROJECT_DIR, "conf", "template.map"))
        self.ows_req = mapscript.OWSRequest()
        
        self.temp_files = []
    
    def _addTempFile(self, temp_file_path):
        self.temp_files.append(temp_file_path)
            
    def _setParameter(self, key, value):
        self.ows_req.setParameter(key, value)

    def _addParameter(self, key, value):
        self.ows_req.addParameter(key, value)

    def configureRequest(self):
        """
        This method configures the ``ms_req.ows_req`` object (an
        instance of ``mapscript.OWSRequest``) with the parameters
        passed in with the user request. This method can be overridden
        in order to change the treatment of parameters.
        """
        if self.req.getParamType() == "kvp":
            self.ows_req.type = mapscript.MS_GET_REQUEST
            for key, values in self.req.getParams().items():
                if len(values) == 1:
                    self._setParameter(key.lower(), escape(values[0]))
                else:
                    c = 0 
                    for value in values:
                        # addParameter() available in MapServer >= 6.2 
                        # https://github.com/mapserver/mapserver/issues/3973
                        try:
                            self._addParameter(key.lower(), escape(value))
                        # Workaround for MapServer 6.0
                        except AttributeError:
                            if c == 0: 
                                new_key = key.lower()
                            else: 
                                new_key = "%s_%d" % (key.lower(), c) 
                            self._setParameter(new_key, escape(value)) 
                            c += 1 
                            while "%s_%d" % (key.lower(), c) in self.req.getParams(): 
                                c += 1 

            self._setParameter("version", self.req.getVersion())
        elif self.req.getParamType() == "xml":
            self.ows_req.type = mapscript.MS_POST_REQUEST
            self.ows_req.postrequest = self.req.getParams()
        else:
            raise Exception("Unknown parameter type '%s'." % self.req.getParamType())

    def dispatch(self):
        """
        This method actually executes the MapServer request by calling
        ``ms_req.map.OWSDispatch()``. This method should not be
        overridden by child classes.
        """
        
        logger.debug("MapServer: Installing stdout to buffer.")
        mapscript.msIO_installStdoutToBuffer()
        
        try:
            logger.debug("MapServer: Dispatching.")
            ts = time.time()
            # Execute the OWS request by mapserver, obtain the status in 
            # dispatch_status (0 is OK)
            dispatch_status = self.map.OWSDispatch(self.ows_req)
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
            complete_result = mapscript.msIO_getStdoutBufferBytes()
            parts = complete_result.split("\r\n")
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
        
        return MapServerResponse(result, content_type, dispatch_status)

    def cleanup(self):
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                logger.warning("Could not remove temporary file '%s'" % temp_file)

def gdalconst_to_imagemode(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a MapScript image mode constant.
    """
    if const == GDT_Byte:
        return mapscript.MS_IMAGEMODE_BYTE
    elif const == GDT_Int16 or const == GDT_UInt16:
        return mapscript.MS_IMAGEMODE_INT16
    elif const == GDT_Float32:
        return mapscript.MS_IMAGEMODE_FLOAT32
    else:
        raise InternalError("MapServer is not capable to process the datatype %d" % const)

def gdalconst_to_imagemode_string(const):
    """
    This function translates a GDAL data type constant as defined in the
    :mod:`gdalconst` module to a string as used in the MapServer map file
    to denote an image mode.
    """
    if const == GDT_Byte:
        return "BYTE"
    elif const == GDT_Int16 or const == GDT_UInt16:
        return "INT16"
    elif const == GDT_Float32:
        return "FLOAT32"
    
