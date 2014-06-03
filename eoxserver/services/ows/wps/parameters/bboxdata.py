#-------------------------------------------------------------------------------
#
#  WPS Bounding-Box Data type
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2013 EOX IT Services GmbH
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

from eoxserver.core.util.rect import Rect
from .base import Parameter

#-------------------------------------------------------------------------------

class BoundingBox(tuple):
    """ Bounding Box representation. """

    def __new__(cls, bbox, crs=None):
        if isinstance(bbox, Rect):
            lower, uppper = bbox.offset, bbox.upper
        else:
            lower, upper = bbox

        lower = tuple(lower)
        upper = tuple(upper)

        if len(lower) != len(upper):
            raise ValueError("Both the lower and uppper corners must have"
                             " the same dimension!")

        return tuple.__new__(cls, (lower, upper))

    def __init__(self, bbox, crs=None):
        """ bounding box constructor

            Parameters:

                bbox    n-dimensional bounding box definition:
                            ((xmin,),(xmax,))
                            ((xmin,ymin),(xmax,ymax))
                            ((xmin,ymin,zmin),(xmax,ymax,zmax))
                        or instance of the ``Rect`` class.
                crs     optional crs identifier (URI)
        """
        tuple.__init__(self)
        self.__crs = crs or getattr(bbox, "crs", None)

    @property
    def crs(self):
        return self.__crs

    @property
    def lower(self):
        return self[0]

    @property
    def upper(self):
        return self[1]

    @property
    def dim(self):
        return len(self[0])

    @property
    def as_rect(self):
        """Cast to a Rect object."""
        if self.dim != 2:
            raise RuntimeError("Only 2D bounding-box can be cast to "
                                "a rectangle object!")
        return Rect(self[0][0], self[0][1], None, None, self[1][0], self[1][1])

#-------------------------------------------------------------------------------

class BoundingBoxData(Parameter):
    def __init__(self, identifier, crss=None, *args, **kwargs):
        super(BoundingBoxData, self).__init__(identifier, *args, **kwargs)
        # TODO: CRSs
        self.crss = crss or ('EPSG:4326',)  # the first CRS is the default one
        #self.dim = dim                      # data dimension
