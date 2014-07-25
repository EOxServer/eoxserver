#-------------------------------------------------------------------------------
#
#  WPS Literal Data type
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

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from .base import Parameter
from .data_types import BaseType, String, DTYPES
from .allowed_values import BaseAllowed, AllowedAny, AllowedEnum
from .units import UnitOfMeasure, UnitLinear


class LiteralData(Parameter):
    """ literal-data parameter class """

    def __init__(self, identifier, dtype=String, uoms=None, default=None,
                 allowed_values=None, *args, **kwargs):
        """ Object constructor.

            Parameters:
                identifier  identifier of the parameter.
                title       optional human-raedable name (defaults to identifier).
                abstract    optional human-redable verbose description.
                metadata    optional metadata (title/URL dictionary).
                optional    optional boolean flag indicating whether the input
                            parameter is optional or not.
                dtype       optional data type of the parameter. String type
                            ``str`` is set by default. For list of supported
                            types see ``LiteralData.SUPPORTED_TYPES``).
                uoms        optional sequence of the supported units.
                default     optional default input value. Presence of the
                            default value sets the parameter optional.
                allowed_values optional restriction on the accepted values.
                            By default any value of the given type is
                            supported. The allowed value can be specified by an
                            an enumerated list (iterable) of values or by
                            instance of one of the following classes:
                            ``AllowedAny``, ``AllowedEnum``, ``AllowedRange``,
                            or ``AllowedByReference``.
        """
        super(LiteralData, self).__init__(identifier, *args, **kwargs)

        if issubclass(dtype, BaseType):
            self._dtype = dtype
        elif dtype in DTYPES:
            self._dtype = DTYPES[dtype]
        else:
            raise TypeError("Non-supported data type %s! "%dtype)

        if isinstance(allowed_values, BaseAllowed):
            if (hasattr(allowed_values, 'dtype')
                                      and self._dtype != allowed_values.dtype):
                raise TypeError("The allowed values vs. literal data  type"
                      " mismatch! %s != %s", allowed_values.dtype, self._dtype)
            self._allowed_values = allowed_values
        elif allowed_values is not None:
            self._allowed_values = AllowedEnum(allowed_values, self._dtype)
        else:
            self._allowed_values = AllowedAny()

        if uoms: # the first uom is the default one
            tmp = OrderedDict()
            for uom in uoms:
                if not isinstance(uom, UnitOfMeasure):
                    uom = UnitLinear(uom[0], uom[1])
                tmp[uom.name] = uom
            self._uoms = tmp
        else:
            self._uoms = None

        if default is None:
            self.default = None
        else:
            self.default = self.parse(default)
            self.is_optional = True

    @property
    def default_uom(self):
        return self._uoms.keys()[0] if self._uoms else None

    @property
    def uoms(self):
        return self._uoms.keys() if self._uoms else None

    @property
    def dtype(self):
        """Data type class of the literal data object. (RO)"""
        return self._dtype

    @property
    def allowed_values(self):
        """Allowed values object of the literal data object. (RO)"""
        return self._allowed_values

    def check(self, value):
        """Check whether the value is allowed (True) or not (False)."""
        return self._allowed_values.check(value)

    def verify(self, value):
        """Return the value if allowed or raise the ValueError exception."""
        return self._allowed_values.verify(value)

    def apply_uom(self, value, uom):
        if uom is None:
            return value
        try:
            return self._uoms[uom].apply(value)
        except KeyError:
            raise ValueError("Invalid UOM '%s'!"%uom)

    def strip_uom(self, value, uom):
        if uom is None:
            return value
        try:
            return self._uoms[uom].strip(value)
        except KeyError:
            raise ValueError("Invalid UOM '%s'!"%uom)

    def encode(self, value, uom=None, encoding=None):
        """ Encode the output value to its string representation.

            The value is checked to match the defined allowed values
            restriction and the UOM conversion is applied.

            Returns unicode or byte-string if the encoding is given.
        """
        try:
            _value = self._allowed_values.verify(value)
            _value = self.apply_uom(_value, uom)
            _value = self._dtype.encode(_value)
            return _value.encode(encoding) if encoding else _value
        except (ValueError, TypeError) as exc:
            raise ValueError("Output encoding error: '%s' (value '%s')"
                                                        "" % (str(exc), value))

    def parse(self, raw_value, uom=None, encoding="utf-8"):
        """ Parse the input value from its string representation.

            The value is checked to match the defined allowed values
            restriction and the UOM conversion is applied.

            Non-unicode raw_data are converted to unicode before parsing.
            Byte strings are decoded using the profided encoding (utf8 by
            default).
        """
        try:
            if isinstance(raw_value, unicode):
                _value = raw_value
            elif isinstance(raw_value, str):
                _value = unicode(raw_value, encoding)
            else:
                _value = unicode(raw_value)
            _value = self._dtype.parse(raw_value)
            _value = self.strip_uom(_value, uom or self.default_uom)
            _value = self._allowed_values.verify(_value)
            return _value
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "Input parsing error: '%s' (raw value '%s')" % (exc, raw_value)
            )
