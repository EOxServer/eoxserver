#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

import os
from django.utils.six import string_types


if os.environ.get('READTHEDOCS', None) != 'True':
    try:
        from osgeo.osr import *
    except ImportError:
        from osr import *

    UseExceptions()

    _SpatialReference = SpatialReference


class SpatialReference(object):
    """ Extension to the original SpatialReference class.
    """

    def __init__(self, raw=None, format=None):
        self.sr = sr = _SpatialReference()
        if raw is not None:
            format = format.upper() if format is not None else None
            if format == "WKT" or (
                isinstance(raw, string_types) and (raw.startswith('PROJCS') or raw.startswith('GEOGCS'))
            ):
                sr.ImportFromWkt(raw)
            elif isinstance(raw, int) or format == "EPSG":
                sr.ImportFromEPSG(int(raw))
            elif isinstance(raw, string_types) and raw.startswith('EPSG:'):
                sr.ImportFromEPSG(int(raw.partition(':')[2]))
            else:
                sr.SetFromUserInput(raw)

    def IsSame(self, other):
        if isinstance(other, SpatialReference):
            return self.sr.IsSame(other.sr)
        else:
            return self.sr.IsSame(other)

    @property
    def proj(self):
        return self.sr.ExportToProj4()

    @property
    def wkt(self):
        return self.sr.ExportToWkt()

    @property
    def xml(self):
        return self.sr.ExportToXML()

    @property
    def url(self):
        # TODO: what about other authorities than EPSG?
        return "http://www.opengis.net/def/crs/EPSG/0/%d" % self.srid

    @property
    def srid(self):
        """ Convenience function that tries to get the SRID of the projection.
        """

        if self.sr.IsGeographic():
            cstype = 'GEOGCS'
        else:
            cstype = 'PROJCS'

        srid = self.sr.GetAuthorityCode(cstype)
        return int(srid) if srid is not None else None

    @property
    def swap_axes(self):
        # TODO:
        pass

    def __getattr__(self, name):
        return getattr(self.sr, name)
