#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   WCSt 1.1 Exceptions  
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

LANG="en"

#=======================================================
# base exception 

class OWS11_Exception( Exception ) : 
    """ base WPS exception """ 
    def __init__( self , locator = None , message = None ) : 
        self.locator = locator 
        self.message = message 
        self.msg = unicode( self ) 

    def getCode( self ) : 
        return self.__class__.__name__[2:]

    def __str__( self ) : 
        return unicode( self ).encode("UTF-8")

    def __unicode__( self ) : 
        t = [ u"code=%s" % self.getCode() ] 
        if self.locator is not None : t.append(u"locator=%s"%self.locator) 
        if self.message is not None : t.append(u"message=%s"%self.message) 
        return "OWS11_Exception{%s}"%(";".join(t) )

#=======================================================
# specific WPS exceptions 

# no locator exceptions
class ExServerBusy( OWS11_Exception ): 
    def __init__( self ): pass 

class ExNotEnoughStorage( OWS11_Exception ):
    def __init__( self ): pass 

# locator holding exceptions 

class ExInvalidParameterValue( OWS11_Exception ):
    def __init__( self , locator ): 
        OWS11_Exception.__init__( self , locator = locator ) 

class ExMissingParameterValue( OWS11_Exception ): 
    def __init__( self , locator ):
        OWS11_Exception.__init__( self , locator = locator ) 

class ExInvalidURI( OWS11_Exception ):
    def __init__( self , locator , message = None ): 
        OWS11_Exception.__init__( self , locator = locator ) 

class ExActionFailed( OWS11_Exception ):
    def __init__( self , locator ): 
        OWS11_Exception.__init__( self , locator = locator ) 

class ExOperationNotSupported( OWS11_Exception ):
    def __init__( self , locator , message = None ): 
        OWS11_Exception.__init__( self , locator = locator , message = message ) 

# generic exception 
class ExNoApplicableCode( OWS11_Exception ):
    def __init__( self , message ): 
        OWS11_Exception.__init__( self , message = message ) 


#=======================================================
# forming the exception report 

def createXML_OWS11Exception( exception ) : 

    xml = ows11ExceptionReport( exception ) 
    xml.insert(0,u'<?xml version="1.0" encoding="UTF-8"?>\n') 

    return ( u"".join(xml) ).encode("UTF-8") 

def ows11ExceptionReport( exception ) :

    xml = [] 

    # prepare exception

    try :   raise exception 
    except OWS11_Exception : pass # the exception is already a OWS11 exception
    except : # conversion must be done  
        exception = ExNoApplicableCode( unicode( exception ) ) 

    # prepare report 
    code = exception.getCode() 
    loc  = u' locator="%s"'%( exception.locator ) if exception.locator else "" 

    xml.append( u'<ows:ExceptionReport ' )
    xml.append( u'xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' )
    xml.append( u'xsi:schemaLocation="http://www.opengis.net/ows/1.1 http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd" ' )
    xml.append( u'xml:lang="%s" version="1.0.0">\n' % LANG ) 

    xml.append( u'\t<ows:Exception exceptionCode="%s"%s' % ( code , loc ) ) 

    if exception.message : 
        msg = unicode( exception.message ).replace( "]]>" , "]]]]><![CDATA[>" ) 
        xml.append( u">\n\t\t<ows:ExceptionText><![CDATA[%s]]></ows:ExceptionText>\n\t</ows:Exception>\n" % msg )
    else : 
        xml.append( u"/>\n" )

    xml.append( u'</ows:ExceptionReport>' ) 

    return xml 
