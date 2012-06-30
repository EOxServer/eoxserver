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
This module contains implementation of MIME multipart packing and unpacking utilities.
"""

#-------------------------------------------------------------------------------

def mpPack( parts , boundary ) :
    """Low-level memory-friendly MIME multipart packing.

       Note: the payload is not affected and the transport encoding 
       of the payload is not performed. 

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
            pack.append( "\n%s: %s"%( key, value ) )

        # terminate header
        pack.append( "\n\n" )

        # append data 
        pack.append( data )

        # terminate partition 
        pack.append( "\n--%s"%boundary )

    #terminate package 
    pack.append("--")

    # return package 
    return pack

def mpUnpack( cbuffer , boundary ) :
    """Low-level memory-friendly MIME multipart unpacking.

       Note: the payload is not affected and the decodiing of the transport encoded
       payload is not performed. 

       Inputs: 

        - ``cbuffer`` - character buffer (string) containing the 
          the header list and (string) payload. The header itsels should be 
          a sequence of key-value pairs (tuples). 

        - ``boundary`` - boundary string 

       Output: 

        - list of parts - each part is a tuple of the header dictionary,
          payload ``cbuffer`` offset and payload size.

       Note: The header keys are converted to lower-case.
    """

    def findBorder( offset = 0 ) :

        delim = "--%s"%boundary if offset == 0 else "\n--%s"%boundary

        dlen = len( delim )
        idx = dlen + cbuffer.find( delim , offset )

        if ( idx < dlen ) or ( len(cbuffer[idx:]) < 2 )  : raise ValueError , "The input buffer is not a valid multi-part package!"

        if cbuffer[idx:(idx+2)] == "--" :

            # termination 
            return ( idx - dlen , idx+2 , -1 )

        elif cbuffer[idx] != "\n" :
            raise ValueError , "The input buffer is not a valid multi-part package!"

        idx += 1

        # lookup the data begin
        jdx = 2 + cbuffer.find( "\n\n" , idx )

        if ( jdx < 2 ) : raise ValueError , "The input buffer is not a valid multi-part package!"

        return ( idx - dlen , idx , jdx )

    def unpack( v ) :
        key , _ , val  = v.partition(":")
        return ( key.lower() , val.strip() )

    # get the offsets 
    off = findBorder()
    offsets  = [off]

    while off[1] < off[2] :
        off = findBorder( off[2] )
        offsets.append(off)

    # process the parts 
    parts    = []
    for of0 , of1 in zip( offsets[:-1] , offsets[1:] ) :

        # unpack header 
        header = dict( map( unpack , cbuffer[of0[1]:(of0[2]-2)].split("\n") ) )

        # get the header and payload offset and size 
        parts.append( ( header , of0[2] , of1[0]-of0[2] ) )

    return parts

    pass
