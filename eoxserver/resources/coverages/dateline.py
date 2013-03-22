#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from django.contrib.gis.geos import Polygon


EXTENT_EPSG_4326 = Polygon.from_bbox((-180, -90, 180, 90))
EXTENT_EPSG_4326.srid = 4326

CRS_WIDTH = {
    3857: -20037508.3428 * 2,
    4326: 360.0
}

def extent_crosses_dateline(extent, srid=4326):
    """ Returns `True` if a dataset crosses the dateline border. """
    
    poly = Polygon.from_bbox(extent)
    poly.srid = srid
    
    poly.transform(EXTENT_EPSG_4326.srs)
    
    if not EXTENT_EPSG_4326.contains(poly):
        return True
    
    return False

    
def wrap_extent_around_dateline(extent, srid=4326):
    """ Wraps the given extent around the dateline. Currently only works for 
    EPSG:4326 and EPSG:3857"""
    
    try:
        return (extent[0] - CRS_WIDTH[srid], extent[1], 
                extent[2] - CRS_WIDTH[srid], extent[3])
    except KeyError:
        raise NotImplemented("Dateline wrapping is not implemented for SRID "
                             "%d. Supported are SRIDs %s." % 
                             (srid, ", ".join(CRS_WIDTH.keys())))
