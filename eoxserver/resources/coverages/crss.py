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
 This module provides CRS handling utilities.
"""

#-------------------------------------------------------------------------------

from osgeo import osr
import logging
from eoxserver.core.system import System

#-------------------------------------------------------------------------------
# format functions 

def asInteger( v ): 
    """ convert EPSG code to integer """
    return int(v) 

def asShortCode( v ):  
    """ convert EPSG code to short CRS ``EPSG:<code>`` notation """
    return "EPSG:%d"%int(v)

def asURL( v ):  
    """ convert EPSG code to OGC URL CRS 
    ``http://www.opengis.net/def/crs/EPSG/0/<code>`` notation """
    return "http://www.opengis.net/def/crs/EPSG/0/%d"%int(v) 

def asURN( v ):
    """ convert EPSG code to OGC URN CRS ``urn:ogc:def:crs:epsg::<code>`` 
    notation """
    return "urn:ogc:def:crs:epsg::%d"%int(v) 

def asProj4Str( v ) : 
    """ convert EPSG code to *proj4* ``+init=epsg:<code>`` notation """
    return "+init=epsg:%d"%int(v)

#-------------------------------------------------------------------------------
# public API 

__SUPPORTED_CRS_WMS = None
__SUPPORTED_CRS_WCS = None

def getSupportedCRS_WMS( format_function = asShortCode ) : 
    """ Get list of CRSes supported by WMS. The ``format_function`` is used to
    format individual list items.""" 

    global __SUPPORTED_CRS_WMS

    if __SUPPORTED_CRS_WMS is None : 

        __SUPPORTED_CRS_WMS = __parseListOfCRS( System.getConfig() , 
                "services.ows.wms","supported_crs")

    # return formated list of EPSG codes 
    return map( format_function , __SUPPORTED_CRS_WMS ) 


def getSupportedCRS_WCS( format_function = asShortCode ) : 
    """ Get list of CRSes supported by WCS. The ``format_function`` is used to
    format individual list items.""" 

    global __SUPPORTED_CRS_WCS

    if __SUPPORTED_CRS_WCS is None : 

        __SUPPORTED_CRS_WCS = __parseListOfCRS( System.getConfig() , 
                "services.ows.wcs","supported_crs")

    # return formated list of EPSG codes 
    return map( format_function , __SUPPORTED_CRS_WCS ) 


#-------------------------------------------------------------------------------

def __parseListOfCRS( config , section , field ) : 
    """ parse CRS configuartion """ 

    spat_ref = osr.SpatialReference() 

    # validate and convert to EPSG code 
    def checkCode( v ) :
        # validate the input CRS whether recognized by GDAL/Proj 
        # NOTE: the try-except block catches also invalid non-iteger input
        try : 
            if spat_ref.ImportFromEPSG(int(v)) != 0 : raise ValueError 
        except ValueError : 
            logging.warning( "Invalid EPSG code \"%s\" ! This CRS will be " \
                "ignored! section=\"%s\" item=\"%s\""%( str(v).strip() , 
                section , field ) )
            return False
        return True

    # read the configuration 
    tmp = config.getConfigValue( section , field )

    # strip comments 
    tmp = "".join([ l.partition("#")[0] for l in tmp.split("\n") ])

    # filter out invalid EPSG codes and covert them to integer 
    return map( int , filter( checkCode , tmp.split(",") ) ) 

#-------------------------------------------------------------------------------
