#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   WCS-t context handling 
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
import shutil

import logging
#import traceback 

from wcstUtils import getNewRequestID
from wcstUtils import checkResponseHandler

#-------------------------------------------------------------------------------

from eoxserver.core.system import System

#-------------------------------------------------------------------------------


logger = logging.getLogger(__name__) #  TODO: set up logging for this module

def contextCreate( requestId = None , reponseHandler = None , maxAttempts = 3 ) : 

    conf = System.getConfig()

    log_file   = conf.getConfigValue("core.system","logging_filename") 
    log_level  = conf.getConfigValue("core.system","logging_level" ) 
    log_format = conf.getConfigValue("core.system","logging_format" ) 

    path_temp0 = conf.getConfigValue("services.ows.wcst11","path_wcst_temp") 
    path_perm0 = conf.getConfigValue("services.ows.wcst11","path_wcst_perm") 
    muti_act   = ( "True" == conf.getConfigValue("services.ows.wcst11","allow_multiple_actions") ) 

    context = {} 
    context['responseHandler'] = checkResponseHandler( reponseHandler ) 
    context['isAsync']         = reponseHandler is not None 
    context['mutipleActionsAllowed'] = muti_act
    context['loggingFilename'] = log_file 
    context['loggingLevel']    = log_level
    context['loggingFormat']   = log_format 

    logging.debug("WCSt11: loggingFilename %s "  % str(log_file) )
    logging.debug("WCSt11: loggingformat %s "  % str(log_format) )
    logging.debug("WCSt11: loggingLevel %s "  % str(log_level) )

    for i in xrange( maxAttempts ) :
    
        # internal transaction ID (used as request ID if not provided by the client) 
        tid = getNewRequestID() 

        path_temp = os.path.join( path_temp0 , tid ) 
        path_perm = os.path.join( path_perm0 , tid ) 

        # check if directories do not exist 
        try : 
            os.mkdir( path_temp )
        except Exception as e : 
            logging.warning( "Failed to create the temporary storage directory! %s" % str(path_temp) ) 
            continue # try another process ID

        try : 
            os.mkdir( path_perm )
        except Exception as e : 
            os.rmdir( path_temp ) 
            logging.warning( "Failed to create the permanent storage directory! %s" % str(path_perm) ) 
            continue # try another process ID

        # store the values 
        context['requestId'] = tid if ( requestId is None ) else requestId
        context['tid']       = tid 
        context['pathTemp']  = path_temp
        context['pathPerm']  = path_perm

        # store the current working directory
        context['pathOrig']  = os.getcwd() 

        # change to the temporary storage dir 
        os.chdir( path_temp ) 

        #---------------------------------------------

        logging.debug("WCSt11: Request ID:        %s %s" % ( tid , "" if ( requestId is None ) else "(%s)" %(requestId) ) )
        logging.debug("WCSt11: Permanent Storage:  %s" % path_perm )
        logging.debug("WCSt11: Temporary Storage:  %s" % path_temp )

        break 

    else : 
        msg = "WCSt11: Failed to create an unique WCS transaction's context!" 
        logging.error( msg ) 
        raise OSError , msg 

    return context 

#-------------------------------------------------------------------------------

def _contextDiscardCommon( context ) : 
    # restore the origina working directory 
    os.chdir( context['pathOrig'] ) 
    # ------------------------------

def _contextDiscardPermIfEmpty( context ) :
    try:
        os.rmdir( context["pathPerm"] )
        logging.debug("WCSt11: Discarding empty permanent storage: %s" % context["pathPerm"] )
    except OSError :
        logging.debug("WCSt11: Keeping non-empty permanent storage: %s" % context["pathPerm"] )

def _contextDiscardTemp( context ) :
    logging.debug("WCSt11: Discarding temporary storage: %s" % context["pathTemp"] )
    shutil.rmtree( context["pathTemp"] )

def _contextDiscardPerm( context ) :
    logging.debug("WCSt11: Discarding permanent storage: %s" % context["pathPerm"] )
    shutil.rmtree( context["pathPerm"] )

#-------------------------------------------------------------------------------

def contextDiscardAsync( context ) : 
    _contextDiscardCommon( context ) 

def contextDiscardSuccess( context ) : 
    _contextDiscardCommon( context ) 
    _contextDiscardTemp( context )
    _contextDiscardPermIfEmpty( context )

def contextDiscardFailure( context ) : 
    _contextDiscardCommon( context ) 
    _contextDiscardTemp( context )
    _contextDiscardPerm( context )

