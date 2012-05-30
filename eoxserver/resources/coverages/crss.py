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
 This module CRS handling utilities.
"""

#-------------------------------------------------------------------------------

import re 
import logging
from eoxserver.core.system import System

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
# format function 

asInteger = lambda v : int(v) 
asShortCode = lambda v : "EPSG:%4.4d"%int(v)
asURL = lambda v : "http://www.opengis.net/def/crs/EPSG/0/%4.4d"%int(v) 

#-------------------------------------------------------------------------------
# conversion from text formats 

_gerexValCRS_EPSGCode = re.compile( "^[1-9][0-9]{,4}$" ) 
_gerexValCRS_URL = re.compile( "^http://www.opengis.net/def/crs/EPSG/0/[1-9][0-9]{,4}$" ) 
_gerexValCRS_ShortCode = re.compile( "^EPSG:[1-9][0-9]{,4}$" ) 

#-------------------------------------------------------------------------------

def getSupportedCRS_WMS( config = None , format_function = asShortCode ) : 
    """ get list of CRSes supported by WMS """ 
    if config is None : config = System.getConfig()
    return __parseListOfCRS(config,"services.ows.wms","supported_crs",format_function)

def getSupportedCRS_WCS( config = None , format_function = asShortCode ) : 
    """ get list of CRSes supported by WCS """ 
    if config is None : config = System.getConfig()
    return __parseListOfCRS(config,"services.ows.wcs","supported_crs",format_function)
