#-------------------------------------------------------------------------------
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


class Rect(tuple):
    """ Named tuple to describe areas in a 2D array like in images. The tuple
        is always in the form (offset_x, offset_y, size_x, size_y).

        :param offset_x: the x offset of the origin
        :param offset_y: the y offset of the origin
        :param size_x: thy x size of the rect
        :param size_y: thy y size of the rect
        :param upper_x: thy upper x offset of the rect (mutually exclusive with
                        size_x)
        :param upper_y: thy upper y offset of the rect (mutually exclusive with
                        size_y)
    """

    __slots__ = ()

    def __new__(cls, offset_x=0, offset_y=0, size_x=None, size_y=None,
                upper_x=0, upper_y=0):

        # To subclass tuples, it is necessary to overwrite the `__new__`
        # method.

        size_x = size_x if size_x is not None else max(0, upper_x - offset_x)
        size_y = size_y if size_y is not None else max(0, upper_y - offset_y)

        return tuple.__new__(cls, (offset_x, offset_y, size_x, size_y))

    offset_x = property(lambda self: self[0])
    offset_y = property(lambda self: self[1])
    offset = property(lambda self: (self.offset_x, self.offset_y))

    size_x = property(lambda self: self[2])
    size_y = property(lambda self: self[3])
    size = property(lambda self: (self.size_x, self.size_y))

    upper_x = property(lambda self: self.offset_x + self.size_x)
    upper_y = property(lambda self: self.offset_y + self.size_y)
    upper = property(lambda self: (self.upper_x, self.upper_y))

    area = property(lambda self: self.size_x * self.size_y)

    def envelope(self, other):
        """ Returns the envelope of two :class:`Rect`, i.e., a smallest
            rectange contaning the input rectangles.
        """
        return Rect(
            offset_x=min(self.offset_x, other[0]),
            offset_y=min(self.offset_y, other[1]),
            upper_x=max(self.upper_x, other[0] + other[2]),
            upper_y=max(self.upper_y, other[1] + other[3])
        )

    __or__ = envelope

    def intersection(self, other):
        """ Returns the intersection of two :class:`Rect`, i.e.,
            a largest common rectanle contained by the input rectangles.
        """

        return Rect(
            offset_x=max(self.offset_x, other[0]),
            offset_y=max(self.offset_y, other[1]),
            upper_x=min(self.upper_x, other[0] + other[2]),
            upper_y=min(self.upper_y, other[1] + other[3])
        )

    __and__ = intersection

    def intersects(self, other):
        """ Tests whether two :class:`Rect` overlap (True) or not (False).
        """
        return self.intersection(other).area > 0

    def translated(self, tup):
        """ Returns a new :class:`Rect` shifted by the given offset.
        """
        return Rect(
            self.offset_x + tup[0], self.offset_y + tup[1],
            self.size_x, self.size_y
        )

    __add__ = translated

    __sub__ = (lambda self, coordinates: self.translated((-coordinates[0], -coordinates[-1])))

    def __repr__(self):
        return "Rect(offset_x=%s, offset_y=%s, size_x=%s, size_y=%s)" % self
