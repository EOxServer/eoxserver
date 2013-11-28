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


    def combination(self, other):
        """ Returns a combined rect 
        """
        return Rect(
            offset_x=min(self.offset_x, other[0]), 
            offset_y=min(self.offset_y, other[1]),
            upper_x=max(self.upper_x, other[0] + other[2]), 
            upper_y=max(self.upper_y, other[1] + other[3])
        )

    __or__ = combination

    def intersection(self, other):
        return Rect(
            offset_x=max(self.offset_x, other[0]), 
            offset_y=max(self.offset_y, other[1]),
            upper_x=min(self.upper_x, other[0] + other[2]), 
            upper_y=min(self.upper_y, other[1] + other[3])
        )

    __and__ = intersection

    def intersects(self, other):
        return self.intersection(other).area > 0


    def translated(self, (diff_x, diff_y)):
        return Rect(
            self.size_x, self.size_y, 
            self.offset_x + diff_x, self.offset_y + diff_y
        )

    __add__ = translated

    __sub__ = (lambda self, (x, y): self.translated((-x, -y)))
