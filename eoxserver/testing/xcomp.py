#-------------------------------------------------------------------------------
#
# simple tool comparing XML documents - powered by Python miniDOM
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
#

""" Simple XML documets' comparator. """

import xml.dom.minidom as dom

from django.utils.six import string_types


# define node types 
ELEMENT_NODE                = dom.Element.ELEMENT_NODE
ATTRIBUTE_NODE              = dom.Element.ATTRIBUTE_NODE
TEXT_NODE                   = dom.Element.TEXT_NODE
CDATA_SECTION_NODE          = dom.Element.CDATA_SECTION_NODE
ENTITY_REFERENCE_NODE       = dom.Element.ENTITY_REFERENCE_NODE
ENTITY_NODE                 = dom.Element.ENTITY_NODE
PROCESSING_INSTRUCTION_NODE = dom.Element.PROCESSING_INSTRUCTION_NODE
COMMENT_NODE                = dom.Element.COMMENT_NODE
DOCUMENT_NODE               = dom.Element.DOCUMENT_NODE
DOCUMENT_TYPE_NODE          = dom.Element.DOCUMENT_TYPE_NODE
DOCUMENT_FRAGMENT_NODE      = dom.Element.DOCUMENT_FRAGMENT_NODE
NOTATION_NODE               = dom.Element.NOTATION_NODE

# define note type to string conversion 
NODE_DICT = { 
    ELEMENT_NODE                : "ELEMENT_NODE",
    ATTRIBUTE_NODE              : "ATTRIBUTE_NODE",
    TEXT_NODE                   : "TEXT_NODE",
    CDATA_SECTION_NODE          : "CDATA_SECTION_NODE",
    ENTITY_REFERENCE_NODE       : "ENTITY_REFERENCE_NODE",
    ENTITY_NODE                 : "ENTITY_NODE",
    PROCESSING_INSTRUCTION_NODE : "PROCESSING_INSTRUCTION_NODE",
    COMMENT_NODE                : "COMMENT_NODE",
    DOCUMENT_NODE               : "DOCUMENT_NODE",
    DOCUMENT_TYPE_NODE          : "DOCUMENT_TYPE_NODE",
    DOCUMENT_FRAGMENT_NODE      : "DOCUMENT_FRAGMENT_NODE",
    NOTATION_NODE               : "NOTATION_NODE",
} 

# exceptions 

class XMLError( Exception ) : 
    """ XML base error error """

class XMLParseError( XMLError ) : 
    """ XML parse error """

class XMLMismatchError( XMLError ) : 
    """ XML mismatch error """ 

#-------------------------------------------------------------------------------
# low level  utilities 

def _getNodeName( node ) : 
    """ get full node name in '{namespace}tagName' format """
    if ( node.namespaceURI is None ) : 
        return node.nodeName
    else : 
        return  "{%s}%s"%( node.namespaceURI , node.localName ) 

def _packName( pair ) :
    """ pack the (<namespace>,<localname>) tuple to curly bracket notation 
        {<namespace>}<localname> """ 
    if ( pair[0] is None ) : 
        return pair[1] 
    else :
        return "{%s}%s"%(pair[0],pair[1])


def _skipIgnorable( node , path ) : 
    """ get node sibling skipping empty text nodes and comments """ 

    while ( node is not None ) :  
        # expected nodes - return immediatelly 
        if node.nodeType in (ELEMENT_NODE,CDATA_SECTION_NODE): break 
        # special treatment of text nodes - ignore blank text 
        if node.nodeType == TEXT_NODE : 
            # ignore blank text  
            if 0 < len( node.wholeText.strip() ) : break 
        # unexpected nodes - raise exception  
        if node.nodeType in (ATTRIBUTE_NODE,DOCUMENT_NODE,DOCUMENT_FRAGMENT_NODE,
                NOTATION_NODE,ENTITY_REFERENCE_NODE,ENTITY_NODE,DOCUMENT_TYPE_NODE): 
            raise XMLParseError("Unexpected child node '%s' ! PATH='%s'" % (NODE_DICT[node.nodeType],path)) 
        # the rest is just ignored  
        #if node.nodeType in (COMMENT_NODE,PROCESSING_INSTRUCTION_NODE) : pass
        node = node.nextSibling 

    return node 

def _compareAttributes( a0 , a1 , level , path , verbose = False ) : 

    # both nodes have no attributes 
    if ( a0 is None ) and ( a1 is None ) : return 

    #attribute mismatch  
    if ( a0 is None ) or ( a1 is None ) :
            raise XMLMismatchError("Attribute mismatch! PATH=\"%s\""%path) 

    # get list of attributes and filter-out namespace definitions 
    isNotNS  = lambda v : ( v[0][0] != "http://www.w3.org/2000/xmlns/" )  
    packName = lambda v : ( _packName(v[0]) , v[1].strip() )

    items0 = sorted( map( packName , filter( isNotNS , a0.itemsNS() ) ) )  
    items1 = sorted( map( packName , filter( isNotNS , a1.itemsNS() ) ) )  

    if len( items0 ) != len( items0 ) : 
        if verbose : 
            for item in items0 :
                print (" < \t %s@%s=\"%s\"" %( path , item[0] , item[1] ))
            for item in items1 :
                print (" > \t %s@%s=\"%s\"" %( path , item[0] , item[1] ))
        raise XMLMismatchError("Attribute count mismatch! PATH=\"%s\""%path)

    for pair in zip( items0 , items1 ) : 
        if verbose : 
            print (" < \t %s@%s=\"%s\"" %( path , pair[0][0] , pair[0][1] )) 
            print (" > \t %s@%s=\"%s\"" %( path , pair[1][0] , pair[1][1] ))
        if ( pair[0] != pair[1]) : 
            raise XMLMismatchError("Attribute mismatch! PATH=\"%s\""%path)


def _compareNode( n0 , n1 , level = 0 , path = "/" , verbose = False ) : 
    """ compare DOM node or element subtree """
    
    #nn0 , nn1 = _getNodeName( n0 ), _getNodeName( n1 )
    nn0 , nn1 = n0.nodeName, n1.nodeName

    path0 = "%s/%s"%( path , nn0 ) if level > 1 else "/%s"%nn0 if level == 1 else _getNodeName( n0 )  
    path1 = "%s/%s"%( path , nn1 ) if level > 1 else "/%s"%nn1 if level == 1 else _getNodeName( n0 )

    if verbose : 
        print ("< \t %s" %( path0 )) 
        print ("> \t %s" %( path1 ))
    
    # compare node name and node type 
    if (( n0.nodeType != n1.nodeType ) 
        or ( _getNodeName( n0 ) != _getNodeName( n1 ) )): 
            raise XMLMismatchError("Node mismatch! PATH0=\"%s\" vs. PATH1=\"%s\""%(path0,path1)) 

    # compare attributes 
    _compareAttributes( n0.attributes , n1.attributes , level , path0 , verbose ) 

    # in case of text-nodes and CDATA section check the content 
    if n0.nodeType == TEXT_NODE : 
        if verbose : 
            print (" < TEXT: \t \"%s\"" % n0.wholeText.strip())
            print (" > TEXT: \t \"%s\"" % n1.wholeText.strip())
        if n0.wholeText.strip() != n1.wholeText.strip() : 
            raise XMLMismatchError("Text mismatch! PATH=\"%s\""%(path)) 
        return 

    if n0.nodeType == CDATA_SECTION_NODE : 
        if verbose : 
            print (" < CDATA: \t \"%s\"" % n0.wholeText)
            print (" > CDATA: \t \"%s\"" % n1.wholeText)
        if n0.wholeText != n1.wholeText : 
            raise XMLMismatchError("CDATA mismatch! PATH=\"%s\""%(path)) 
        return 

    
    # get first child
    nn0 = _skipIgnorable( n1.firstChild , path )
    nn1 = _skipIgnorable( n0.firstChild , path )
    while ( nn0 is not None ) and ( nn1 is not None ) : 
        # sublevel comparison 
        _compareNode( nn0 , nn1 , level+1 , path0 , verbose ) 
        #get next sibling 
        nn0 = _skipIgnorable( nn0.nextSibling , path )
        nn1 = _skipIgnorable( nn1.nextSibling , path )

    # make sure there are no remaining nodes 
    if not (( nn0 is None ) and ( nn1 is None )) :  
        raise XMLMismatchError("Childern count mismatch! PATH=\"%s\""%path0)

#-------------------------------------------------------------------------------

def xmlCompareDOMs( xml0 , xml1  , verbose = False ) : 
    """ Compare two XML documents passed as DOM trees (xml.dom.minidom)."""

    return _compareNode( xml0 , xml1 , verbose = verbose ) 


def xmlCompareStrings( str0 , str1  , verbose = False ) : 
    """ Compare two XML documents passed as strings. """ 

    def parse( src , label ) : 
        try : 
            return dom.parseString( src ) 
        except Exception as e : 
            raise XMLParseError("Failed to parse %s XML string! %s" % ( label , str(e) )) 

    return xmlCompareDOMs( parse(str0,"the first") , parse(str1,"the second") , verbose ) 


def xmlCompareFiles( src0 , src1 , verbose = False ) : 
    """ Compare two XML documents passed as filenames, file or file-like objects.""" 

    def parseFileName( src ) : 
        try : 
            with open( src ) as fid : 
                return dom.parse( fid ) 
        except Exception as e : 
            raise XMLParseError("Failed to parse the \"%s\" file! %s" % ( src , str(e) )) 

    def parseFileObj( src , label ) : 
        try : 
            return dom.parse( src ) 
        except Exception as e : 
            raise XMLParseError("Failed to parse the %s XML file(-like) object! %e" % ( label , str(e) )) 

    def parse( src , label ) : 
        return  parseFileName( src ) if ( type(src) in string_types ) else parseFileObj( src , label ) 

    return xmlCompareDOMs( parse(src0,"the first") , parse(src1,"the second") , verbose ) 

#-------------------------------------------------------------------------------

