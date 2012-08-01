#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

""" This module contains definition of the auxiliary 2D bounding box class. """

class BBox:
    """ Simple 2D bounding box primitive. 
    
        Possible initializations: 

         - size and zerro offset ``BBox(sx,sy)``
         - size and offset (lower corner) ``BBox(sx,sy,ox,oy)``  
         - lower and upper corners ``BBox(None,None,ox,oy,ux,uy)``

         BBox class supports following operators: 

            &   - area intersection (maximum common area)
            |   - area expansion (minimum area contaning both boxes)
            +   - offset translation (adding vector to current value)
            -   - offset translation (substracting vector from current value)
    """ 

    # upper corrner                                     
    ox = property( lambda s : s.__ox , doc="x offset/lower corner (RO)" )                                     
    oy = property( lambda s : s.__oy , doc="y offset/lower corner (RO)" )                                     
    sx = property( lambda s : s.__sx , doc="x size (RO)" )                                     
    sy = property( lambda s : s.__sy , doc="y size (RO)" )                                     
    ux = property( lambda s : s.__ox + s.__sx , doc="x upper corner (RO)" )                                     
    uy = property( lambda s : s.__oy + s.__sy , doc="y upper corner (RO)" )                                     
                                                                                
    # extent                                                                    
    ext  = property( lambda s: s.__sx * s.__sy , doc="extent/box area (RO)" )
    off  = property( lambda s: (s.__ox,s.__oy) , doc="offset tuple (RO)")
    cup  = property( lambda s: (s.ux,s.uy) , doc="upper corner tuple (RO)" )
    size = property( lambda s: (s.__sx,s.__sy) , doc="size tuple (RO)" )

    def as_tuple( self ) : 
        """ Get bbounding box as (sx.sy,ox,oy) tuple """ 
        return ( self.__sx , self.__sy , self.__ox, self.__oy ) 

    def __str__( self ) : 
        return "BBox%s"%str(self.as_tuple()) 

    def __init__( self , sx=None, sy=None, ox=0, oy=0, ux=0, uy=0 ) : 

        self.__ox = ox 
        self.__oy = oy 
        self.__sx = max( 0 , ( ux - ox ) if sx is None else sx ) 
        self.__sy = max( 0 , ( uy - oy ) if sy is None else sy ) 

    # area operators 
    def __and__( self , other ) : 
        """ operator - intersection """
        return BBox( ox=max(self.ox,other.ox), oy=max(self.oy,other.oy),       
                     ux=min(self.ux,other.ux), uy=min(self.uy,other.uy) )    

    def __or__( self , other ) : 
        """ operator - expansion """
        return BBox( ox=min(self.ox,other.ox), oy=min(self.oy,other.oy),       
                     ux=max(self.ux,other.ux), uy=max(self.uy,other.uy) )    

    # box operator - offset translation                                                
    def __add__( self , (ox,oy) ) :
        """ operator - offset translation """
        return BBox( self.sx, self.sy, self.ox + ox, self.oy + oy )

    def __sub__( self , (ox,oy) ) :
        """ operator - offset translation """
        return BBox( self.sx, self.sy, self.ox - ox, self.oy - oy )
