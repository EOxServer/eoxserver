#-------------------------------------------------------------------------------
#
#  WPS Literal Data - units of measure
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

class UnitOfMeasure(object):
    """ Base unit class. """

    def __init__(self, name):
        self.name = name

    def apply(self, value):
        """ Convert value from the common base to this uinit."""
        raise NotImplementedError

    def strip(self, value):
        """ Convert value of this unit to the common base."""
        raise NotImplementedError


class UnitLinear(UnitOfMeasure):
    """ Simple linear scale + offset unit of measure.

            value_uom = (value_base - offset)/scale
            value_base = value_uom*scale + offset

        Set scale linear conversion from  the base uinit E.g.,
        for 'F' UOM and base unit in 'K' set scale to 5.0/9.0 and
        offset to 459.67*5.0/9.0 .

        In case of simple scale factor set scale to multiple of the base unit
        and offset to zero E.g., for 'km' UOM base unit in 'm' set scale
        factor to 1000.0 and offset to 0.
    """

    def __init__(self, name, scale, offset=0):
        UnitOfMeasure.__init__(self, name)
        self._scale = float(scale)
        self._offset = float(offset)
        if self._scale == 0:
            raise ValueError("Invalid zero UOM scale!")

    def apply(self, value):
        """ Convert value from the common base to this uinit."""
        return (value - self._offset)/self._scale

    def strip(self, value):
        """ Convert value of this unit to the common base."""
        return value*self._scale + self._offset

