#-----------------------------------------------------------------------
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

import os.path

import logging
import traceback 

#from eoxserver.core.util.xmltools import DOMElementToXML
#from eoxserver.core.exceptions import InternalError
from eoxserver.services.interfaces import OperationHandlerInterface
from eoxserver.services.interfaces import VersionHandlerInterface
from eoxserver.services.owscommon import OWSCommonVersionHandler

from eoxserver.core.system import System
from eoxserver.services.requests import Response
#from eoxserver.services.ogc import OGCExceptionHandler
from eoxserver.services.exceptions import InvalidRequestException
from eoxserver.services.base import BaseRequestHandler 

from eoxserver.services.ows.wcst.wcstXML import parseCoverageXML 
from eoxserver.services.ows.wcst.wcst11Transaction import wcst11Transaction
from eoxserver.services.ows.wcst.wcst11Context import contextCreate, contextDiscardSuccess, contextDiscardFailure, contextDiscardAsync
from eoxserver.services.ows.wcst.wcst11Exception import createXML_OWS11Exception, ExOperationNotSupported
# 
# NOTE: WCS-T allows service to be '1.1' only. Since the EOxServer accept version '1.1.0' only 
#       we need to define a new version handler dedicated to WCS-T only. 
#       If you (EOX guys) know a better solution please let me know.
#


logger = logging.getLogger(__name__)

class WCS11VersionHandler(OWSCommonVersionHandler):
    SERVICE = "wcs"
    
    REGISTRY_CONF = {
        "name": "WCS 1.1 Version Handler",
        "impl_id": "services.ows.wcs11Transaction.WCS11VersionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1"
        }
    }

WCS11VersionHandlerImplementation = VersionHandlerInterface.implement(WCS11VersionHandler)

#
# WCS-T operation handler 
#
NS_WCST11="http://www.opengis.net/wcs/1.1/wcst"

class WCS11TransactionHandler(BaseRequestHandler):

    REGISTRY_CONF = {
        "name": "WCS 1.1.x Transaction Handler",
        "impl_id": "services.ows.wcs11Transaction.WCS11TransactionHandler",
        "registry_values": {
            "services.interfaces.service": "wcs",
            "services.interfaces.version": "1.1",
            "services.interfaces.operation": "transaction"
        }
    }

    PARAM_SCHEMA = {
        "requestId": {"xml_location": "/{%s}RequestId"%NS_WCST11, "xml_type": "string", "kvp_key": "requestId", "kvp_type": "string"},
        "responseHandler": {"xml_location": "/{%s}ResponseHandler"%NS_WCST11, "xml_type": "string", "kvp_key": "responseHandler", "kvp_type": "string"},
        "actions": {"xml_location":"/{%s}InputCoverages/{%s}Coverage"%(NS_WCST11,NS_WCST11),"xml_type":"element[]","kvp_key":"coverages","kvp_type":"string"},
        } 

    def _handleException(self, req, exception):

        logger.debug("WCS110: Transaction() - Exception Handler!") 

        # dump exception to the log file 
        logger.error( traceback.format_exc() ) 

        return Response( content=createXML_OWS11Exception(exception) , content_type="text/xml" , status=500 ) 
        

    def _processRequest(self, req ):

        logger.debug("WCS110: Transaction()") 

        # KVP encoding is not supported by WCS-T 
        if req.http_req.method.upper() == "GET" : 
            raise ExOperationNotSupported("transaction","Operation does not support KVP encoding!")  

        # parse request 
        req.decoder.setSchema( self.PARAM_SCHEMA ) 

        # get actions (requests) and context (working env.)
        actions = map( parseCoverageXML , req.decoder.getValue('actions') ) 
        context = contextCreate( req.decoder.getValue('requestId') , req.decoder.getValue('responseHandler') )  

        try: 

            # execute transaction 
            response = wcst11Transaction( actions , context )

        except : #FAILURE 

            # discard permanent and temporary storage 
            contextDiscardFailure( context )
            raise 

        else : # SUCCESS 

            # clean-up TMP space of a synchronous operation 
            if not context['isAsync'] : 
                contextDiscardSuccess( context ) 
            # no TMP clean-up for asynnchronous operation 
            else : 
                contextDiscardAsync( context ) 

        # prepare the response 
        return Response( content=response , content_type="text/xml" , status=200 )  


WCS11TransactionHandlerImplementation = OperationHandlerInterface.implement(WCS11TransactionHandler)
