#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   WCS 1.1.x Transaction extension operation - implementation 
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
import os.path
import traceback

import logging
import shutil

try:    import cPickle as pickle 
except: import pickle 

from eopParse import eop20GetID, eop20SetID
from wcstCommon import PROCESS_CLASS
from wcstCommon import ACTIONS 
from wcstUtils import getNewCoverageID, downloadReference
from wcstUtils import timeStampUTC
from wcstUtils import responseUpload, saveToFile
from wcst11Exception import ExInvalidURI, ExServerBusy
from wcst11Exception import createXML_OWS11Exception

from wcst11Context import contextDiscardSuccess, contextDiscardFailure, contextDiscardAsync

#-------------------------------------------------------------------------------
# actions 

from wcst11ActionAdd import wcst11ActionAdd
from wcst11ActionDelete import wcst11ActionDelete
from wcst11ActionUpdateAll import wcst11ActionUpdateAll
from wcst11ActionUpdateMetadata import wcst11ActionUpdateMetadata
from wcst11ActionUpdateDataPart import wcst11ActionUpdateDataPart

ACTION = { 
    "Add"            : wcst11ActionAdd, 
    "Delete"         : wcst11ActionDelete,
    "UpdateAll"      : wcst11ActionUpdateAll,
    "UpdateMetadata" : wcst11ActionUpdateMetadata,
    "UpdateDataPart" : wcst11ActionUpdateDataPart } 

#-------------------------------------------------------------------------------

import eoxserver 

from eoxserver.resources.coverages.managers import RectifiedDatasetManager
from eoxserver.resources.processes.tracker import QueueFull, registerTaskType, enqueueTask
from eoxserver.core.system import System

settings = __import__( os.environ.get("DJANGO_SETTINGS_MODULE","settings") )  


# TODO: implement proper logging for this module

#===============================================================================

ASYNC_TIMEOUT= 60*60 # [s] time to restart zombie async tasks (be sure it is large enough)
ASYNC_HANDLER='eoxserver.services.ows.wcst.wcst11Transaction.wcst11AsynchronousTransction' 

#===============================================================================

ALLOWED_ACTIONS=None 

def getAllowedActions() :

    global ALLOWED_ACTIONS

    if ( ALLOWED_ACTIONS is not None ) : return ALLOWED_ACTIONS

    ACTIONS_UPPER = map( lambda s : s.upper() , ACTIONS )
    ACTIONS_U2N = dict( zip( ACTIONS_UPPER , ACTIONS ) ) 

    # unpack the allowed actions 
    conf = System.getConfig()
    tmp  = conf.getConfigValue("services.ows.wcst11","allowed_actions")
    tmp  = map( lambda s : s.strip().upper() , tmp.split(",") )
    tmp  = filter( lambda s : s in ACTIONS_UPPER , tmp ) 
    tmp  = map( lambda s : ACTIONS_U2N[s] , tmp ) 

    ALLOWED_ACTIONS = set( tmp ) 

    # always allow Add action  
    #ALLOWED_ACTIONS.add( "Add" ) 

    return ALLOWED_ACTIONS 

#===============================================================================

def wcst11Transaction( actions , context ) : 
    """ WCS-T 1.1 Transaction operation """ 

    # log verbose request summary 
    logging.debug( requestSummary( actions , context ) ) 

    if context['isAsync'] : 
    
        # asynchronous operation  
        wcst11EnqueueAsyncProc( actions , context )
        return createXML_WCSt11Ack( context ) 

    else : 
    
        # synchronous operation  
        return wcst11ActionDispatch( actions , context ) 

#-------------------------------------------------------------------------------
# ATP - new task enqueueing 

def wcst11EnqueueAsyncProc( actions , context ) : 
    """ WCS-T 1.1 Asynchronous Transaction --- task queue & worker daemon """

    try : 

        # register new task handler 
        registerTaskType( PROCESS_CLASS , ASYNC_HANDLER , ASYNC_TIMEOUT ) 

        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS , context['tid'] , (actions,context) ) 

    except QueueFull : 

        raise ExServerBusy

#-------------------------------------------------------------------------------
# APT - task handler - this subroutine is executed by the APT daemon 

def wcst11AsynchronousTransction( taskStatus , ( actions , context ) ) : 
    """ WCS-T 1.1 Asynchronous Transaction --- process class handler """

    try : 

        # perform transaction 
        response = wcst11ActionDispatch( actions , context )

        # clean up the context 
        contextDiscardSuccess( context ) 

        # change status  
        taskStatus.setSuccess() 

    except Exception as e :

        # change status 
        taskStatus.setFailure(unicode(e)) 

        # dump exception to the log file 
        logging.error( "[%s] %s"%( context['tid'] , traceback.format_exc() ) ) 

        # generate exception report 
        response = createXML_OWS11Exception( e ) 
        
        # clean up the context 
        contextDiscardFailure( context ) 

    # store response in DB 
    taskStatus.storeResponse( response ) 

    try : 

        # deliver the response to the response handler 
        logging.debug( "Uploading response to: %s " % context['responseHandler'] ) 

        responseUpload( context['responseHandler'] , response , "%s.xml"%context['requestId'] ) 

    except : 

        # change status 
        taskStatus.setFailure("Failed to deliver the transaction response!") 

        # dump exception to the log file 
        logging.error( "[%s] %s"%( context['tid'] , traceback.format_exc() ) ) 


#-------------------------------------------------------------------------------
#action dispatcher 

def wcst11ActionDispatch( actions , context ) : 
    """ WCS-T 1.1 Transaction action dispatcher - used by both synchronous and asynchronous mode """ 

    # check the number of action  

    if ( 1 > len(actions) ) : 
        raise Exception , "Request contains no action!"

    if ( 1 < len(actions) ) and (not context['mutipleActionsAllowed']) : 
        raise Exception , "Mutiple actions per single request are not supported!"

    # unpack the allowed actions 
    allowedActions = getAllowedActions()

    # iterate over the actions 
    coverageIDs = []


    for action in actions :

        actionName = action['Action'] 

        if actionName not in allowedActions : 
            raise Exception , "Action '%s' is not allowed!" % actionName 

        if actionName not in ACTION : 
            raise Exception , "Unsupported action '%s'!" % actionName

        coverageIDs.append( ACTION[actionName]( action , context ) )

    return createXML_WCSt11TResponse( coverageIDs , context )

#===============================================================================
# XML generators 

#-------------------------------------------------------------------------------
# create response XML 

def createXML_WCSt11TResponse( coverageIDs , context ) : 
    """ create WCSt 1.1 TransactionResponse XML document """ 

    xml = [] 
    xml.append( u'<?xml version="1.0" encoding="utf-8"?>\n' ) 
    xml.append( u'<TransactionResponse xmlns="http://www.opengis.net/wcs/1.1/wcst"' )
    xml.append( u' xmlns:ows="http://www.opengis.net/ows/1.1"' )
    xml.append( u' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' )
    xml.append( u' xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst ' ) 
    xml.append( u' http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">\n' ) 
    xml.append( u'<RequestId>%s</RequestId>\n' % context['requestId'] )
    for cid in coverageIDs :
        xml.append( u'<ows:Identifier>%s</ows:Identifier>\n' % cid )
    xml.append( u'</TransactionResponse>\n' ) 

    return ( u"".join(xml) ).encode("UTF-8")

#-------------------------------------------------------------------------------
# create response XML 

def createXML_WCSt11Ack( context ) : 
    """ create WCSt 1.1 Acknowledgement XML document """ 

    xml = [] 
    xml.append( u'<?xml version="1.0" encoding="utf-8"?>\n' ) 
    xml.append( u'<Acknowledgement xmlns="http://www.opengis.net/wcs/1.1/wcst"' )
    xml.append( u' xmlns:ows="http://www.opengis.net/ows/1.1"' )
    xml.append( u' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' )
    xml.append( u' xsi:schemaLocation="http://www.opengis.net/wcs/1.1/wcst ' ) 
    xml.append( u' http://schemas.opengis.net/wcst/1.1/wcstTransaction.xsd">\n' ) 
    xml.append( u'<TimeStamp>%s</TimeStamp>\n' % timeStampUTC() )
    xml.append( u'<RequestId>%s</RequestId>\n' % context['requestId'] )
    xml.append( u'</Acknowledgement>\n' ) 

    return ( u"".join(xml) ).encode("UTF-8")

#===============================================================================
# debuging tools 

def requestSummary( actions , context ) : 
    """ request summary used for debuging purposes """ 
    r  = "WCST Request Summary:\n" 
    r += "\t\tMode:            \t%s\n" % ( ("SYNC.","ASYNC.")[context['isAsync']]  ) 
    r += "\t\tRequestID:       \t%s\n" % context['requestId']
    r += "\t\tTransactionID    \t%s\t" % context['tid'] 
    r += "\t\tResponseHandler: \t%s\n" % context['responseHandler'] 
    r += "\t\tPermanent Storage:\t%s\n" % context['pathPerm']
    r += "\t\tTemporary Storage:\t%s\n" % context['pathTemp']
    r += "\t\tInputs\n" 
    for i,item in enumerate( actions ) : 
        r += "\t\t #%i\n" % ( i ) 
        r += "\t\t\tAction:     \t %s \n" % str( item["Action"] ) 
        r += "\t\t\tIdentifier: \t %s \n" % str( item["Identifier"] ) 
        r += "\t\t\tTitle:      \t %s \n" % str( item["Title"] ) 
        r += "\t\t\tAbstract:   \t %s \n" % str( item["Abstract"] ) 
        r += "\t\t\tKeywords:\n"
        for ii in item["Keywords"] : 
            r += "\t\t\t\t %s \n" % str( ii ) 
        r += "\t\t\tReference:\n"
        for ii in item["Reference"] : r += "\t\t %s \n" % str( ii ) 
        r += "\t\t\tMetadata:\n"
        for ii in item["Metadata"] :  r += "\t\t %s \n" % str( ii ) 
    return r 

#===============================================================================
