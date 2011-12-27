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

# namespaces 
NS_EOP20='http://www.opengis.net/eop/2.0'

#tags 
EOP="{%s}EarthObservation" % NS_EOP20
MDP="{%s}metaDataProperty" % NS_EOP20
EOM="{%s}EarthObservationMetaData" % NS_EOP20
IDN="{%s}identifier" % NS_EOP20

#-------------------------------------------------------------------------------

def eop20GetID( src ) :  
    """ get identifier from the EOP2.0 XML document """

    # look up the identifier   
    tmp = etree.parse( src ) 
    tmp = tmp.find( MDP ) 
    tmp = tmp.find( EOM ) 
    tmp = tmp.find( IDN ) 

    return tmp.text

def eop20SetID( src , dst , eoid ) : 

    # look up the identifier   
    tmp = etree.parse( src ) ; root = tmp 

    tmp = tmp.find( MDP ) 
    tmp = tmp.find( EOM ) 
    tmp = tmp.find( IDN ) 

    tmp.text = eoid 

    # save the result 
    root.write( dst , encoding='UTF-8' )
    dst.flush() 


if __name__ == "__main__" : 
        
    fname = os.path.abspath( sys.argv[1] ) 

    print "FNAME: " , fname 

    print "NAME " , eop20GetID( file( fname ) ) 

    eop20SetID( StringIO( file(fname).read() ) , file(fname,"w") , "NEW_ID" ) 

    print "NAME " , eop20GetID( file( fname ) ) 
