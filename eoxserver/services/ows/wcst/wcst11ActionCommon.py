#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   WCS 1.1.x Transaction extension - commons used by the actions 
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

from eoxserver.resources.coverages.managers import CoverageIdManager
from eoxserver.resources.coverages.exceptions import CoverageIdReservedError, \
    CoverageIdReleaseError, CoverageIdInUseError


logger = logging.getLogger(__name__)

#-------------------------------------------------------------------------------

def reserveCoverageId( covIdManager , coverage_id , request_id , until=None ) : 
    logger.debug( "Reserving CID: %s " % coverage_id ) 
    try : 
        covIdManager.reserve( coverage_id , request_id , until ) 
    except ( CoverageIdReservedError , CoverageIdInUseError ) : 
        return False 
    return True 

def releaseCoverageId( covIdManager , coverage_id ) : 
    logger.debug( "Releasing CID: %s " % coverage_id ) 
    try : 
        covIdManager.release( coverage_id ) 
    except CoverageIdReleaseError : pass 
        
def releaseCoverageIds( covIdManager , cids ) : 
    for cid in set( cids ) : 
        releaseCoverageId( covIdManager , cid ) 

#-------------------------------------------------------------------------------

class ExActionFailed( Exception ) : pass 

#-------------------------------------------------------------------------------
# Hey folks! Since I have not found any convinient object I create my own one. 

class LocalPath(object) : 
    def __init__( self , path ) : self.path = os.path.abspath(path) 
    def getType(self) : return "local"
    def open(self,mode="r") : return file(self.path,mode) ;  

# ==============================================================================
# XML generator

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
