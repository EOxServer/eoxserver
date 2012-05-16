#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
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
 This module contains format handling utilities.
"""
#-------------------------------------------------------------------------------

import re
import sys 
import imp
import logging
import os.path 

try:     from osgeo import gdal
except ImportError: import gdal

from django.conf import settings
from eoxserver.core.system import System
from eoxserver.core.exceptions import InternalError
from eoxserver.core.startup import StartupHandlerInterface

#-------------------------------------------------------------------------------

class FormatRecord(object) : 

    """ 
    Single format record specification 
    """  

    def __init__( self , gdal_driver , mime_type , extension , is_writeable ) :  

        self.mimeType    = mime_type 
        self.gdalDriver  = gdal_driver 
        self.defautExt   = extension 
        self.isWriteable = is_writeable  

    def __str__( self ) : 

        return "%s,%s,%s #%s"%(self.gdalDriver,self.mimeType,self.defautExt,["ro","rw"][bool(self.isWriteable)],) 

#-------------------------------------------------------------------------------

class FormatRegistry(object):
    """
    The :class:`FormatRegistry` class represents cofiguration of file supported
    formats and of the auxiliary methods. The formats' configuration relies 
    on two configuration files:
    
    * the default formats' configuration (``eoxserver/conf/default_formats.conf``)
    * the optional instance configuration (``conf/format.conf`` in the instance
      directory)
    
    Configuration values are read from these files.
    """

    #---------------------------------------------------------------------------

    def __init__( self , config ):
 
        # get path to EOxServer installation 
        path_eoxs = self.__get_path_eoxs()

        # default formats' configuration 
        path_formats_def = os.path.join( path_eoxs, "conf", "default_formats.conf" ) 

        if not os.path.exists( path_formats_def ) :

            # try alternative location 
            path_formats_def = os.path.join( sys.prefix, "eox_server", "conf", "default_formats.conf" ) 

            if not os.path.exists( path_formats_def ) :

                # failed to read the file 
                raise InternalError("Cannot find the default file formats' configuration file.")

        # optional formats' configuration 
        path_formats_opt = os.path.join( settings.PROJECT_DIR, "conf", "formats.conf" ) 

        if not os.path.exists( path_formats_opt ) :
            path_formats_opt = None # no user defined formats' configuration 
            logging.info( "Optional, user-defined file formats' specification not found. Only the installation defaults will be used.") 

        # load the formats' configuaration 
        self.__load_formats( path_formats_def , path_formats_opt )

        # parse the config options 
        self.__parse_config( config )

    #---------------------------------------------------------------------------
    # getters 

    def getFormatsAll( self ) :  
        """ Get list of all registered formats """ 

        return self.__gdal2format.values() 


    def getFormatByDriver( self , gdal_driver_name ) :  
        """ Get format record for the given gdal driver name. Incase of no match 'None' value is returned. """ 

        return self.__gdal2format.get( valGdalDriver( dal_driver_name ) ) 


    def getFormatByMIME( self , mime_type ) :  
        """ Get format record for the given MIME type. Incase of no match 'None' value is returned. """ 

        return self.__mime2format.get( valMimeType( mime_type ) ) 

    #---------------------------------------------------------------------------
    # OWS specific getters 

    def getSupportedFormatsWCS( self ) :  
        """ 
            Get list of formats to be announced as supported WCS formats.

            The the listed formats must be:
            * defined in EOxServers configuration (section "services.ows.wcs", item "supported_formats") 
            * defined in the formats' configuration ("default_formats.conf" or "formats.conf")   
            * supported by the used GDAL installation 
        """ 
        return self.__wcs_supported_formats 

    def getSupportedFormatsWMS( self ) :  
        """ 
            Get list of formats to be announced as supported WMS formats.

            The the listed formats must be:
            * defined in EOxServers configuration (section "services.ows.wms", item "supported_formats") 
            * defined in the formats' configuration ("default_formats.conf" or "formats.conf")   
            * supported by the used GDAL installation 
        """ 
        return self.__wms_supported_formats 

    def mapSourceToNativeWCS20( self , format ) :  
        """ Map source format to WCS 2.0 native format. 

        Both the input and output shall be instances of :class:`FormatRecords` class. 
        The input format can be obtained, e.g., by the `getFormatByDriver` or `getFormatByMIME` 
        method.

        The format mapping follows these rules: 
        1. Mapping based on the explicite rules is applied if possible (defined in EOxServers
           configuration, section "services.ows.wcs20", item "source_to_native_format_map").
           If there is no mapping available the source format is kept. 
        2. If the format resulting from step 1 is not a writable GDAL format or 
           it is not among the supported WCS formats than it is 
           replaced by the default native format (defined in EOxServers
           configuration, section "services.ows.wcs20", item "default_native_format"). 
           In case of writable GDAL format, the result of step 1 is returned. 
        """

        # 1. apply mapping 
        format =  self.__wcs20_format_mapping.get( format , format ) 

        # 2. fallback to default 
        if ( format is None ) or ( not format.isWriteable ) \
          or ( format not in self.getSupportedFormatsWCS() ) :   

            format = self.__wcs20_def_native_format 

        return format 

    #---------------------------------------------------------------------------
    # loading of configuration - private auxiliary subroutines 

        # parse the config options 
    def __parse_config( self , config ): 
        """
        Parse the EOxServer configuration. 
        """
        
        #  WMS and WCS suported formats 

        wms = config.getConfigValue("services.ows.wms","supported_formats") 
        wcs = config.getConfigValue("services.ows.wcs","supported_formats") 

        self.__wms_supported_formats = filter( lambda f: f, map( lambda m: self.getFormatByMIME(m.strip()), wms.split(',') ) )
        self.__wcs_supported_formats = filter( lambda f: f, map( lambda m: self.getFormatByMIME(m.strip()), wcs.split(',') ) )

        
        #  WCS 2.0.1 source to native format mapping 
 
        src = config.getConfigValue("services.ows.wcs20","default_native_format").strip() 
        tmp = self.getFormatByMIME( src )

        self.__wcs20_def_native_format = tmp 

        if ( tmp is None ) or ( tmp not in self.getSupportedFormatsWCS() ) : 
            raise ValueError , "Invalid value of configuration option 'services.ows.wcs20' 'default_native_format'! mimeType=\"%s\""% src  


        tmp = config.getConfigValue("services.ows.wcs20","source_to_native_format_map")
        tmp = map( lambda m: self.getFormatByMIME(m.strip()), tmp.split(',') ) 
        tmp = [ (tmp[i],tmp[i+1]) for i in xrange(0,(len(tmp)>>1)<<1,2) ]
        tmp = filter( lambda p: (p[0] is not None ) and ( p[1] is not None ) , tmp ) 

        self.__wcs20_format_mapping = dict( tmp ) 



    def __load_formats( self , path_formats_def , path_formats_opt ):
        """
        Load and parse the formats' configuration. 
        """

        # reset iternall format storage 
        self.__gdal2format = {} 
        self.__mime2format = {} 
            
        # read default configuration 
        logging.info( "Loading formats' configuration from: %s" % path_formats_def ) 
        for ln,line in enumerate( file( path_formats_def ) ) :
            self.__parse_line( line , path_formats_def , ln+1 ) 

        # read the optional configuration 
        if path_formats_opt : 
            logging.info( "Loading formats' configuration from: %s" % path_formats_opt ) 
            for ln,line in enumerate( file( path_formats_opt ) ) :
                self.__parse_line( line , path_formats_opt , ln+1 ) 


    def __parse_line( self , line , fname , lnum ) : 
        """
        Parse single line of configuration.  
        """

        # parse line 
        try : 
  
            line = line.partition( "#" )[0].strip() # strip comments and white characters 

            if 0 == len(line) : return 
        
            ( gdal_driver , mime_type , extension ) = line.split(',')

            gdal_driver = valGdalDriver(gdal_driver.strip()) ; 
            mime_type   = valMimeType(mime_type.strip()) ;
            extension   = extension.strip() ; 

            if None in (gdal_driver,mime_type) : 
                raise ValueError , "Invalid input format specification \"%s\"!" % line  

            # check the GDAL driver 
            driver = gdal.GetDriverByName( gdal_driver ) 
 
            if driver is None : 
                raise ValueError , "Invalid GDAL driver \"%s\"!" % gdal_driver 

            #get the writebility 
            is_writeable = ( driver.GetMetadataItem("DCAP_CREATECOPY") == "YES" ) 

            # new format records 
            frec = FormatRecord( gdal_driver , mime_type , extension , is_writeable )  

            # store format record  
            self.__gdal2format[ gdal_driver ] = frec 
            self.__mime2format[ mime_type ]   = frec 

            logging.info( "Adding new file format: %s" % str( frec ) ) 

        except Exception as e : 

            logging.warning( "%s:%i Invalid file format specification! Line ignored! line=\"%s\" message=\"%s\"" % ( 
                fname , lnum , line , str(e) ) )

    def __get_path_eoxs(self):
        """
        Get path to the EOxServer installation.
        """

        try:
            return imp.find_module("eoxserver")[1]
        except ImportError:
            raise InternalError("Filed to find the 'eoxserver' module! Check your modules' path!")

#-------------------------------------------------------------------------------
# regular expression validators 

__gerexValMime = re.compile("^[-\w]*/[-+\w]*(;[-\w]*=[-\w]*)*$")
__gerexValDriv = re.compile( "^[-\w]*$" ) 

def valMimeType( string ):
    """ 
    MIME type reg.ex. validator. If pattern not matched 'None' is returned 
    otherwise the input is returned.
    """ 
    rv = string if __gerexValMime.match(string) else None 
    if None is rv :  
        logging.warning( "Invalid MIME type \"%s\" ignored." % string ) 
    return rv  

def valGdalDriver( string ):  
    """ 
    GDAL driver dentifier reg.ex. validator. If pattern not matched 'None' is returned 
    otherwise the input is returned.
    """ 
    rv = string if __gerexValDriv.match(string) else None 
    if None is rv :  
        logging.warning( "Invalid GDAL driver identifier \"%s\" ignored." % string ) 
    return rv  

#-------------------------------------------------------------------------------
# 
# EOxServer start-up handler 
#

__FORMAT_REGISTRY = None

class FormatLoaderStartupHandler( object ) : 

    """ 
    This class is the implementation of the :class:`StartupHandlerInterface` 
    responsible for loading and intialization of the format registry.
    """

    REGISTRY_CONF = {
        "name": "Formats' Configuration Loader",
        "impl_id": "resources.coverages.formats.FormatLoaderStartupHandler",
        }

    def __loadFormats( self , config , registry ) : 

        logging.debug(" --==@ FormatLoaderStartupHandler( StartupHandlerInterface ) @==-- ")

        # instantiate format registry 

        global __FORMAT_REGISTRY

        __FORMAT_REGISTRY = FormatRegistry( config )


    def startup( self , config , registry ) :
        """ start-up handler """ 
        return self.__loadFormats( config , registry )
    
    def reset( self , config , registry ) :
        """ reset handler """ 
        return self.__loadFormats( config , registry )

FormatLoaderStartupHandlerImplementation = StartupHandlerInterface.implement( FormatLoaderStartupHandler ) 
    
#-------------------------------------------------------------------------------
# public API 

def getFormatRegistry() : 
    """
        Get initialised format registry.
    """

    global __FORMAT_REGISTRY

    if __FORMAT_REGISTRY is None :  

        # load configuration if not already loaded 
        __FORMAT_REGISTRY = FormatRegistry( System.getConfig() ) 

    return __FORMAT_REGISTRY 

#-------------------------------------------------------------------------------
