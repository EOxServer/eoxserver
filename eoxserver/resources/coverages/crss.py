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

import logging
from eoxserver.core.system import System

#-------------------------------------------------------------------------------
# public API 

def getSupportedCRS_WMS( config = None , format_function = asShortCode ) : 
    """ Get list of CRSes supported by WMS. If ``config`` not provided the
    default ``System.getConfig()`` is used. The ``format_function`` is used to
    format individual list items.""" 
    if config is None : config = System.getConfig()
    return __parseListOfCRS(config,"services.ows.wms","supported_crs",format_function)

def getSupportedCRS_WCS( config = None , format_function = asShortCode ) : 
    """ Get list of CRSes supported by WCS. If ``config`` not provided the
    default ``System.getConfig()`` is used. The ``format_function`` is used to
    format individual list items.""" 
    if config is None : config = System.getConfig()
    return __parseListOfCRS(config,"services.ows.wcs","supported_crs",format_function)

#-------------------------------------------------------------------------------

def __parseListOfCRS( config , section , field , format_function ) : 
    """ parse CRS configuartion """ 

    tmp0 = config.getConfigValue( section , field )

    # strip comments 
    tmp1 = [] 
    for l in tmp0.split("\n") :
        tmp1.append( l.partition("#")[0] ) 
    tmp0 = "".join(tmp1) 

    # validate and convert to EPSG code 
    def checkCode( v ) : 
        try : 
            return 0 < int(v) 
        except ValueError : 
            logging.warning( "Failed to convert \"%s\" to an EPSG code! This CRS will be ignored! section=\"%s\" item=\"%s\"" %( v , section , field ) )
            return False 

    tmp1 = map( format_function , filter( checkCode , tmp0.split(",") ) ) 

    return tmp1 

#-------------------------------------------------------------------------------
# format functions 

def asInteger( v ): 
    """ convert EPSG code to integer """
    return int(v) 

def asShortCode( v ):  
    """ convert EPSG code to short CRS ``EPSG:<code>`` notation """
    return "EPSG:%d"%int(v)

def asURL( v ):  
    """ convert EPSG code to OGC URL CRS notation ``http://www.opengis.net/def/crs/EPSG/0/<code>`` notation """
    return "http://www.opengis.net/def/crs/EPSG/0/%d"%int(v) 

def asURN( v ):
    """ convert EPSG code to OGC URN CRS notation ``urn:ogc:def:crs:epsg::<code>`` notation """
    return "urn:ogc:def:crs:epsg::%d"%int(v) 

def asProj4Str( v ) : 
    """ convert EPSG code to *proj4* ``+init=epsg:<code>`` notation """
    return "+init=epsg:%d"%int(v)

#-------------------------------------------------------------------------------

