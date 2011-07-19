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

"""
This module contains the abstract base classes for request handling.
"""

from django.conf import settings

import logging
import os.path
from cgi import escape

from eoxserver.lib.requests import EOxSMapServerRequest, EOxSResponse, EOxSMapServerResponse
from eoxserver.lib.domainset import EOxSTrim, EOxSSlice
from eoxserver.lib.util import DOMElementToXML, EOxSXMLEncoder
from eoxserver.lib.exceptions import (
    EOxSInvalidRequestException, EOxSVersionNegotiationException,
    EOxSInternalError
)

from eoxserver.contrib import mapscript

class EOxSRequestHandler(object):
    """
    Abstract base class for all EOxServer Handlers.
    """
    def __init__(self, config):
        super(EOxSRequestHandler, self).__init__()
        self.config = config
    
    def _handleException(self, req, exception):
        """
        Abstract method which must be overridden by child classes to
        provide specific exception reports. If the exception report
        cannot be generated in this specific handler, the exception
        should be re-raised. This is also the default behaviour.
        
        @param  req     The {@link eoxserver.lib.requests.EOxSOWSRequest}
                        object that was being processed when the
                        exception was raised
        @param  exception The <tt>Exception</tt> raised by the request
                        handling method
        @return         An {@link eoxserver.lib.requests.EOxSResponse}
                        object containing an exception report
        """
        raise
    
    def _processRequest(self, req):
        """
        Abstract method which must be overridden to provide the specific
        request handling logic. Should not be invoked from external code,
        use the {@link #handle handle} method instead.
        
        @param  req An {@link eoxserver.lib.requests.EOxSOWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.lib.requests.EOxSResponse} object
                    containing the response content, headers and status
        """
        pass

    def handle(self, req):
        """
        Basic request handling method which should be invoked from
        external code.
        
        @param  req An {@link eoxserver.lib.requests.EOxSOWSRequest} object
                    containing the request parameters
        
        @return     An {@link eoxserver.lib.requests.EOxSResponse} object
                    containing the response content, headers and status
        """

        try:
            return self._processRequest(req)
        except Exception, e:
            return self._handleException(req, e)

class EOxSServiceHandler(EOxSRequestHandler):
    """
    Abstract base class for EOxServer Service Handlers.
    
    This class and its subclasses have two class variables that
    determine which requests the class will handle:<br/>
    
    <ul>
    <li><b>SERVICE:</b> Name of the service to be handled</li>
    <li><b>ABSTRACT:</b> A boolean indicating whether this is an abstract base class or a concrete instantiation</li>
    </ul>
    """
    
    SERVICE = ""
    ABSTRACT = True

class EOxSVersionHandler(EOxSRequestHandler):
    """
    Abstract base class for EOxServer Version Handlers.
    
    This class and its subclasses have two class variables that
    determine which requests the class will handle:<br/>
    
    <ul>
    <li><b>SERVICE:</b> Name of the service to be handled</li>
    <li><b>VERSIONS:</b> A tuple of version strings supported by this handler</li>
    <li><b>ABSTRACT:</b> A boolean indicating whether this is an abstract base class or a concrete instantiation</li>
    </ul>
    """
    
    SERVICE = ""
    VERSIONS = ()
    ABSTRACT = True

class EOxSOperationHandler(EOxSRequestHandler):
    """
    Abstract base class for EOxServer Operation Handlers.
    
    This class and its subclasses have four class variables that
    determine which requests the class will handle:<br/>
    
    <ul>
    <li><b>SERVICE:</b> Name of the service to be handled</li>
    <li><b>VERSIONS:</b> A tuple of version strings supported by this handler</li>
    <li><b>OPERATIONS:</b> A tuple of lower case operation names supported by this handler</li>
    <li><b>ABSTRACT:</b> A boolean indicating whether this is an abstract base class or a concrete instantiation</li>
    </ul>
    """
    
    SERVICE = ""
    VERSIONS = ()
    OPERATIONS = ()
    ABSTRACT = True
        
class EOxSMapServerOperationHandler(EOxSOperationHandler):
    """\
    EOxSMapServerOperationHandler serves as parent class for all operations
    involving calls to MapServer. It is not an abstract class, but implements
    the most basic functionality, i.e. simply passing on a request to
    MapServer as it comes in.


    This class implements a workflow for request handling that
    involves calls to MapServer using its Python binding (mapscript).
    Requests are processed in six steps:
    
    <ol>
    <li>retrieve coverage information ({@link #createCoverages} method)</li>
    <li>configure a MapServer <tt>OWSRequest</tt> object with
        parameters from the request ({@link #configureRequest}
        method)</li>
    <li>configure a MapServer <tt>mapObj</tt> object with
        parameters from the request and the config
        ({@link #configureMapObj} method)</li>
    <li>add layers to the MapServer <tt>mapObj</tt>
        ({@link #addLayers} method)</li>
    <li>dispatch the request, i.e. let MapServer actually do its
        work; return the result ({@link dispatch} method)</li>
    <li>postprocess the MapServer response ({@link postprocess}
        method)</li>
    </ol>
    
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
    
    def _processRequest(self, req):
        """
        This method implements the workflow described in the class
        documentation.
        
        First it creates a EOxSMapServerRequest object and passes the
        request data to it. Then it invokes the methods in the order
        defined above and finally returns an {@link eoxserver.lib.requests.EOxSMapServerResponse}
        object. It is not recommended to override this method.
        
        @param  req An {@link eoxserver.lib.requests.EOxSOWSRequest}
                    object containing the request parameters and data
        
        @return     An {@link eoxserver.lib.requests.EOxSMapServerResponse}
                    object containing the response content, headers and
                    status as well as the status code returned by
                    MapServer
        """
        ms_req = EOxSMapServerRequest(req)
        ms_req.setSchema(self.PARAM_SCHEMA)
        self.createCoverages(ms_req)
        self.configureRequest(ms_req)
        self.configureMapObj(ms_req)
        self.addLayers(ms_req)
        response = self.dispatch(ms_req)
        return self.postprocess(ms_req, response)
    
    def createCoverages(self, ms_req):
        """
        This method creates coverages, i.e. it adds coverage objects to
        the <tt>ms_req.coverages</tt> list. The default implementation
        does nothing at all, so you will have to override this method to
        meet your needs. 
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest} object
        
        @return         None
        """
        pass
    
    def _setParameter(self, ms_req, key, value):
        ms_req.ows_req.setParameter(key, value)

    def configureRequest(self, ms_req):
        """
        This method configures the <tt>ms_req.ows_req</tt> object (an
        instance of <tt>mapscript.OWSRequest</tt>) with the parameters
        passed in with the user request. This method can be overridden
        in order to change the treatment of parameters.
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest} object
        
        @return         None
        """
        
        ms_req.ows_req = mapscript.OWSRequest()
        if ms_req.getParamType() == "kvp":
            for key, values in ms_req.getParams().items():
                if len(values) == 1:
                    self._setParameter(ms_req, key.lower(), escape(values[0]))
                else:
                    c = 0
                    for value in values: # TODO: hack: append "_<index>" to equally named KVP keys
                        if c == 0:
                            new_key = key
                        else:
                            new_key = "%s_%d" % (key.lower(), c)
                        self._setParameter(ms_req, new_key, escape(value))
                        
                        c += 1
                        while "%s_%d" % (key.lower(), c) in ms_req.getParams():
                            c += 1

            self._setParameter(ms_req, "version", ms_req.getVersion())
        elif ms_req.getParamType() == "xml":
            ms_req.ows_req.type = mapscript.MS_POST_REQUEST
            ms_req.ows_req.postrequest = ms_req.getParams()
        else:
            raise Exception("Unknown parameter type '%s'." % ms_req.getParamType())

    def configureMapObj(self, ms_req):
        """
        This method configures the <tt>ms_req.map</tt> object (an
        instance of <tt>mapscript.mapObj</tt>) with parameters from the
        config. This method can be overridden in order to implement more
        sophisticated behaviour. 
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest} object
        
        @return         None
        """
        ms_req.map = mapscript.mapObj(os.path.join(settings.PROJECT_DIR, "conf", "template.map")) # TODO: Store information in database??? (title, abstract, etc.)
        #ms_req.map.loadOWSParameters(ms_req.ows_req)
        
        ms_req.map.setMetaData("ows_onlineresource", self.config.http_service_url + "?")
        ms_req.map.setMetaData("wcs_label", "EOxServer WCS") # TODO: to WCS
        
        ms_req.map.setProjection("+init=epsg:4326") #TODO: Set correct projection!

        #ms_req.map.debug = 5
        #ms_req.map.setConfigOption("MS_ERRORFILE", "stderr")
        
    def addLayers(self, ms_req):
        """
        This method adds layers to the <tt>ms_req.map</tt> object based
        on the coverages defined in <tt>ms_req.coverages</tt>. The
        default is to unconditionally add a single layer for each
        coverage defined. This method can be overridden in order to
        customize the way layers are inserted into the map object.
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest} object
        
        @return         None
        """
        for coverage in ms_req.coverages:
            ms_req.map.insertLayer(self.getMapServerLayer(coverage))
    
    def getMapServerLayer(self, coverage, **kwargs):
        """
        This method is invoked by the {@link #addLayers} method in order
        to generate <tt>mapscript.layerObj</tt> instances for each
        coverage. The basic configuration is done here, but subclasses
        will have to override this method in order to define e.g. the
        data sources for the layer.
        
        @param  coverage    An {@link eoxserver.lib.interfaces.EOxSCoverageInterface}
                            object giving access to the coverage data
        
        @return             A <tt>mapscribt.layerObj</tt> object
                            representing the layer to be inserted
        """
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON
        #layer.debug = 5

        layer.setProjection("+init=epsg:%d" % int(coverage.getGrid().srid))

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)

        return layer


    def dispatch(self, ms_req):
        """
        This method actually executes the MapServer request by calling
        <tt>ms_req.map.OWSDispatch()</tt>. This method should not be
        overridden by child classes.
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest}
                        object
        
        @return         An {@link eoxserver.lib.requests.EOxSMapServerResponse}
                        object containing the content, headers and status
                        of the request as well as the status code
                        returned by MapServer
        """
        logging.debug("EOxSMapServerOperationHandler.dispatch: 1")
        mapscript.msIO_installStdoutToBuffer()
        # Execute the OWS request by mapserver, obtain the status in dispatch_status (==0 is OK)
        logging.debug("EOxSMapServerOperationHandler.dispatch: 2")
        dispatch_status = ms_req.map.OWSDispatch(ms_req.ows_req)
        
        logging.debug("EOxSMapServerOperationHandler.dispatch: 3")
        content_type = mapscript.msIO_stripStdoutBufferContentType()
        mapscript.msIO_stripStdoutBufferContentHeaders()
        logging.debug("EOxSMapServerOperationHandler.dispatch: 4")
        result = mapscript.msIO_getStdoutBufferBytes()
        logging.debug("EOxSMapServerOperationHandler.dispatch: 5")
        mapscript.msCleanup()
        
        return EOxSMapServerResponse(result, content_type, dispatch_status)
        
    def postprocess(self, ms_req, resp):
        """
        This method operates on the MapServer response. The default
        behaviour is to do nothing at all, i.e. return the input
        response unchanged. If postprocessing is needed, you should
        override this method. 
        
        @param  ms_req  An {@link eoxserver.lib.requests.EOxSMapServerRequest}
                        object
        @param  resp    An {@link eoxserver.lib.requests.EOxSMapServerResponse}
                        object.
        """
        return resp
        
    def postprocessFault(self, ms_req, resp):
        return resp

class EOxSExceptionHandler(object):
    def _filterExceptions(self, exception):
        raise
    
    def _getEncoder(self):
        raise EOxSInternalError("Not implemented.")
    
    def _getExceptionReport(self, req, exception, encoder):
        if isinstance(exception, EOxSVersionNegotiationException):
            return DOMElementToXML(encoder.encodeVersionNegotiationException(exception))
        elif isinstance(exception, EOxSInvalidRequestException):
            return DOMElementToXML(encoder.encodeInvalidRequestException(exception))
        
    def _getHTTPStatus(self, exception):
        return 400
        
    def _logError(self, req, exception):
        logging.error(str(req.getParams()))
        logging.error(str(exception))
        
    def _getContentType(self, exception):
        raise EOxSInternalError("Not implemented.")
    
    def handleException(self, req, exception):
        self._filterExceptions(exception)
        
        encoder = self._getEncoder()
        
        content = self._getExceptionReport(req, exception, encoder)
        status = self._getHTTPStatus(exception)
        
        self._logError(req, exception)
        
        return EOxSResponse(
            content = content,
            content_type = self._getContentType(exception),
            headers = {},
            status = status
        )

class EOxSExceptionEncoder(EOxSXMLEncoder):
    def encodeInvalidRequestException(self, exception):
        pass
    
    def encodeVersionNegotiationException(self, exception):
        pass
