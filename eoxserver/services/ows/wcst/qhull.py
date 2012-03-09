#-----------------------------------------------------------------------
# $Id$
#
# Description: 
#
#   convex hull calculation - simple quick hull algorithm 
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

from numpy import argmin, argmax 
from numpy import dot,array
from numpy import logical_and as aand
from numpy import abs as aabs
from math import sqrt 

# --------------------------------
# analytical geometry 

def _getLineCoef( data , clock_wise = True) :
    """ calculate coeficients (a,b,c,dx,dy,x0,y0) of equations of line 

            0 = a*x + b*y + c

            x(t) = dx * t + x0 
            y(t) = dy * t + y0 

        the (a,b) is the normal vecor of the line (unit lenght) 
    """

    # select direction of the normal 
    d  = (-1,+1)[clock_wise]  

    # tangent 
    dx = data[1,0] - data[0,0] 
    dy = data[1,1] - data[0,1] 

    x0 = data[0,0] ; y0 = data[0,1] 

    dd = sqrt( dx*dx + dy*dy )

    f  = d/dd if ( dd > 0 ) else 0 

    # normal vector 
    a = -f * dy 
    b = +f * dx
    c = -( a*x0 + b*y0 ) 

    return ( a , b , c , dx , dy , x0 , y0 )


def _evalPoint2LineDist( data , (a,b,c,dx,dy,x0,y0) ) :
    """ Evaluates distance of points from line given by the 
        coeficients (a,b,c,dx,dy,x0,y0). The distance is calculated as 

            d(x,y) = a*x + b*y + c

        Vector (a,b) must be unit normal vector of the line!

    """
    return c + a*data[:,0] + b*data[:,1]



def _evalPoint2LineDistAndParmam( data , coef ) :
    """ Evaluates distance of a point from line and parameter of 
        the closest line's ponit (projection) .
        The line is given by the coeficients (a,b,c,dx,dy,x0,y0). 
        The distance is calculated as 

            d(x,y) = a*x + b*y + c

        The position of closest line's point is avaluated as 

            xc(x,y) = x - d(x,y) * a 
            yc(x,y) = y - d(x,y) * b 
        
        and finally the parameter t is evauated as 
        
            if ( abs(dx) > abs(dy) ) : 
                t(x,y) = ( xc(x,y) - x0 ) / dx 
            else :
                t(x,y) = ( yc(x,y) - y0 ) / dy 

        Note: Vector (a,b) must be unit normal vector of the line!

    """
    a,b,c,dx,dy,x0,y0 = coef 

    dist = _evalPoint2LineDist( data , coef ) 

    #proj = data - dot( dist.reshape((dist.size,1)) , array([[a,b]]) )

    if abs(dx) > abs(dy) : 
        parm = (1/dx) * ( data[:,0] - dist*a - x0 ) 
    else : 
        parm = (1/dy) * ( data[:,1] - dist*b - y0 ) 

    return ( dist , parm ) 

# --------------------------------
# qhull operations 

def _expand( data , sgm , I , eps = 1e-6 , clock_wise = True ) : 
    """ expand hull 
        find a point of max.distance from the single polygone boundary 
        (line segment) and return its index 

        eps is the absolute tolerance to round-off errors  
    """
    if len(I) < 1 : return None 

    # distance from the line segment 
    dist = _evalPoint2LineDist( data[I] ,_getLineCoef( data[sgm] , clock_wise ) )

    # find the max. distance point 
    idx = argmax( dist ) 

    # return point index if outside the convex polygon
    return None if ( dist[idx] < eps ) else I[idx] 


def _extend( data , sgm , I , eps = 1e-6 , clock_wise = True ) : 
    """
        extend hull 
        find a point closely located to the boundary segement but not part 
        of the footprint polygon

        eps is the absolute tolerance of the distance below which the 
        point is considered part of the bounary 
    """
    if len(I) < 1 : return None 

    # distance from the line segment and parametric projection of the point 
    # to the boundary segement 
    dist , parm = _evalPoint2LineDistAndParmam( data[I] ,_getLineCoef( data[sgm] , clock_wise ) ) 

    # select points below the threshold and projected on the boundary segment 
    idx = aand( aabs( dist ) < eps , aand( parm >= 0 , parm <= 1 ) ).nonzero()[0] 

    return None if ( len(idx) < 1 ) else I[idx[0]] 

# --------------------------------

def chull2D_qhull( data , eps = 1e-6 , clock_wise = True ) : 
    """ 
        2D convex hull calculation using slightly modified quick hull algorithm 
       
        data    - Nx2 numpy array - set of 2D points 
        eps     - the absolute tolerance to round-off errors  
        clock_wise - boolean flag selecting clock-wise (True default) 
                     counter-clock-wise orientation of the convex hull 
    """

    if len(data) == 0 : return array([]) 

    I = range( data.shape[0] ) 

    # ------------------------------------
    # initialization - find the extremes 

    i0 = argmin(data[:,0])
    i1 = argmax(data[:,0])

    if i0 != i1 : 
        H = [ i0 , i1 ] ; I.remove( i0 ) ; I.remove( i1 ) 
    else : # i0 == i1 
        j0 = argmin(data[:,1])
        j1 = argmax(data[:,1])
    
        if j0 != j1 : 
            H = [ j0 , j1 ] ; I.remove( j0 ) ; I.remove( j1 ) 
        elif i0 != j0 :  
            H = [ i0 , j0 ] ; I.remove( i0 ) ; I.remove( j0 ) 
        else : 
            return [ i0 ] 

    # ------------------------------------
    # split the segments 

    nnew = 2 ; 
    while nnew > 0 : 
        nnew = 0 
        H1 = [] 
        for i in xrange(len(H)) : 
            j = (i+1)%len(H) 
            H1.append( H[i] ) 
            idx = _expand( data , [ H[i] , H[j] ] , I , eps , clock_wise ) 
            if idx : 
                nnew += 1 
                H1.append( idx ) 
                I.remove( idx ) 
        H = H1 

    # ------------------------------------
    # add the very border points 

    nnew = len(H)  
    while nnew > 0 : 
        nnew = 0 
        H1 = [] 
        for i in xrange(len(H)) : 
            j = (i+1)%len(H) 
            H1.append( H[i] ) 
            idx = _extend( data , [ H[i] , H[j] ] , I , eps , clock_wise ) 
            if idx : 
                nnew += 1 
                H1.append( idx ) 
                I.remove( idx ) 
        H = H1 

    # ------------------------------------

    return H 

