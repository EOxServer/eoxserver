#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
# This file contains definition of WCS 1.1.x Transaction extension operation handler. 
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

from xml.dom.minidom import Node as DOMNode

#-----------------------------------------------------------------------

ELNODE = DOMNode.ELEMENT_NODE
CDNONE = DOMNode.CDATA_SECTION_NODE
TXNODE = DOMNode.TEXT_NODE

def getAttrValue( node , name , default = None ) : 
    # extract attrib. and its value
    sel = filter(lambda n: n.localName == name , node.attributes.values() )
    if len(sel) < 1 : return default
    return sel[0].value 
    #attr = node.attributes.get(name)   
    #if attr is None : return None 
    #return attr.value  

def getElementList( node , name = None ) : 
    if name :
        return filter(lambda n: n.nodeType == ELNODE and n.localName == name , node.childNodes )
    else : 
        return filter(lambda n: n.nodeType == ELNODE , node.childNodes )


def getSingleElement( node , name = None ) : 
    # get element by name 
    sel = getElementList( node , name ) 
    if len( sel ) < 1 : return None 
    return sel[0]

def getText( node ) : 
    # get text data 
    sel = filter( lambda n: n.nodeType in ( TXNODE , CDNONE ) , node.childNodes ) 
    # extract text 
    return "".join( map( lambda n: n.data , sel ) )
    
def getElemValue( node , name ) : 
    # get element by name 
    element = getSingleElement( node , name ) 
    if element is None : return None
    # get text data 
    return getText( element ) 

#-----------------------------------------------------------------------

class LangSelect( object ) : 
    """ human readable annotation in several language variants """

    def keys( self ) : 
        return self.__data.keys()

    def has_key( self , key ) : 
        return self.__data.has_key() 

    def items( self ) : 
        return self.items() 

    def __init__( self ) : 
        self.__data = {} 

    def __getitem__( self , key ) :
        """ __getitem__ returns the default item if specified language variant is missing """
        default = self.__data.get(None,None) 
        return self.__data.get( key , default ) 
        
    def __setitem__( self , key ,value ) :
        if type(key) is unicode : key = str(key) 
        self.__data[key] = value

    def __contains__( self , key ) :  
        return self.has_key( key ) 

    def __len__( self ) : 
        return len( self.__data ) 

    def __repr__( self ) : 
        return "LangSelect%s" % repr( self.__data ) 

    def __str__( self ) : 
        return "LangSelect%s" % str( self.__data ) 

    def __unicode__( self ) : 
        return u"LangSelect%s" % unicode( self.__data ) 

#-----------------------------------------------------------------------
    
class KeywordSet( object ) : 

    def __init__( self , kstype = None , codeSpace = None ) : 
        self.__keys = [] 
        self.codeSpace = codeSpace
        self.type      = kstype 

    def append( self , keyword , lang = None , kstype = None , codeSpace = None ) : 
        """ append new keyword with optional language specification """
        if type(lang) is unicode : lang = str(lang)  
        self.__keys.append( (keyword,lang) ) 

    def items( self ) : 
        """ list of all (keyword,language) tuples """
        return list( self.__keys ) 

    def keywordsAll( self ) : 
        """ get all keywords without language filtering """
        return map( lambda k,l : k , self.__keys )  
        
    def items( self , lang = None ) : 
        """ get keywords filtered by language """
        return map( lambda k,l : k , filter( lambda k,l: ( l == lang ) , self.__keys ) ) 

    def languages( self ) : 
        """ get set of all available language codes """
        return set( map( lambda k,l : l , self.__keys ) )   
        
    def __unicode__( self ) : 
        return u"KeywordSet(%s,type=%s,codeSpace=%s)" % ( unicode(self.__keys) , unicode(self.type) , unicode(self.codeSpace) ) 

    def __str__( self ) : 
        return unicode(self).encode("UTF-8")

    def __repr__( self ) :
        return str( self ) 
    
    def __bool__( self ) : 
        return ( len(self.__keys) > 0 ) 

#-----------------------------------------------------------------------

def parseCoverageXML( element ) : 

    prm = {} 

    #-----------------------------------------
    # Action        1   (mandatory) 

    action = getSingleElement( element , "Action" )  
    if action : action = getText( action ).strip()

    prm['Action'] = action if action else None 

    #-----------------------------------------
    # Identifier    0-1 

    identifier = getSingleElement( element , "Identifier" ) 
    if identifier : identifier = getText( identifier ).strip()  

    prm['Identifier'] = identifier if identifier else None 


    #-----------------------------------------
    # Title         0-N (lang)

    tmp = LangSelect() 
    for e in getElementList( element , "Title" ) : 
        tmp[getAttrValue(e,"lang")] = getText(e).strip()
    prm['Title']=tmp 

    #-----------------------------------------
    # Abstract      0-N (lang) 

    tmp = LangSelect() 
    for e in getElementList( element , "Abstract" ) : 
        tmp[getAttrValue(e,"lang")] = getText(e).strip()
    prm['Abstract'] = tmp 

    #-----------------------------------------
    # Keywords      0-N 

    keywords = []
    for eKW in getElementList( element , "Keywords" ) : 
        keySet = KeywordSet() 
        for e in getElementList( eKW , "Type" ) : 
            kt = getText(e).strip() 
            keySet.type      = kt if kt else None 
            keySet.codeSpace = getAttrValue( e , "codeSpace" )
        for e in getElementList( eKW , "Keyword" ) : 
            kw = getText(e).strip()
            if kw : keySet.append( kw , getAttrValue( e , "lang" ) ) 
        if keySet : keywords.append( keySet )
    prm['Keywords'] = keywords

    #-----------------------------------------
    # Reference     1-N (mandatory)

    def addItem( key ) : 
        tmp = getAttrValue(e,key) 
        if tmp : item[key] = tmp 

    prm['Reference']  = []
    for e in getElementList( element , "Reference" ) : 
        item = {} 
        for attrib in ("href","role","title","arcrole","actuate") : 
            addItem( attrib ) 
        if item : prm['Reference'].append( item ) 
        
    #-----------------------------------------
    # Metadata      0-N

    prm['Metadata'] = []
    for e in getElementList( element , "Metadata" ) : 
        item = {} 
        for attrib in ("about","href","role","title","arcrole","actuate") : 
            addItem( attrib ) 
        if item : prm['Metadata'].append( item ) 

    #-----------------------------------------

    return prm  
