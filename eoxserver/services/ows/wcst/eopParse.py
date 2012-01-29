#!/usr/bin/env python 
#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  EOP 2.0 parser and editor 
# 
#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@iguassu.cz>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 Iguassu Software Systems, a.s 
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

import os 
import sys 

try :       from cStringIO import StringIO
except :    from StringIO import StringIO

from xml.etree import ElementTree as etree

#-------------------------------------------------------------------------------
# explicite namespace prefix registration 

try:
    # works for Python >= 2.7 ( ElementTree >= 1.3 ) 
    register_namespace = etree.register_namespace
except AttributeError:
    # falback for older Python versions 
    def register_namespace(prefix, uri):
        etree._namespace_map[uri] = prefix

#-------------------------------------------------------------------------------

# namespaces 
NS_EOP20='http://www.opengis.net/eop/2.0'
NS_GML32='http://www.opengis.net/gml/3.2' 
NS_OM20='http://www.opengis.net/om/2.0'
NS_XSI="http://www.w3.org/2001/XMLSchema-instance"
NS_XLN="http://www.w3.org/1999/xlink"

#tags 
EOP="{%s}EarthObservation" % NS_EOP20
MDP="{%s}metaDataProperty" % NS_EOP20
EOM="{%s}EarthObservationMetaData" % NS_EOP20
IDN="{%s}identifier" % NS_EOP20

#-------------------------------------------------------------------------------
def _findElement( e0 , name ) : 
    """ find the first occurence of the element of the given name in the whole element tree """
    if e0.tag == name : return e0 
    for e in e0 : 
        rv = _findElement( e , name ) 
        if rv : return rv 
    return None 

def eop20GetID( src ) :  
    """ get identifier from the EOP2.0 XML document """

    # find the first occurence of the EOP element 
    tmp = _findElement( etree.parse( src ).getroot() , EOP ) 

    # find the identifier 
    tmp = tmp.find( MDP ) 
    tmp = tmp.find( EOM ) 
    tmp = tmp.find( IDN ) 

    return tmp.text

def eop20SetID( src , dst , eoid ) : 

    # find the first occurence of the EOP element 
    tmp = _findElement( etree.parse( src ).getroot() , EOP ) 
    root = tmp 

    tmp = tmp.find( MDP ) 
    tmp = tmp.find( EOM ) 
    tmp = tmp.find( IDN ) 

    tmp.text = eoid 

    # set the namespaces' prefixes 

    register_namespace( "eop" , NS_EOP20 )  
    register_namespace( "om"  , NS_OM20 )  
    register_namespace( "gml" , NS_GML32 )  
    register_namespace( "xsi" , NS_XSI ) 
    register_namespace( "xlink" , NS_XLN ) 

    # save the result 
    dst.write( etree.tostring( root , encoding='UTF-8' ) ) 
    dst.flush() 

# simle test 
if __name__ == "__main__" : 
        
    fname = os.path.abspath( sys.argv[1] ) 
    print "FNAME: " , fname 
    print "NAME " , eop20GetID( file( fname ) ) 
    #eop20SetID( StringIO( file(fname).read() ) , file(fname,"w") , "NEW_ID" ) 
    eop20SetID( StringIO( file(fname).read() ) , sys.stdout , "NEW_ID" ) 
    #eop20SetID( StringIO( file(fname).read() ) , file(fname,"w") , "NEW_ID" ) 
    #print "NAME " , eop20GetID( file( fname ) ) 
