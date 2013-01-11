#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   WCS 1.1.x Transaction extension -  implementation of the Delete action  
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

from wcst11ActionCommon import ExActionFailed

#-------------------------------------------------------------------------------

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.managers import RectifiedDatasetManager
from eoxserver.resources.coverages.managers import ReferenceableDatasetManager

from eoxserver.resources.coverages.models import RectifiedDatasetRecord
from eoxserver.resources.coverages.models import ReferenceableDatasetRecord

#-------------------------------------------------------------------------------


logger = logging.getLogger(__name__)

# ACTION: DELETE 
#
# NOTE: WCS-T Delete action, as currently implemented, can remove only those 
#       coverages which have been inserted via the WCS-T Add action. 
#

def wcst11ActionDelete( action , context ) : 

    aname = action["Action"]
    logger.debug( "WCSt11:%s: START" % aname ) 

    # extract permanet storage 
    pathPerm = os.path.abspath( "%s/.."%context['pathPerm'] ) 

    # extract user provided CID 
    coverageId = action["Identifier"] 

    if not coverageId: raise ExActionFailed , "WCSt11:%s: Missing the required coverage identifier!" % aname 

    # check the covergae type 
    coverageType = CoverageIdManager().getCoverageType( coverageId )

    if not coverageType: raise ExActionFailed , "WCSt11:%s: Invalid coverage identifier! Identifier=%s" % ( aname , repr( coverageId ) )  
    
    # process the supproted coverage types 

    if coverageType == "RectifiedDataset":
        cls = RectifiedDatasetRecord
        mng = RectifiedDatasetManager() 

    elif coverageType == "ReferenceableDataset": 
        cls = ReferenceableDatasetRecord
        mng = ReferenceableDatasetManager()  

    else : # unsupproted coverage types 
        raise ExActionFailed , "WCSt11:%s: Unsupported coverage type! Type=%s ; Identifier=%s" % ( aname , repr(coverageType) , repr( coverageId ) )  

    # check the location 

    obj = cls.objects.get( coverage_id = coverageId ) 
    pck = obj.data_package

    if pck.data_package_type == 'local' : 

        logger.debug( dir( pck.localdatapackage ) ) 

        lpath = pck.localdatapackage.data_location.path
        mpath = pck.localdatapackage.metadata_location.path

        # let only the covergas inserted via the WCS-T to be deletable via this interface 
        if not ( lpath.startswith( pathPerm ) and mpath.startswith( pathPerm ) ) : 
            raise ExActionFailed , "WCSt11:%s: No permission to remove the coverage! Identifier=%s" % ( aname , repr(coverageId) )  

        # delete the coverage 
        logger.info( "WCSt11:%s: Removing coverage: %s " % ( aname , coverageId ) ) 
        mng.delete( coverageId ) 

        # delete the coverage data 
        for f in ( lpath , mpath ) : 
            try : 
                logger.info( "WCSt11:%s: Removing file: %s " % ( aname , f ) )
                os.remove( f ) 
            except Exception as e :
                logger.warn( "WCSt11:%s: Failed to remove file! path=%s " % ( aname , f ) ) 
                logger.warn( "WCSt11:%s: Reason: %s %s" % ( aname , str(type(e)) , str(e) ) )  

        # delete directories if empty 
        for d in set( ( os.path.dirname( lpath ) , os.path.dirname( mpath ) ) ) : 
            try : 
                logger.info( "WCSt11:%s: Removing directory: %s " % ( aname , d ) )
                os.rmdir( d ) 
            except Exception as e :
                logger.warn( "WCSt11:%s: Failed to remove directory! path=%s " % ( aname , d ) ) 
                logger.warn( "WCSt11:%s: Reason: %s %s" % ( aname , str(type(e)) , str(e) ) )

    return coverageId
