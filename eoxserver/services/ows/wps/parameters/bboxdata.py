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

import re
from itertools import chain

from eoxserver.core.util.rect import Rect
from .data_types import Double
from .crs import CRSType
from .base import Parameter


# precompiled reg.ex. used to eliminate repeated white-spaces
_RE_MULTIWS = re.compile(r"\s+")

#-------------------------------------------------------------------------------

class BoundingBox(tuple):
    """ Bounding Box representation. """

    def __new__(cls, bbox, crs=None):
        if isinstance(bbox, Rect):
            lower, upper = bbox.offset, bbox.upper
        else:
            lower, upper = bbox
        lower = tuple(float(v) for v in lower)
        upper = tuple(float(v) for v in upper)
        if len(lower) != len(upper):
            raise ValueError("Dimension mismatch! Both the lower and uppper "
                             "corners must have the same dimension!")
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
        self._crs = crs if crs is not None else getattr(bbox, "crs", None)

    @property
    def crs(self):
        return self._crs

    @property
    def lower(self):
        return self[0]

    @property
    def upper(self):
        return self[1]

    @property
    def dimension(self):
        return len(self[0])

    @property
    def as_rect(self):
        """Cast to a Rect object."""
        if self.dimension != 2:
            raise RuntimeError("Only 2D bounding-box can be cast to "
                                "a rectangle object!")
        return Rect(self[0][0], self[0][1], None, None, self[1][0], self[1][1])

    def __str__(self):
        crs = ", crs=%s" % (self.crs if self.crs is not None else "")
        return "BoundingBox((%s, %s)%s)" % (self.lower, self.upper, crs)

#-------------------------------------------------------------------------------

class BoundingBoxData(Parameter):
    """ bunding box parameter class """
    dtype = Double
    dtype_crs = CRSType

    def __init__(self, identifier, crss=None, dimension=2, default=None,
                 *args, **kwargs):
        """ Object constructor.

            Parameters:
                identifier  identifier of the parameter.
                title       optional human-raedable name (defaults to identifier).
                abstract    optional human-redable verbose description.
                metadata    optional metadata (title/URL dictionary).
                optional    optional boolean flag indicating whether the input
                            parameter is optional or not.
                default     optional default input value. Presence of the
                            default value sets the parameter optional.
                crss        list of accepted CRSs (Coordinate Reference Systems).
                            The CRSs shall be given in form of the integer EPSG
                            codes. Defaults to WGS84 (EPSG:4326).
                dimension   optional dimension of the bounding box coordinates.
                            Defaults to 2.
        """
        super(BoundingBoxData, self).__init__(identifier, *args, **kwargs)
        self.dimension = int(dimension)
        self.crss = tuple(self.parse_crs(crs) for crs in crss or (4326,))
        self.default = self.parse(default) if default is not None else None
        if self.dimension < 1:
            raise ValueError("Invalid bounding box dimension %s!" % dimension)

    @property
    def default_crs(self):
        return self.crss[0]

    def _encode(self, bbox):
        """ Common low-level encoding method."""
        if self.dimension != bbox.dimension:
            raise ValueError("Invalid dimension %s of the encoded bounding "
                              "box!"%bbox.dimension)
        crs = bbox.crs if bbox.crs is not None else self.default_crs
        if crs not in self.crss:
            raise ValueError("Invalid crs %s of the encoded bounding box!"%crs)

        return (
            (self.dtype.encode(v) for v in bbox.lower),
            (self.dtype.encode(v) for v in bbox.upper),
            (self.encode_crs(crs),)
        )

    def encode_kvp(self, bbox):
        """ Encode KVP bounding box."""
        return ",".join(chain(*self._encode(bbox)))

    def encode_xml(self, bbox):
        """ Encode XML bounding box."""
        lower, upper, crs = self._encode(bbox)
        return (" ".join(lower), " ".join(upper), crs[0])

    def parse(self, raw_bbox):
        if isinstance(raw_bbox, BoundingBox):
            bbox = BoundingBox((raw_bbox.lower, raw_bbox.upper),
                raw_bbox.crs if raw_bbox.crs is not None else self.default_crs)
        elif isinstance(raw_bbox, basestring):
            items = raw_bbox.split(',')
            dim = len(items)/2
            lower = [self.dtype.parse(item) for item in items[0:dim]]
            upper = [self.dtype.parse(item) for item in items[dim:2*dim]]
            if len(items) > 2*dim:
                crs = self.parse_crs(items[2*dim])
            else:
                crs = self.default_crs
            bbox = BoundingBox((lower, upper), crs)
        else: # assuming XML decoded tuple
            lower = _RE_MULTIWS.sub(",", raw_bbox[0].strip()).split(",")
            upper = _RE_MULTIWS.sub(",", raw_bbox[1].strip()).split(",")
            if len(lower) != len(upper):
                raise ValueError("Dimension mismatch of the bounding box's"
                       " corner coordinates! %d != %d"%(len(lower), len(upper)))
            lower = [self.dtype.parse(item) for item in lower]
            upper = [self.dtype.parse(item) for item in upper]
            if raw_bbox[2] is not None:
                crs = self.parse_crs(raw_bbox[2])
            else:
                crs = self.default_crs
            bbox = BoundingBox((lower, upper), crs)
        if bbox.dimension != self.dimension:
            raise ValueError("Invalid dimenstion %d of the parsed bounding"
                             " box!"%(bbox.dimension))
        if bbox.crs not in self.crss:
            raise ValueError("Invalid CRS %r of the parsed bounding"
                             " box!"%(bbox.crs))
        return bbox

    @classmethod
    def parse_crs(cls, raw_crs):
        return cls.dtype_crs.parse(raw_crs)

    @classmethod
    def encode_crs(cls, crs):
        return cls.dtype_crs.encode(crs)

