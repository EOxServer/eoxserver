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

import mapscript

import logging 
import datetime

from urllib import unquote

from eoxserver.services.owscommon import OWSCommonConfigReader
from eoxserver.services.mapserver import (
    MapServerOperationHandler, gdalconst_to_imagemode
)
from eoxserver.services.exceptions import InvalidRequestException

from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss

class WCSCommonHandler(MapServerOperationHandler):
    def __init__(self):
        super(WCSCommonHandler, self).__init__()
        
        self.coverages = []
        
    def _processRequest(self, req):
        """
        This method implements the workflow described in the class
        documentation.
        
        First it creates a :class:``MapServerRequest`` object and passes the
        request data to it. Then it invokes the methods in the order
        defined above and finally returns an :class:`MapServerResponse`
        object. It is not recommended to override this method.
        
        @param  req An :class:`~.OWSRequest`
                    object containing the request parameters and data
        
        @return     An :class:`MapServerResponse`
                    object containing the response content, headers and
                    status as well as the status code returned by
                    MapServer
        """
        self.req = req
        self.req.setSchema(self.PARAM_SCHEMA)

        try:
            self.validateParams()
            self.createCoverages()
            self.configureRequest()
            self.configureMapObj()
            self.addLayers()
            response = self.postprocess(self.dispatch())
        finally:
            self.cleanup()
        
        return response
    
    def validateParams(self):
        pass
    
    def createCoverages(self):
        """
        This method creates coverages, i.e. it adds coverage objects to
        the ``ms_req.coverages`` list. The default implementation
        does nothing at all, so you will have to override this method to
        meet your needs. 
        
        @param  ms_req  An :class:`MapServerRequest` object
        
        @return         None
        """
        pass

    def configureMapObj(self):
        """
        This method configures the ``ms_req.map`` object (an
        instance of ``mapscript.mapObj``) with parameters from the
        config. This method can be overridden in order to implement more
        sophisticated behaviour. 
        
        @param  ms_req  An :class:`MapServerRequest` object
        
        @return         None
        """
        
        self.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        self.map.setMetaData("wcs_label", "EOxServer WCS")
        
        self.map.setProjection("+init=epsg:4326") #TODO: Set correct projection!
        
    def addLayers(self):
        """
        This method adds layers to the ``ms_req.map`` object based
        on the coverages defined in ``ms_req.coverages``. The
        default is to unconditionally add a single layer for each
        coverage defined. This method can be overridden in order to
        customize the way layers are inserted into the map object.
        
        @param  ms_req  An :class:`MapServerRequest` object
        
        @return         None
        """
        for coverage in self.coverages:
            self.map.insertLayer(self.getMapServerLayer(coverage))

    def getMapServerLayer(self, coverage):
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON

        # TODO: check me / fix me 
#        if coverage.getType() != "eo.ref_dataset":
#            layer.setProjection("+init=epsg:%d" % int(coverage.getSRID()))
#            layer.setMetaData("ows_srs", "EPSG:%d" % int(coverage.getSRID()))

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)

        extent = coverage.getExtent()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10f %.10f %.10f %.10f" % extent)
        layer.setMetaData("wcs_resolution", "%.10f %.10f" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent())
        
        return layer

    def postprocess(self, resp):
        return resp

def getMSOutputFormatsAll( coverage = None ) : 
    """ Setup all the supported MapServer output formats.
        When the coverage parameter is provided than the 
        range type is used to setup format's image mode.""" 

    # set image mode 
    if coverage is not None : 
        # set image mode based on the coverage's range type 
        im = gdalconst_to_imagemode( coverage.getRangeType().data_type ) 
    else : 
        # default 
        im = None 

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get the supported formats 
    sfs = FormatRegistry.getSupportedFormatsWCS() 

    #prepare list of output formats 
    ofs = [] 

    for sf in sfs : 
    
        # output format definition 
        of = mapscript.outputFormatObj( sf.driver, "custom" )
        of.name      = sf.mimeType 
        of.mimetype  = sf.mimeType 
        of.extension = sf.defaultExt 
        if im is not None : 
            of.imagemode = im 

        ofs.append( of ) 

    return ofs 

def getWCSNativeFormat( source_mime ): 

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry()

    # get the coverage's source format 
    source_format = FormatRegistry.getFormatByMIME( source_mime )

    # map the source format to the native one 
    native_format = FormatRegistry.mapSourceToNativeWCS20( source_format )

    #return native format mime 
    return native_format 


def getMSWCSNativeFormat( source_mime ): 
    return getWCSNativeFormat( source_mime ).mimeType


def getMSWCSSRSMD(): 
    """ get the space separated list of CRS EPSG codes to be passed 
        to MapScript setMedata("wcs_srs",...) method """

    return " ".join( crss.getSupportedCRS_WCS(None,crss.asShortCode) ) 

def getMSWCSFormatMD():
    """ get the space separated list of supported formats to be passed 
        to MapScript setMedata("wcs_formats",...) method """

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get format record  
    frm = FormatRegistry.getSupportedFormatsWCS() 

    return " ".join( map( lambda f : f.mimeType , frm ) )  


def getMSOutputFormat(format_param, coverage):

    #split MIME type to base MIME and format specific options 
    mime_type, format_options = parse_format_param(format_param)

    # get coverage range type 
    rangetype = coverage.getRangeType()

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get format record  
    frm = FormatRegistry.getFormatByMIME( mime_type ) 

    if ( frm not in FormatRegistry.getSupportedFormatsWCS() ) : 
        sf = map( lambda f : f.mimeType , FormatRegistry.getSupportedFormatsWCS() )
        raise InvalidRequestException(
            "Unsupported format '%s'. Known formats: %s" % ( mime_type, ", ".join(sf) ) ,
            "InvalidParameterValue", "format" )

    # check the driver
    if frm.driver.partition("/")[0] != "GDAL" : 
        raise InternalError( "Unsupported format backend \"%s\"!" % frm.driver.partition("/")[0] ) 

    # output format definition 
    output_format = mapscript.outputFormatObj( frm.driver, "custom" )
    output_format.mimetype  = frm.mimeType 
    output_format.extension = frm.defaultExt
    output_format.imagemode = gdalconst_to_imagemode( rangetype.data_type )

    # format specific options 
    for fo in format_options:
        key, value = map( lambda s : str(s.strip()) , fo.split("=") ) 
        output_format.setOption( key, value )
    
    # set the response filename 

    time_stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    filename   = "%s_%s%s" % ( coverage.getCoverageId(), time_stamp, frm.defaultExt ) 

    output_format.setOption( "FILENAME", str(filename) )

    return output_format


def parse_format_param(format_param):

    parts = unquote(format_param).split(";")
    
    mime_type = parts[0]
    
    format_options = parts[1:]

    return (mime_type, format_options)
