#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#  miscelaneous utilities 
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
import base64
import urllib
import httplib
import logging 
import mimetypes
import time 
import ftplib
import sys
import traceback
import urlparse 

try :       from cStringIO import StringIO 
except :    from StringIO import StringIO 
#-------------------------------------------------------------------------------

import wcst11Exception 
#import ExInvalidURI, ExServerBusy

#-------------------------------------------------------------------------------

def saveToFile( data , fname , mode = "w" , encoding = "UTF-8" ) : 
    """ save string to file """

    fid = file( fname , mode ) 

    if type( data ) is unicode : 
        tmp = data.encode( encoding ) 
    else : 
        tmp = str( data ) 

    fid.write( tmp ) 

    fid.close() 

#-------------------------------------------------------------------------------

LLEVELS = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }

def loggingSetUp( context ) : 

    msg   = "%(message)s" 

    logging.basicConfig(
        level    = LLEVELS[ context['loggingLevel'] ],
        format   = context['loggingFormat'].replace(msg,"(%s) %s"%(context["tid"],msg)) , 
        filename = context['loggingFilename'] ) 

def loggingShutDown() : 

    logging.shutdown()

#-------------------------------------------------------------------------------

def timeStampUTC( ttt = None ) : 
    """ get ISO XML date-time """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", \
        time.gmtime() if ( ttt is None ) else ttt )

#-------------------------------------------------------------------------------

# return a new process ID token 
def getNewCoverageID() : 
    return "wcstCov_%s" % ( base64.urlsafe_b64encode( os.urandom(15) ) ) 

# return a new request ID token 
def getNewRequestID() : 
    return "wcstReq_%s" % ( base64.urlsafe_b64encode( os.urandom(15) ) ) 

#-------------------------------------------------------------------------------

def guessExtension( mimeType ) : 

    try : 

        mimeType = mimeType.split(';')[0].strip()

        if mimeType in ( "text/xml" , "application/xml" ) : 
            ext = ".xml"
        elif mimeType == "image/jpeg" : 
            ext = ".jpg"
        else : 
            ext = mimetypes.guess_extension( mimeType )

    except Exception as e : 
        logging.warning( str( e ) ) 

        ext = ".data" 
        mimeType  = None 

    return ext , mimeType 


#-------------------------------------------------------------------------------

class HTTPError( Exception ) : pass  

def downloadReference( url , basename , prefix = "" ) : 
    """
        donwload reference - baseline 
    """
    if prefix : prefix = "%s: " % prefix 

    # open the URL and get info 
    sock = urllib.urlopen( url )

    #check the HTTP error code 
    httpCode = sock.getcode()
    if ( httpCode is not None ) and ( int(httpCode) != 200 ) :  
        raise HTTPError , "%sCode: %s\tURL: %s" % ( prefix , str(httpCode) , url ) 
    
    # guess file extension 
    info = sock.info() 
    ext , contentType = guessExtension( info["Content-Type"] )

    # prepare filename 
    filename = "%s%s" %( basename , ext ) 

    logging.info( "%sDownloading: [%s] %s --> %s " % ( prefix , str(contentType) , url , filename ) ) 

    # download the file 
    fid = file( filename , "w" ) 

    for block in sock : 
        fid.write( block ) 

    fid.close() 

    # close the connection 
    sock.close() 

    return filename , contentType


def wcst11DownloadReference( url , basename , prefix = "" ) :
    """
        donwload reference - throwing proper OWS 1.1 exception in case of error 
    """
    try: 
        return downloadReference( url , basename , prefix )
    except Exception as e : 
        # keep track of the errors 
        logging.error( str(e) ) 
        raise wcst11Exception.ExInvalidURI( url ) 


#-------------------------------------------------------------------------------

class InvalidResponseHandler( Exception ) : pass 

# encryption supported by Python 2.7+
SUPPORTS_FTPS=hasattr( ftplib , "FTP_TLS" ) 

def checkResponseHandler( responseHandlerURL ) : 

    if responseHandlerURL is None : return None 

    url = urlparse.urlparse( responseHandlerURL ) 

    if url.scheme not in ( 'ftp' , 'ftps' , 'http' , 'https' ) : 
        if '' == url.scheme : 
            raise InvalidResponseHandler , "The response handler does not seem to be a valid URL! responseHandler=%s " % responseHandlerURL 
        else : 
            raise InvalidResponseHandler , "Unsupported URL scheme '%s' ! responseHandler=%s " % ( url.schema , responseHandlerURL ) 

    if ( url.scheme == 'ftps' ) and not SUPPORTS_FTPS : 
        raise InvalidResponseHandler , "Unsupported URL scheme '%s' ! responseHandler=%s " % ( url.schema , responseHandlerURL ) 

    return responseHandlerURL 


def responseUpload( responseHandlerURL , response , filename ) : 
    """ upload response to a given response handler URL 
        
        currently supported protocols are: 

            ftp   - upload response over FTP 
            ftps  - upload response over FTPS (TLS secured FTP; P2.7+) 
            http  - post response over HTTP 
            https - post response over HTTPS (SSL secured HTTP) 

        NONE: HTTP authentication not supported (yet).
        NONE: SSL client certificate authentication not supported (yet). 

    """

    url = urlparse.urlparse( responseHandlerURL ) 

    if   "http"  == url.scheme :
        responseUploadHTTP( url, responseHandlerURL, response, False ) 

    elif "https" == url.scheme :
        responseUploadHTTP( url, responseHandlerURL, response, True ) 

    elif "ftp"   == url.scheme :
        responseUploadFTP( url, responseHandlerURL, response, filename, False ) 

    elif ( "ftps"  == url.scheme ) and SUPPORTS_FTPS : 
        responseUploadFTP( url, responseHandlerURL, response, filename, True ) 

    else : 
        raise InvalidResponseHandler , "Unsupported URL schema '%s' ! "\
                "responseHandler=%s " % ( url.schema , responseHandlerURL ) 

#-------------------------------------------------------------------------------

def responseUploadFTP( url , responseHandlerURL , response , filename , secure ) : 

    # extract connection parameters

    username = "anonymous" if url.username is None else url.username 
    password = "anonymous@eoxserver.org" if url.password is None else url.password 
    hostname = "localhost" if not url.hostname else url.hostname
    portnumb = 21 if url.port is None else url.port
    path     = "/" if not url.path else url.path 

    # connect to FTP server 

    ftp = ftplib.FTP_TLS() if secure else ftplib.FTP() 

    ftp.connect( hostname , portnumb )

    try: 

        # secure the connection 
        if secure : 
            ftp.auth()
            ftp.prot_c()

        ftp.login( username , hostname )

        try : # assuming the path is a directory 

            ftp.cwd( path ) 

        except ftplib.error_perm : # assuming the path is a filename 
        
            # split filename from the path 
            filename = os.path.basename( path ) 
            path     = os.path.dirname( path ) 

            ftp.cwd( path )

        # secure the data transfers 
        if secure : ftp.prot_s()

        # upload file 
        ftp.storbinary( 'STOR %s' % filename , StringIO( response ) )

    finally : # close FTP connection 

        ftp.close() 


def responseUploadHTTP( url , responseHandlerURL , response , secure ) : 

    # extract connection parameters

    hostname = "localhost" if not url.hostname else url.hostname
    selector = urlparse.urlunsplit( (None,None,url.path,url.query,url.fragment) )

    # start the proper HTTP os HTTPS connection

    if secure : # HTTPS 
        portnumb = 443 if url.port is None else url.port
        http = httplib.HTTPSConnection(hostname,portnumb)
    else : # HTTP
        portnumb = 80 if url.port is None else url.port
        http = httplib.HTTPConnection(hostname,portnumb)

    # start the request and get the response 
    http.request("POST", selector , response , {"Content-type":"text/xml"} )
    resp = http.getresponse()

    # log the return status 
    if int( resp.status ) not in ( 200 , 204 ) : 
        raise InvalidResponseHandler , "HTTP/POST FAILED! URL=%s ; STATUS=%s %s" \
            % ( responseHandlerURL , str(resp.status) , resp.reason ) 

