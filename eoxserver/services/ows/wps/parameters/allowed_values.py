#-------------------------------------------------------------------------------
#
#  WPS Literal Data - allowed values
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

from math import isinf
try:
    from itertools import chain, ifilterfalse as filterfalse
except ImportError:
    from itertools import filterfalse

from .data_types import BaseType, Double, DTYPES


class TypedMixIn(object):
    """ Mix-in class adding date-type to an allowed value range. """
    # pylint: disable=too-few-public-methods

    def __init__(self, dtype):
        if issubclass(dtype, BaseType):
            self._dtype = dtype
        elif dtype in DTYPES:
            self._dtype = DTYPES[dtype]
        else:
            raise TypeError("Non-supported data type %s!" % dtype)

    @property
    def dtype(self):
        """ Get data-type. """
        return self._dtype


class BaseAllowed(object):
    """ Allowed values base class. """

    def check(self, value):
        """ check validity """
        raise NotImplementedError

    def verify(self, value):
        """ Verify the value."""
        raise NotImplementedError


class AllowedAny(BaseAllowed):
    """ Allowed values class allowing any value. """

    def check(self, value):
        return True

    def verify(self, value):
        return value


class AllowedByReference(BaseAllowed):
    """ Allowed values class defined by a reference.

    NOTE: As it is not how such a reference definition looks like
    this class has the same behaviour as the AllowedAny class.
    """
    # TODO: Implement proper handling of the allowed values defined by a reference.

    def __init__(self, url):
        self._url = url

    @property
    def url(self):
        """ Get the URL of the reference. """
        return self._url

    def check(self, value):
        return True

    def verify(self, value):
        return value


class AllowedEnum(BaseAllowed, TypedMixIn):
    """ Allowed values class allowing values from an enumerated set. """

    @staticmethod
    def _unique(values):
        """ Get list of order-preserved unique values and the corresponding
        unordered set.
        """
        vset = set()
        vlist = []
        vset_add = vset.add
        vlist_append = vlist.append

        for value in filterfalse(vset.__contains__, values):
            vset_add(value)
            vlist_append(value)
        return vlist, vset

    def __init__(self, values, dtype=Double):
        TypedMixIn.__init__(self, dtype)
        self._values_list, self._values_set = self._unique(
            self._dtype.parse(value) for value in values
        )

    @property
    def values(self):
        """ Get the allowed values. """
        return self._values_list

    def check(self, value):
        return self._dtype.parse(value) in self._values_set

    def verify(self, value):
        if self.check(value):
            return value
        raise ValueError("The value is not in the set of the allowed values.")


class AllowedRange(BaseAllowed, TypedMixIn):
    """ Allowed values class allowing values from a range.

    Constructor parameters:
                minval      range lower bound - set to None if unbound
                maxval      range upper bound - set to None if unbound
                closure    *'closed'|'open'|'open-closed'|'closed-open'
                spacing     uniform spacing of discretely sampled ranges
                spacing_rtol relative tolerance of the spacing match
        """

    ALLOWED_CLOSURES = ['closed', 'open', 'open-closed', 'closed-open']

    # NOTE: Use of spacing with float discrete range is not recommended.
    def __init__(self, minval, maxval, closure='closed',
                 spacing=None, spacing_rtol=1e-9, dtype=Double):
        # pylint: disable=too-many-arguments
        TypedMixIn.__init__(self, dtype)

        if not self._dtype.comparable:
            raise ValueError("Non-supported range data type '%s'!" % self._dtype)

        if closure not in self.ALLOWED_CLOSURES:
            raise ValueError("Invalid closure specification!")

        if minval is None and maxval is None:
            raise ValueError("Invalid range bounds!")

        if spacing_rtol < 0.0 or spacing_rtol > 1.0:
            raise ValueError("Invalid spacing relative tolerance!")

        self._closure = self.ALLOWED_CLOSURES.index(closure)
        self._minval = None if minval is None else self._dtype.parse(minval)
        self._maxval = None if maxval is None else self._dtype.parse(maxval)
        self._base = self._maxval if self._minval is None else self._minval

        # verify the spacing
        if spacing is not None:
            ddtype = self._dtype.get_diff_dtype()

            # check whether the type has difference operation defined
            if ddtype is None or ddtype.zero is None:
                raise TypeError(
                    "Spacing is not applicable for type '%s'!" % dtype
                )
            spacing = ddtype.parse(spacing)
            if spacing <= ddtype.zero:
                raise ValueError("Invalid spacing '%s'!" % spacing)

        self._spacing = spacing
        self._rtol = spacing_rtol

    @property
    def minval(self):
        """ Get the lower bound of the range. """
        return self._minval

    @property
    def maxval(self):
        """ Get the upper bound of the range. """
        return self._maxval

    @property
    def spacing(self):
        """ Get the range spacing. """
        return self._spacing

    @property
    def closure(self):
        """ Get the range closure type. """
        return self.ALLOWED_CLOSURES[self._closure]

    def _out_of_spacing(self, value):
        if self._spacing is None:
            return False
        ddtype = self._dtype.get_diff_dtype()
        tmp0 = ddtype.as_number(self._dtype.sub(value, self._base))
        tmp1 = ddtype.as_number(self.spacing)
        tmp2 = float(tmp0) / float(tmp1)
        if isinf(tmp2):
            return True
        return not self._rtol >= abs(tmp2 - round(tmp2))

    def _out_of_bounds(self, value):
        if value != value:  # simple type-safe NaN check (works in Python > 2.5)
            return True
        below = self._minval is not None and (
            value < self._minval or (
                value == self._minval and self._closure in (1, 2)
            )
        )
        above = self._maxval is not None and (
            value > self._maxval or (
                value == self._maxval and self._closure in (1, 3)
            )
        )
        return below or above

    def check(self, value):
        value = self._dtype.parse(value)
        return not (self._out_of_bounds(value) or self._out_of_spacing(value))

    def verify(self, value):
        parsed_value = self._dtype.parse(value)
        if self._out_of_bounds(parsed_value):
            raise ValueError("The value is not within the allowed range.")
        if self._out_of_spacing(parsed_value):
            raise ValueError("The value does not fit the requested spacing.")
        return value


class AllowedRangeCollection(BaseAllowed, TypedMixIn):
    """ Allowed value class allowing values from a collection of AllowedEnum
    and AllowedRange instances.
    """

    def __init__(self, *objs):
        if not objs:
            raise ValueError(
                "At least one AllowedEnum or AllowedRange object "
                "must be provided!"
            )
        TypedMixIn.__init__(self, objs[0].dtype)

        values = set()
        ranges = []

        for obj in objs:
            # Merge enumerated values into one set.
            if isinstance(obj, AllowedEnum):
                values.update(obj.values)
            # Collect ranges.
            elif isinstance(obj, AllowedRange):
                ranges.append(obj)
            else:
                raise ValueError(
                    "An object which is neither AllowedEnum"
                    " nor AllowedRange instance! OBJ=%r" % obj
                )

            # Check that all ranges and value sets are of the same type.
            if self.dtype != obj.dtype:
                raise TypeError("Data type mismatch!")

        self._enum = AllowedEnum(values, dtype=self.dtype)
        self._ranges = ranges

    @property
    def enum(self):
        """ Get merged set of the enumerated allowed values. """
        return self._enum

    @property
    def ranges(self):
        """ Get list of the allowed values' ranges. """
        return self._ranges

    def check(self, value):
        for obj in chain([self._enum], self._ranges):
            if obj.check(value):
                return True
        return False

    def verify(self, value):
        if self.check(value):
            return value
        raise ValueError(
            "The value does not match the range of the allowed values!"
        )
