#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@iguassu.cz>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 Iguassu Software Systems a.s. 
#
# MEPermission is hereby granted, free of charge, to any person obtaining a copy
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

import logging
from eoxserver.core.system import System
from eoxserver.services.requests import Response

from xml.etree import ElementTree as etree

from eoxserver.core.system import System


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------
# actions

from wcstCommon import ACTIONS 

ACTIONS_UPPER=map( lambda s : s.upper() , ACTIONS ) 
ACTIONS_U2N= dict( zip( ACTIONS_UPPER , ACTIONS ) ) 

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

NS_WCS11="http://www.opengis.net/wcs/1.1"
NS_OWS11="http://www.opengis.net/ows/1.1"
NS_WCS20="http://www.opengis.net/wcs/2.0"
NS_OWS20="http://www.opengis.net/ows/2.0"
NS_XLN="http://www.w3.org/1999/xlink"
NS_XSI="http://www.w3.org/2001/XMLSchema-instance"

# attribute names 

A_href      = '{%s}href'%NS_XLN 
A_type      = '{%s}type'%NS_XLN
A_name      = 'name'

# element names

class OWS11: pass 


OWS11.version     = '1.1' 
OWS11.E_DCP       = '{%s}DCP'%NS_OWS11
OWS11.E_HTTP      = '{%s}HTTP'%NS_OWS11
OWS11.E_Post      = '{%s}Post'%NS_OWS11 
OWS11.E_Fees      = '{%s}Fees'%NS_OWS11 
OWS11.E_Value     = '{%s}Value'%NS_OWS11
OWS11.E_Profile   = '{%s}Profile'%NS_OWS11
OWS11.E_Operation = '{%s}Operation'%NS_OWS11 
OWS11.E_Parameter = '{%s}Parameter'%NS_OWS11 
OWS11.E_Constraint = '{%s}Constraint'%NS_OWS11
OWS11.E_AllowedValues = '{%s}AllowedValues'%NS_OWS11 
OWS11.E_AccessConstraints = '{%s}AccessConstraints'%NS_OWS11 
OWS11.E_OperationsMetadata = '{%s}OperationsMetadata'%NS_OWS11 
OWS11.E_ServiceIdentification = '{%s}ServiceIdentification'%NS_OWS11

class OWS20: pass 

OWS20.version     = '2.0' 
OWS20.E_DCP       = '{%s}DCP'%NS_OWS20
OWS20.E_HTTP      = '{%s}HTTP'%NS_OWS20
OWS20.E_Post      = '{%s}Post'%NS_OWS20 
OWS20.E_Fees      = '{%s}Fees'%NS_OWS20 
OWS20.E_Value     = '{%s}Value'%NS_OWS20
OWS20.E_Profile   = '{%s}Profile'%NS_OWS20
OWS20.E_Operation = '{%s}Operation'%NS_OWS20 
OWS20.E_Parameter = '{%s}Parameter'%NS_OWS20 
OWS20.E_Constraint = '{%s}Constraint'%NS_OWS20
OWS20.E_AllowedValues = '{%s}AllowedValues'%NS_OWS20 
OWS11.E_AccessConstraints = '{%s}AccessConstraints'%NS_OWS11 
OWS20.E_OperationsMetadata = '{%s}OperationsMetadata'%NS_OWS20 
OWS20.E_ServiceIdentification = '{%s}ServiceIdentification'%NS_OWS20


#-------------------------------------------------------------------------------

def splitQN( qname ) : 
    " split etree qualified name in form of {<namespace>}lname " 
    if qname[0] == "{" : 
        ns , sep , lname = qname[1:].partition( "}" ) 
        return ns , lname 
    else : 
        return None , qname 

#-------------------------------------------------------------------------------

def wcst11AlterCapabilities11( respSrc ) : 

    # register namespace prefixes 
    register_namespace("wcs",NS_WCS11)
    register_namespace("ows",NS_OWS11)
    register_namespace("xsi",NS_XSI) 
    register_namespace("xlink",NS_XLN) 

    return _wcst11AlterCapabilities( respSrc , OWS11 ) 

def wcst11AlterCapabilities20( respSrc ) : 

    # register namespace prefixes 
    register_namespace("wcs",NS_WCS20)
    register_namespace("ows",NS_OWS20)
    register_namespace("xsi",NS_XSI) 
    register_namespace("xlink",NS_XLN) 

    return _wcst11AlterCapabilities( respSrc , OWS20 ) 

#-------------------------------------------------------------------------------
    
def _wcst11AlterCapabilities( respSrc , OWS ) : 

    conf = System.getConfig()
    regs = System.getRegistry() 

    # get the service URL  
    base_url = conf.getConfigValue("services.owscommon","http_service_url") 

    # =====================================================================
    # check the content 

    try : 

        # check if the WCST11 request handler is registered and enabled
        if not regs.getImplementationStatus("services.ows.wcs11Transaction.WCS11TransactionHandler") :  
            raise Exception , "Operation handler is not enabled!"

        # check if payload contains XML content 
        if respSrc.content_type not in ("text/xml","application/xml") : 
            raise Exception , "Not XML!"
    
        # parse the original payload 
        root = etree.fromstring( respSrc.content )

        # check the root element 
        if splitQN( root.tag )[1] != "Capabilities" :
            raise Exception , "Not Capabilities!"

        # check version  
        if not root.get('version','').startswith(OWS.version) : 
            raise Exception ,"Not Capabilities version %s!" % OWS.version 

        # look for OperationsMetadata 
        eOM = root.find( OWS.E_OperationsMetadata ) 

        # look for ServiceIdentification 
        eSI = root.find( OWS.E_ServiceIdentification ) 

        if ( eOM is None ) and ( eSI is None ) : 
            raise Exception , "No element to be altered has been found!"

    except Exception as e : 

        # keep track of the failures 
        logger.debug( "_wcst11AlterCapabilities(): version %s : Content not altered! reason: %s " % ( OWS.version , str(e) ) ) 

        # return unafected original response 
        return respSrc  

    # =====================================================================
    # insert new Profile element to ServiceIdentification

    conf = System.getConfig()
 
    if eOM is not None :

        #insert sub-element before the selected elements 
        def insertBefore( dst , src , before ) : 

            # get the sublelements  
            elements = filter( lambda e : ( e is not None ) , map( lambda tag : dst.find( tag ) , before ) ) 

            try: 
                # locate firts sublelemet 
                dl  = list( dst ) 
                idx = min( map( lambda e : dl.index( e ) , elements ) )

                # create element 
                e = etree.Element( src ) 

                # insert element at the desired position 
                dst.insert( idx , e ) 

            except: 
            
                # simply append elemet at the end 
                e = etree.SubElement( dst , src ) 

            return e 

        before = ( OWS11.E_Fees , OWS11.E_AccessConstraints ) ; 

        # ows:Profile - WCSt >>Multiple Actions<< 
        if ( "True" == conf.getConfigValue("services.ows.wcst11","allow_multiple_actions") ) : 
            #etree.SubElement( eSI , OWS.E_Profile ).text = "urn:ogc:extension:WCS:1.1:TransactionMultipleActions"
            insertBefore( eSI , OWS.E_Profile , before ).text = "urn:ogc:extension:WCS:1.1:TransactionMultipleActions"

        # unpack the allowed actions 
        allowedActions = conf.getConfigValue("services.ows.wcst11","allowed_actions")
        allowedActions = set( filter( lambda s : s in ACTIONS_UPPER , map( lambda s : s.strip().upper() , allowedActions.split(",") ) ) )  

        # annotate allowd actions 
        for action in allowedActions : 
            # ows:Profile - WCSt allowed action action
            #etree.SubElement( eSI , OWS.E_Profile ).text = "urn:ogc:extension:WCS:1.1:Transaction%s" % ACTIONS_U2N[action] 
            insertBefore( eSI , OWS.E_Profile , before ).text = "urn:ogc:extension:WCS:1.1:Transaction%s" % ACTIONS_U2N[action] 

    # =====================================================================
    # insert new Operation element to OperationMetadata 

    if eOM is not None : 

        # ows:Operation
        eOp= etree.SubElement( eOM , OWS.E_Operation, { A_name : "transaction" } )

        # ows:DCP
        tmp = etree.SubElement( eOp , OWS.E_DCP )
        tmp = etree.SubElement( tmp , OWS.E_HTTP )
        tmp = etree.SubElement( tmp , OWS.E_Post , { A_href : base_url , A_type : "simple" } )

        # ows:Constraint 
        if 1 < int(OWS.version[0]) : 
            tmp = etree.SubElement( tmp , OWS.E_Constraint , { A_name : "PostEncoding" } )
            tmp = etree.SubElement( tmp , OWS.E_AllowedValues )
            tmp = etree.SubElement( tmp , OWS.E_Value )
            tmp.text = "XML"

        # ows:Parameter 
        tmp = etree.SubElement( eOp , OWS.E_Parameter , { A_name : "service" } )
        tmp = etree.SubElement( tmp , OWS.E_AllowedValues )
        tmp = etree.SubElement( tmp , OWS.E_Value )
        tmp.text = "WCS"

        # ows:Parameter 
        tmp = etree.SubElement( eOp , OWS.E_Parameter , { A_name : "version" } )
        tmp = etree.SubElement( tmp , OWS.E_AllowedValues )
        tmp = etree.SubElement( tmp , OWS.E_Value )
        tmp.text = "1.1"

    # =====================================================================
    # return the altered payload 

    return Response( content= etree.tostring(root,"UTF-8") , content_type=respSrc.content_type , status=respSrc.status ) 
