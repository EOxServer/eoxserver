# -----------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
# -----------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies of this Software or works derived from this Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# -----------------------------------------------------------------------------

# from django.contrib.gis.geos import Polygon

from osgeo import ogr
from osgeo import osr

from eoxserver.resources.coverages.crss import crs_bounds


EXTENT_EPSG_4326 = ogr.CreateGeometryFromWkt(
    'POLYGON ((-180 -90, -180 90, 180 90, 180 -90, -180 -90))'
)
SR_EPSG_4326 = osr.SpatialReference()
SR_EPSG_4326.ImportFromEPSG(4326)
try:
    SR_EPSG_4326.SetAxisMappingStrategy(0)
except AttributeError:
    # earlier version did not have this behavior
    pass


CRS_WIDTH = {
    3857: -20037508.3428 * 2,
    4326: 360.0
}


def extent_crosses_dateline(extent, srid=4326):
    """ Returns ``True`` if a dataset crosses the dateline border. """

    poly = ogr.CreateGeometryFromWkt(
        'POLYGON (({minx} {miny}, {minx} {maxy}, {maxx} {maxy}, '
        '{maxx} {miny}, {minx} {miny}))'.format(
            minx=extent[0],
            miny=extent[1],
            maxx=extent[2],
            maxy=extent[3],
        )
    )

    sr = osr.SpatialReference()
    sr.ImportFromEPSG(srid)
    try:
        sr.SetAxisMappingStrategy(0)
    except AttributeError:
        # earlier version did not have this behavior
        pass

    if not sr.IsSame(SR_EPSG_4326):
        transform = osr.CoordinateTransformation(sr, SR_EPSG_4326)
        poly.Transform(transform)

    if not EXTENT_EPSG_4326.Contains(poly):
        return True

    return False


def wrap_extent_around_dateline(extent, srid=4326):
    """ Wraps the given extent around the dateline. Currently only works for
    EPSG:4326 and EPSG:3857"""

    try:
        return (extent[0] - CRS_WIDTH[srid], extent[1],
                extent[2] - CRS_WIDTH[srid], extent[3])
    except KeyError:
        raise NotImplementedError(
            "Dateline wrapping is not implemented for SRID "
            "%d. Supported are SRIDs %s." %
            (srid, ", ".join(str(v) for v in CRS_WIDTH.keys()))
        )


def get_extent_wrappings(extent, srid=4326):
    """ Returns a list of extents covering the dateline if the given extent
    crosses the dateline. Otherwise a list containing only the given extent
    is returned.
    """

    crs_minx, _, crs_maxx, _ = crs_bounds(srid)
    crs_width = crs_maxx - crs_minx

    extents = []
    working_extent = extent
    while True:
        working_extent = (working_extent[0] - crs_width, working_extent[1],
                          working_extent[2] - crs_width, working_extent[3])
        if working_extent[2] > crs_minx:
            extents.append(working_extent)
        else:
            break

    working_extent = extent
    while True:
        working_extent = (working_extent[0] + crs_width, working_extent[1],
                          working_extent[2] + crs_width, working_extent[3])
        if working_extent[0] < crs_maxx:
            extents.append(working_extent)
        else:
            break

    return extents
