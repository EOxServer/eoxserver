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
import subprocess 

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
from extractGeoTiffFootprint import extractGeoTiffFootprint

#-------------------------------------------------------------------------------

import eoxserver 

from eoxserver.resources.coverages.covmgrs import RectifiedDatasetManager
from eoxserver.resources.processes.tracker import QueueFull, registerTaskType, enqueueTask
from eoxserver.core.system import System

settings = __import__( os.environ.get("DJANGO_SETTINGS_MODULE","settings") )  

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

        # enqueue task for execution 
        enqueueTask( PROCESS_CLASS , context['tid'] , (actions,context) ) 

    except QueueFull : 

        raise ExServerBusy

#-------------------------------------------------------------------------------
# APT - task hadler - this subroutine is executed by the APT daemon 

# register new task handler 
registerTaskType( PROCESS_CLASS , ASYNC_HANDLER , ASYNC_TIMEOUT ) 

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

        actionName = str( action['Action'] ).strip()

        if actionName not in allowedActions : 
            raise Exception , "Action '%s' is not allowed!" % actionName 

        if ( "Add" == actionName ) : 
            coverageIDs.append( wcst11ActionAdd( action , context ) )
        elif ( "Delete" == actionName ) : 
            coverageIDs.append( wcst11ActionDelete( action , context ) )
        elif ( "UpdateAll" == actionName ) : 
            coverageIDs.append( wcst11ActionUpdateAll( action , context ) )
        elif ( "UpdateMetadata" == actionName ) : 
            coverageIDs.append( wcst11ActionUpdateMetadata( action , context ) )
        # uncomment if you decide to imlpement 
        #elif ( "UpdateDataPart" == actionName ) : 
        #    coverageIDs.append( wcst11ActionUpdateDataPart( action , context ) )

        else : 
            raise Exception , "Unsupported action '%s'!" % actionName

    return createXML_WCSt11TResponse( coverageIDs , context )

#===============================================================================



# ACTION: DELETE 

def wcst11ActionDelete( action , context ) : 

    # extract and check the user provided coverage ID ... 

    coverageId , coverageType = checkExistingCoverageId( action["Identifier"] , action["Action"] ) 

    # delete the coverage 

    msg = "WCSt11:%s: Action not implemented!" % action["Action"]
    logging.error( msg ) 
    raise Exception , msg 

    return coverageId


# ACTION: UPDATE METADATA 

def wcst11ActionUpdateMetadata( action , context ) : 

    # extract and check the user provided coverage ID ... 

    coverageId , coverageType = checkExistingCoverageId( action["Identifier"] , action["Action"] ) 

    # update coverage's metadata  

    msg = "WCSt11:%s: Action not implemented!" % action["Action"]
    logging.error( msg ) 
    raise Exception , msg 

    return coverageId


# ACTION: UPDATE ALL

def wcst11ActionUpdateAll( action , context ) : 

    # extract and check the user provided coverage ID ... 

    coverageId , coverageType = checkExistingCoverageId( action["Identifier"] , action["Action"] ) 

    # update coverage's metadata  

    msg = "WCSt11:%s: Action not implemented!" % action["Action"]
    logging.error( msg ) 
    raise Exception , msg 

    return coverageId


# ACTION: ADD 

def wcst11ActionAdd( action , context , maxAttempts = 3 ) : 
    """ WCS-T 1.1 Transaction - action handler """ 

    cid_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
    eom_reader  = System.getRegistry().bind("resources.coverages.metadata.XMLEOMetadataFileReader") 

    # generate internal coverage ID (no relation to the one provided by the user, used to name the files) 

    for i in xrange( maxAttempts ) : 
        cid = getNewCoverageID()
        if not cid_factory.exists( obj_id = cid ) : break 
    else : 
        msg = "WCSt11:Add: Failed to generate an unique coverage ID!" 
        logging.error( msg ) 
        raise Exception , msg 

    # extract user provided coverage ID ... 
    # ... and try to use is as an unique coverage name 
    # If cannot be used as coverage name using internal CID instead.

    coverageId = action["Identifier"] 

    if ( not coverageId ) or ( cid_factory.exists( obj_id = coverageId ) ) : 
        coverageId = cid 
        
    # ------------------------------------------------------------------------------

    pixelData    = [] 
    covDescript  = [] 
    geoTransform = []  
    eopXML       = None 

    # download references 
    for i,r in enumerate(action["Reference"]): 

        basename = os.path.join( context['pathTemp'] , "%s_ref_%3.3i" % ( cid , i ) ) 

        logging.debug( "WCSt11: Reference: role: %s \t href: %s " % ( r['role'] , r['href'] ) ) 

        if r['role'] == "urn:ogc:def:role:WCS:1.1:Pixels" : 
            pixelData.append( wcst11DownloadReference( r['href'] , basename ) ) 
        elif r['role'] == "urn:ogc:def:role:WCS:1.1:CoverageDescription" : 
            pass
            #covDescript.append( wcst11DownloadReference( r['href'] , basename ) )
        elif r['role'] == "urn:ogc:def:role:WCS:1.1:GeoreferencingTransformation" : 
            pass
            #geoTransform.append( wcst11DownloadReference( r['href'] , basename ) )

    # -MP- NOTE: 
    # I REALLY do not know what to do with the CoverageDescription and GeoreferencingTransformation.
    # They are required by the WCS-T standard (mandatory references which are always supposed to be present)
    # but not by the EOxServer API at all. Therefore I decided to silently ignore their absence. 
    # If provided nice, if not they are not needed anayway.  

    # ------------------------------------------------------------------------------
    # download metadata 
    for i,r in enumerate(action["Metadata"]): 

        logging.debug( "WCSt11: Metadata: role: %s \t href: %s " % ( r['role'] , r['href'] ) ) 

        basename = os.path.join( context['pathTemp'] , "%s_md_%3.3i" % ( cid , i ) ) 

        if r['role'] == "http://www.opengis.net/eop/2.0/EarthObservation" : 
            eopXML = wcst11DownloadReference( r['href'] , basename ) 

    # ------------------------------------------------------------------------------
    # input data check - eopXML validation - TBD 

    # ------------------------------------------------------------------------------

    dstXMLfile =  os.path.join( context['pathPerm'] , "%s.xml" % cid )
    dstTIFfile =  os.path.join( context['pathPerm'] , "%s.tif" % cid )

    srcTIFfile = pixelData[0][0]
    srcXMLfile = os.path.join( context['pathTemp'] , "%s_md.xml" % cid ) 

    fid = file( srcXMLfile , "w" ) 

    if  eopXML is not None :

        logging.debug( "WCSt11: Using the existing EOP2.0 XML file: %s  " % eopXML[0] )

        eop20SetID( file(eopXML[0]) , fid , coverageId ) 

    else :     
        # prepare coverage insert 

        md_start     = timeStampUTC()
        md_stop      = md_start

        md_footprint = extractGeoTiffFootprint( srcTIFfile , repeatFirst = True )

        logging.debug( "WCSt11: Creating EOP2.0 XML file: %s" % srcXMLfile )

        fid.write( createXML_EOP20( coverageId , md_footprint , md_start , md_stop ) ) 

    fid.close() 

    # ------------------------------------------------------------------------------

    # move the files to the final destination 
    shutil.move( srcTIFfile , dstTIFfile )                          
    #shutil.move( srcXMLfile , dstXMLfile )                          

    # finally insert the data to the EOXServer 

    rdm = RectifiedDatasetManager() 

    #rdsync.create( coverageId , str( os.path.abspath( dstTIFfile ) ) ) 
    # range_type_name 
    # geo_metadata
    # eo_metadata
    # layer metadata: abstract, title, keywords

    # Hey folks! Since I have not found any convinient object I create my own one. 
    class LocalPath(object) : 
        def __init__( self , path ) : self.path = os.path.abspath(path) 
        def getType(self) : return "local"
        def open(self,mode="r") : return file(self.path,mode) ;  

    rdm.create( coverageId , 
            local_path = os.path.abspath( dstTIFfile ) ,
            range_type_name = "Grayscale" , 
            eo_metadata = eom_reader.readEOMetadata( LocalPath( srcXMLfile ) ) 
        ) 

    return coverageId

#-------------------------------------------------------------------------------

# utility - check whether coverage exists 

def checkExistingCoverageId( coverageId , actionID ) : 

    cid_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")

    # check whether the coverage exists - if not stop 

    if cid_factory.exists( obj_id = coverageId ) : 
        msg = "WCSt11:%s: Invalid coverage ID!" % actionID 
        logging.error( msg ) 
        raise Exception , msg 

    # determine the coverage type (model class - PlainCoverage, RectifiedDataset, ReferencedDatasets etc.) 

    coverageType = "N/A"

    return coverageId , coverageType

# utility - donwload reference throwing proper OWS exception

def wcst11DownloadReference( url , basename ) :

    try: 
        return downloadReference( url , basename )
    except Exception as e : 
        # keep track of the errors 
        logging.error( str(e) ) 
        raise ExInvalidURI( url ) 

#===============================================================================
# XML generators 

#   metadata 
def createXML_EOP20( covid , md_footprint , md_start , md_stop ) : 
    """ create baseline EOP 2.0 metadata XML document """ 

    xml = [] 
    xml.append( u'<?xml version="1.0" encoding="utf-8"?>\n' ) 
    xml.append( u'<eop:EarthObservation xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
    xml.append( u' xsi:schemaLocation="http://www.opengis.net/opt/2.0 ../xsd/opt.xsd"')
    xml.append( u' xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:gml="http://www.opengis.net/gml/3.2"') 
    xml.append( u' xmlns:eop="http://www.opengis.net/eop/2.0" xmlns:swe="http://www.opengis.net/swe/1.0"') 
    xml.append( u' xmlns:om="http://www.opengis.net/om/2.0" gml:id="eop_%s">\n' % covid ) 
    xml.append( u'<om:phenomenonTime><gml:TimePeriod gml:id="tp_%s">\n' % covid ) 
    xml.append( u'\t<gml:beginPosition>%s</gml:beginPosition>\n' % md_start ) 
    xml.append( u'\t<gml:endPosition>%s</gml:endPosition>\n' % md_stop ) 
    xml.append( u'</gml:TimePeriod></om:phenomenonTime>\n') 
    xml.append( u'<om:featureOfInterest><eop:Footprint gml:id="footprint_%s"><eop:multiExtentOf>\n' % covid ) 
    xml.append( u'<gml:MultiSurface gml:id="ms_%s" srsName="EPSG:4326"><gml:surfaceMember>\n' % covid ) 
    xml.append( u'\t<gml:Polygon gml:id="poly_%s"><gml:exterior><gml:LinearRing><gml:posList>\n' % covid ) 
    xml.append( md_footprint )  
    xml.append( u'</gml:posList></gml:LinearRing></gml:exterior></gml:Polygon></gml:surfaceMember>\n' ) 
    xml.append( u'</gml:MultiSurface></eop:multiExtentOf></eop:Footprint></om:featureOfInterest>\n' )
    xml.append( u'<eop:metaDataProperty><eop:EarthObservationMetaData>\n' ) 
    xml.append( u'\t<eop:identifier>%s</eop:identifier>\n' % covid ) 
    xml.append( u'</eop:EarthObservationMetaData></eop:metaDataProperty></eop:EarthObservation>\n' ) 

    return ( u"".join(xml) ).encode("UTF-8")

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
    xml.append( u' http://www.opengis.net/wcs/1.1/wcst/wcstTransaction.xsd">\n' ) 
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
    xml.append( u' http://www.opengis.net/wcs/1.1/wcst/wcstTransaction.xsd">\n' ) 
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
