#!/usr/bin/env python 
#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
# GDAL based GeoTIFF utilities
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

import sys
import os.path 
from numpy import linalg 
from numpy import array
from numpy import dot 
from numpy import argmin, argmax 

from qhull import chull2D_qhull

from eoxserver.contrib import osr, gdal

#-------------------------------------------------------------------------------

class GeoTransform(object) : 

    def __init__( self , gt ) : 
        
        self.xy = array( (gt[0],gt[3]) , 'float64' ) 
        self.af = array( ((gt[2],gt[1]),(gt[5],gt[4])) , 'float64' ) 
        self.ab = linalg.inv( self.af ) 

    def rc2xy( self , rc ) : 
        rc = array( rc , 'float64' ) 
        xy = self.xy + dot( self.af , rc )  
        return xy 

    def xy2rc( self , xy ) : 
        xy = array( xy , 'float64' ) 
        rc = dot( self.ab , xy - self.xy )  
        return rc 

#-------------------------------------------------------------------------------

class OSRTransform( object ) : 

    def __init__( self , src , dst ) : 

        self.fwd = osr.CoordinateTransformation( src , dst )
        self.bwd = osr.CoordinateTransformation( dst , src )

    def src2dst( self , xy ) :
        return array( self.fwd.TransformPoint( xy[0] , xy[1] ) , 'float64' ) 

    def dst2src( self , xy ) :
        return array( self.bwd.TransformPoint( xy[0] , xy[1] ) , 'float64' ) 

#-------------------------------------------------------------------------------

class GDalInfo( object ) : 
    """ this class holds the GDAL information of the rester file """

    def __init__( self , fname ) : 

        # get the dataset and its params
        gdal.AllRegister()
        ds = gdal.Open(fname)
    
        self.fileName = fname 
        self.driverName =  ds.GetDriver().LongName
        self.size       = (ds.RasterYSize,ds.RasterXSize,ds.RasterCount) 
        self.GCPCount   = ds.GetGCPCount() 
        self.GCPProjection = ds.GetGCPProjection()
        self.Projection = ds.GetProjection()
        self.ProjectionRef = ds.GetProjectionRef() 
        self.GeoTransform = ds.GetGeoTransform() 
        self.GCP         = ds.GetGCPs() 
        self.isRectified  = bool( self.Projection ) 
        self.isReferenceable = bool( self.GCPProjection) and ( self.GCPCount > 0 ) 


    def __str__( self ) : 

        a = [] 
        a.append( "GDalInfo:" ) 
        a.append( "\tFile:         \t %s" % str(self.fileName) ) 
        a.append( "\tDriver:       \t %s" % str(self.driverName) ) 
        a.append( "\tSize:         \t %s" % str( self.size ) )
        a.append( "\tNo.GCP        \t %s" % str( self.GCPCount ) )
        a.append( "\tProjectionRef:\t %s" % str( self.ProjectionRef  ) )
        a.append( "\tProjection:   \t %s" % str( self.Projection ) )
        a.append( "\tGeoTransform: \t %s" % str( self.GeoTransform ) )
        a.append( "\tGCP Projection:\t %s" % str( self.GCPProjection ) )
        a.append( "" ) 

        return "\n".join( a ) 

#-------------------------------------------------------------------------------

def getFootprint( info , **kvarg ) : 
    """ extract geotiff image footprint 
    
        info            - [instance of GDalInfo class] image descriptor  
        numberOfPoints  - [integer] number of points per single image size 
                          (20 by default, applicable to Rectified images only) 
        delimiter       - [string] separator delimiting the footprint coordinates (<space> by default) 
        repeatFirst     - [boolean] if True the first point is repeated as last one to close the loop
    """

    if info.isRectified : 
        return getFootprintRect( info , **kvarg )
    elif info.isReferenceable : 
        return getFootprintRef( info , **kvarg )

    return None 


def getFootprintRect( info , numberOfPoints = 20, delimiter = " " , repeatFirst = False ) : 
    """ extract geotiff image footprint of a Rectified image  
    
        info            - [instance of GDalInfo class] image descriptor  
        numberOfPoints  - [integer] number of points per single image size 
                          (20 by default) 
        delimiter       - [string] separator delimiting the footprint coordinates (<space> by default) 
        repeatFirst     - [boolean] if True the first point is repeated as last one to close the loop
    """

    # -----------------------------
    # projections conversion

    size = ( info.size[0] , info.size[1] ) 

    gt = GeoTransform( info.GeoTransform ) 

    cr_src = osr.SpatialReference() 
    cr_dst = osr.SpatialReference() 

    cr_src.ImportFromWkt( info.Projection ) 
    cr_dst.SetWellKnownGeogCS( "WGS84" ) 

    trn = OSRTransform(cr_src,cr_dst) 

    # -----------------------------
    # extract footprint (clockwise)

    foot = [] 

    # top (L2R)
    for i  in xrange( 0 , numberOfPoints ) : foot.append( tuple( trn.src2dst(gt.rc2xy((0,size[1]*float(i)/float(numberOfPoints))))[:2] ) ) 
    # right (T2B) 
    for i  in xrange( 0 , numberOfPoints ) : foot.append( tuple( trn.src2dst(gt.rc2xy((size[0]*float(i)/float(numberOfPoints),size[1])))[:2] ) ) 
    # bottom (R2L) 
    for i  in xrange( 0 , numberOfPoints ) : foot.append( tuple( trn.src2dst(gt.rc2xy((size[0],size[1]*float(numberOfPoints-i)/float(numberOfPoints))))[:2] ) ) 
    # left (B2T) 
    for i  in xrange( 0 , numberOfPoints ) : foot.append( tuple( trn.src2dst(gt.rc2xy((size[0]*float(numberOfPoints-i)/float(numberOfPoints),0)))[:2] ) ) 

    if ( repeatFirst ) : foot.append( foot[0] ) 
    
    # things to be done 
    # 1) POLAR PROJECTIONS 
    # 2) NON-POLAR FOOTPRINT CROSSING +/-180 MERIDIAN 

    return delimiter.join(map( lambda x : "%.6f%s%.6f"%(x[0],delimiter,x[1]) , foot ))

#-------------------------------------------------------------------------------

def getFootprintRef( info , numberOfPoints = 20, delimiter = " " , repeatFirst = False ) : 
    """ extract geotiff image footprint of a Referenceableimage  
    
        info            - [instance of GDalInfo class] image descriptor  
        numberOfPoints  - [integer] dummy placeholder - not used (20 by default) 
        delimiter       - [string] separator delimiting the footprint coordinates (<space> by default) 
        repeatFirst     - [boolean] if True the first point is repeated as last one to close the loop
    """
    # NOTE: numberOfPoints parameter is ignored 

    D = array( map( lambda gcp : ( gcp.GCPLine , gcp.GCPPixel ) , info.GCP ) ) 

    H = chull2D_qhull( D , eps = 1e-3 , clock_wise = True ) 

    if ( repeatFirst ) : H.append( H[0] ) 

    # things to be done 
    # 1) POLAR PROJECTIONS 
    # 2) NON-POLAR FOOTPRINT CROSSING +/-180 MERIDIAN 

    return delimiter.join(map( lambda i : "%.6f%s%.6f"%(info.GCP[i].GCPX,delimiter,info.GCP[i].GCPY) , H ))

#-------------------------------------------------------------------------------

# simple test 
if __name__ == "__main__" : 
        
    fname = os.path.abspath( sys.argv[1] ) 

    info = GDalInfo( fname ) 

    #print info 
    #print "WGS84 Footprint: " 
    print getFootprint( info ) 
