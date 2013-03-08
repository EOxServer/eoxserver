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
This module contains implementation of MIME multipart packing and unpacking 
utilities.

The main benefit of the utilities over other methods of mutipart handling 
is that the functions of this module do not manipulate the input data
buffers and especially avoid any unnecessary data copying. 
"""

#-------------------------------------------------------------------------------

def capitalize( header_name ) : 
    """ Capitalize header field name. Eg., 'content-type' is capilalized to 'Content-Type'."""
    return "-".join([ f.capitalize() for f in header_name.split("-") ])

# local alias to prevent conflict with local variable
__capitalize = capitalize

#-------------------------------------------------------------------------------

def getMimeType( content_type ) : 
    """ Extract MIME-type from Content-Type string and convert it to lower-case."""
    return content_type.partition(";")[0].strip().lower() 

def getMultipartBoundary( content_type ) : 
    """ Extract boundary string from mutipart Content-Type string."""

    for opt in content_type.split(";")[1:] : 
        key , _ , val = opt.partition("=")
        if ( key.strip().lower() == "boundary" ) : 
            return val.strip() 
     
    raise ValueError , "failed to extract the mutipart boundary string! content-type: %s" % content_type 

#-------------------------------------------------------------------------------

def mpPack( parts , boundary ) :
    """
Low-level memory-friendly MIME multipart packing.

Note: The data payload is passed untouched and no transport encoding 
of the payload is performed. 

Inputs: 

 - parts - list of part-tuples, each tuple shall have two elements 
    the header list and (string) payload. The header itsels should be 
    a sequence of key-value pairs (tuples). 

 - boundary - boundary string 

Ouput: 
  
 - list of strings (which can be directly passsed as a Django response content)
    """

    # empty multipart package 
    pack = [ "--%s"%boundary ]

    for header,data  in parts :

        # pack header 
        for key,value in header :
            pack.append( "\r\n%s: %s"%( key, value ) )

        # terminate header
        pack.append( "\r\n\r\n" )

        # append data 
        pack.append( data )

        # terminate partition 
        pack.append( "\r\n--%s"%boundary )

    #terminate package 
    pack.append("--")

    # return package 
    return pack

#-------------------------------------------------------------------------------

def mpUnpack( cbuffer , boundary , capitalize = False ) :
    """
Low-level memory-friendly MIME multipart unpacking.

Note: The payload of the multipart package data is neither modified nor copied. 
No decoding of the transport encoded payload is performed. 

Note: The subroutine does not unpack any nested mutipart content. 

Inputs: 

 - ``cbuffer`` - character buffer (string) containing the 
   the header list and (string) payload. The header itsels should be 
   a sequence of key-value pairs (tuples). 

 - ``boundary`` - boundary string 

 - ``capitalize`` - by default the header keys are converted to lower-case (e.g., 'content-type'). 
   To capitalize the names (e.g., 'Content-Type') set this option to true.

Output: 

 - list of parts - each part is a tuple of the header dictionary,
   payload ``cbuffer`` offset and payload size.

    """

    #--------------------------------------------------------------------------
    # boundary finder - closure 

    def findBorder( offset = 0 ) :

        delim = "--%s"%boundary if offset == 0 else "\n--%s"%boundary               
                                                                                    
        # boundary offset (end of last data)                                        
        idx0 = cbuffer.find( delim , offset )                                       
                                                                                    
        if ( idx0 < 0 ) :                                                           
            raise ValueError , "Boundary cannot be found!"                          
                                                                                    
        # header offset                                                             
        idx1 = idx0 + len( delim )                                                  
                                                                                    
        # nescessary check to be able to safely check two following characters      
        if len(cbuffer[idx1:]) < 2  :                                               
            raise ValueError , "Buffer too short!"                                  
                                                                                    
        # check the leading CR character                                            
        if ( idx0 > 0 ) and ( cbuffer[idx0-1] == "\r" ) : idx0 -= 1                 
                                                                                    
        # check the terminating sequence                                            
        if cbuffer[idx1:(idx1+2)] == "--" : return ( idx0, idx1+2 , -1 )            
                                                                                    
        # look-up double endl-line (data offset)                                    
        tmp = idx1                                                                  
                                                                                    
        while True :                                                                
                                                                                    
            tmp = 1 + cbuffer.find( "\n" , tmp )                                    
                                                                                    
            if ( tmp < 1 ) :                                                        
                raise ValueError , "Cannot find payload's a double new-line separator!"
                                                                                    
            # is it followed by new line?                                           
                                                                                    
            elif cbuffer[tmp:(tmp+2)] == "\r\n" :                                   
                idx2 = tmp + 2                                                      
                break                                                               
                                                                                    
            elif cbuffer[tmp:(tmp+1)] == "\n" :                                     
                idx2 = tmp + 1                                                      
                break                                                               
                                                                                    
            # otherwise continue to lookup                                          
            continue

        # adjust the data offset (separator must be followed by new-line)           
        if   cbuffer[idx1:(idx1+2)] == "\r\n" : idx1 += 2                           
        elif cbuffer[idx1:(idx1+1)] == "\n"   : idx1 += 1                           
        else :                                                                      
            raise ValueError , "Boundary is not followed by a new-line!"            
                                                                                    
        return ( idx0 , idx1 , idx2 )

    #--------------------------------------------------------------------------
    # auxiliary nested functions formating header names 

    # capitalize header name  
    def unpackCC( v ) :
        key , _ , val  = v.partition(":")
        return ( __capitalize(key.strip()) , val.strip() )

    # header name all lower 
    def unpackLC( v ) :
        key , _ , val  = v.partition(":")
        return ( key.strip().lower() , val.strip() )

    # filter function rejecting entries with blank keys 
    def noblank( (k,v) ) : return bool(k) 

    #--------------------------------------------------------------------------

    # get the offsets 
    # off = (<last payload end>,<header start>,<payload start>)
    # negative <payload start> means terminating boundary  

    try : 

        off = findBorder()
        offsets  = [off]

        while off[1] < off[2] :
            off = findBorder( off[2] )
            offsets.append(off)

    except ValueError as e :

        raise "The buffer is not a valid MIME multi-part message!"\
              " Reason: %s" % e.message 

    # process the parts 
    parts    = []
    for of0 , of1 in zip( offsets[:-1] , offsets[1:] ) :

        # get the http header with <LF> line ending 
        tmp = cbuffer[of0[1]:of0[2]].replace("\r\n","\n")[:-2].split("\n")

        # unpack header 
        header = dict(filter(noblank,map((unpackLC,unpackCC)[capitalize],tmp))) 

        # get the header and payload offset and size 
        parts.append( ( header , of0[2] , of1[0]-of0[2] ) )

    return parts
