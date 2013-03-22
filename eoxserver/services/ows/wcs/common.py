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
This module contains handlers and functions commonly used by the different WCS
version implementations.
"""

import datetime
from urllib import unquote

import mapscript

from eoxserver.core.exceptions import InternalError

from eoxserver.services.owscommon import OWSCommonConfigReader
from eoxserver.services.mapserver import (
    MapServerOperationHandler, gdalconst_to_imagemode
)
from eoxserver.services.exceptions import InvalidRequestException

from eoxserver.resources.coverages.formats import getFormatRegistry
from eoxserver.resources.coverages import crss

_stripDot = lambda s : s[1:] if s[0] == '.' else s 

class WCSCommonHandler(MapServerOperationHandler):
    """
    This class provides the common operation handler for handling WCS
    operation requests using MapServer. It inherits from
    :class:`~.MapServerOperationHandler`.
    
    The class implements a handling chain:
    
    * first, the request parameters are validated using :meth:`validateParams`
    * then, the coverage(s) the request relates to are retrieved using
      :meth:`createCoverages`
    * then, the :class:`mapscript.OWSRequest` and :class:`mapscript.mapObj`
      instances are configured using :meth:`configureRequest` and
      :meth:`configureMapObj`
    * then the layers are added using :meth:`addLayers`
    * then the request is carried out by MapServer using :meth:`dispatch`
    * finally, postprocessing steps on the response retrieved from MapServer
      can be performed using :meth:`postprocess`
    """
    def __init__(self):
        super(WCSCommonHandler, self).__init__()
        
        self.coverages = []
        
    def _processRequest(self, req):
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
        """
        This method is intended to validate the parameters. It has to be
        overridden by child classes.
        """
        pass
    
    def createCoverages(self):
        """
        This method creates coverages, i.e. it adds coverage objects to
        the ``coverages`` list of the handler. It has to be overridden by
        child classes.
        """
        pass

    def configureMapObj(self):
        """
        This method configures the ``map`` property of the handler (an
        instance of :class:`mapscript.mapObj`) with parameters from the
        config. This method can be overridden in order to implement more
        sophisticated behaviour.
        """
        
        self.map.setMetaData("ows_onlineresource", OWSCommonConfigReader().getHTTPServiceURL() + "?")
        self.map.setMetaData("wcs_label", "EOxServer WCS")
        
    def addLayers(self):
        """
        This method adds layers to the :class:`mapscript.mapObj` stored by the
        handler. By default it inserts a layer for every coverage. The layers
        are retrieved by calls to :meth:`getMapServerLayer`.
        """
        for coverage in self.coverages:
            self.map.insertLayer(self.getMapServerLayer(coverage))

    def getMapServerLayer(self, coverage):
        """
        This method creates and returns a :class:`mapscript.layerObj` instance
        and configures it according to the metadata stored in the ``coverage``
        object.
        """
        layer = mapscript.layerObj()
        
        layer.name = coverage.getCoverageId()
        layer.setMetaData("ows_title", coverage.getCoverageId())
        layer.status = mapscript.MS_ON

        for key, value in coverage.getLayerMetadata():
            layer.setMetaData(key, value)

        extent = coverage.getExtent()
        size = coverage.getSize()
        rangetype = coverage.getRangeType()
        resolution = ((extent[2]-extent[0]) / float(size[0]),
                      (extent[1]-extent[3]) / float(size[1]))
        
        layer.setMetaData("wcs_extent", "%.10g %.10g %.10g %.10g" % extent)
        layer.setMetaData("wcs_resolution", "%.10g %.10g" % resolution)
        layer.setMetaData("wcs_size", "%d %d" % size)
        
        layer.type = mapscript.MS_LAYER_RASTER
        layer.dump = mapscript.MS_TRUE
        layer.setConnectionType(mapscript.MS_RASTER, '')
        
        layer.setMetaData("wcs_label", coverage.getCoverageId())
        
        layer.setExtent(*coverage.getExtent())
        
        return layer

    def postprocess(self, resp):
        """
        This method postprocesses a :class:`~.MapServerResponse` object
        ``resp``. By default the response is returned unchanged. The method
        can be overridden by child classes.
        """
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
        of.extension = _stripDot( sf.defaultExt ) 
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

def getMSWCS10NativeFormat( source_mime ): 
    return getWCSNativeFormat( source_mime ).wcs10name 

def getMSWCSSRSMD(): 
    """ get the space separated list of CRS EPSG codes to be passed 
        to MapScript setMedata("wcs_srs",...) method """
    return " ".join(crss.getSupportedCRS_WCS(format_function=crss.asShortCode)) 

def getMSWCSFormatMD():
    """ get the space separated list of supported formats to be passed 
        to MapScript setMedata("wcs_formats",...) method """

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get format record  
    frm = FormatRegistry.getSupportedFormatsWCS() 

    return " ".join( map( lambda f : f.mimeType , frm ) )  

def getMSWCS10FormatMD():
    """ get the space separated list of supported formats to be passed 
        to MapScript setMedata("wcs_formats",...) method """

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get format record  
    frm = FormatRegistry.getSupportedFormatsWCS() 

    return " ".join( map( lambda f : f.wcs10name , frm ) )  

def getMSOutputFormat(format_param, coverage):

    #split MIME type to base MIME and format specific options 
    mime_type, format_options = parse_format_param(format_param)

    # get coverage range type 
    rangetype = coverage.getRangeType()

    # retrieve the format registry 
    FormatRegistry = getFormatRegistry() 

    # get format record  
    frm = FormatRegistry.getFormatByMIME( mime_type ) 

    # check also WCS 1.0 name (this time 'mime_type' is not really a MIME-type)
    if frm is None : 
        frms = FormatRegistry.getFormatsByWCS10Name( mime_type ) 
        frm = frms[0] if len( frms ) > 0 else None  

    # check that the format is among the supported formats 
    if ( frm not in FormatRegistry.getSupportedFormatsWCS() ) : 
        sf = map( lambda f : f.mimeType , FormatRegistry.getSupportedFormatsWCS() )
        raise InvalidRequestException(
            "Unsupported format '%s'!" % ( mime_type ) ,
            "InvalidParameterValue", "format" )

    # check the driver
    if frm.driver.partition("/")[0] != "GDAL" : 
        raise InternalError( "Unsupported format backend \"%s\"!" % frm.driver.partition("/")[0] ) 

    # output format definition 
    output_format = mapscript.outputFormatObj( frm.driver, "custom" )
    output_format.mimetype  = frm.mimeType 
    output_format.extension = _stripDot( frm.defaultExt ) 
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
    """
    This utility function is used to parse a MIME type expression
    ``format_param`` into its parts. It returns a tuple
    ``(mime_type, format_options)`` which contains the mime type as a string
    as well as a list of format options. The input is expected as a MIME type
    like string of the form::
    
      <type>/<subtype>[;<format_option_key>=<format_option_value>[;...]]
    
    This is used for an EOxServer specific extension of the WCS format parameter
    which allows to tag additional format creation options such as compression
    and others to format expressions, e.g.::
    
      image/tiff;compression=LZW
    """
    parts = unquote(format_param).split(";")
    
    mime_type = parts[0]
    
    format_options = parts[1:]

    return (mime_type, format_options)
