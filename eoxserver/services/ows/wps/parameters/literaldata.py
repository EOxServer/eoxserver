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
from django.utils.encoding import smart_str
from django.utils.six import text_type


class LiteralData(Parameter):
    """ Literal-data parameter class.

    Constructor parameters:
        identifier  identifier of the parameter used by the WPS service
        title       optional human-readable name (defaults to identifier)
        abstract    optional human-readable verbose description
        metadata    optional metadata (title/URL dictionary)
        optional    optional boolean flag indicating whether the input
                    parameter is optional or not
        dtype       optional data type of the parameter. String type
                    ``str`` is set by default. For list of supported
                    types see ``LiteralData.SUPPORTED_TYPES``)
        uoms        optional sequence of the supported units
        default     optional default input value. Presence of the
                    default value sets the parameter optional.
        allowed_values optional restriction on the accepted values.
                    By default any value of the given type is
                    supported. The allowed value can be specified by
                    an enumerated list (iterable) of values or by
                    instance of one of the following classes:
                    ``AllowedAny``, ``AllowedEnum``, ``AllowedRange``,
                    or ``AllowedByReference``.
        resolve_input_references  Set this option to False not to resolve
                    input references. By default the references are
                    resolved (downloaded and parsed) transparently.
                    If set to False the references must be handled
                    by the process.
    """

    def __init__(self, identifier, dtype=String, uoms=None, default=None,
                 allowed_values=None, *args, **kwargs):
        # pylint: disable=too-many-arguments, too-many-branches
        super(LiteralData, self).__init__(identifier, *args, **kwargs)

        if isinstance(dtype, type) and issubclass(dtype, BaseType):
            self._dtype = dtype
        elif isinstance(dtype, BaseType):
            self._dtype = dtype
        elif dtype in DTYPES:
            self._dtype = DTYPES[dtype]
        else:
            raise TypeError("Non-supported data type %s!" % dtype)

        if isinstance(allowed_values, BaseAllowed):
            if (hasattr(allowed_values, 'dtype') and
                    self._dtype != allowed_values.dtype):
                raise TypeError(
                    "The allowed values has a different data-type "
                    "then the literal data object %s != %s" %
                    (allowed_values.dtype, self._dtype)
                )
            self._allowed_values = allowed_values
        elif allowed_values is not None:
            self._allowed_values = AllowedEnum(allowed_values, self._dtype)
        else:
            self._allowed_values = AllowedAny()  # pylint: disable=redefined-variable-type

        if uoms:  # the first UOM is the default one
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
        """ Get the default UOM. """
        return list(self._uoms)[0] if self._uoms else None

    @property
    def uoms(self):
        """ Get all allowed UOMs. """
        return list(self._uoms) if self._uoms else None

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
        """ Convert value from the common base to the desired UOM. """
        if uom is None:
            return value
        try:
            return self._uoms[uom].apply(value)
        except KeyError:
            raise ValueError("Invalid UOM '%s'!" % uom)

    def strip_uom(self, value, uom):
        """ Convert value from the provided UOM to the common base. """
        if uom is None:
            return value
        try:
            return self._uoms[uom].strip(value)
        except KeyError:
            raise ValueError("Invalid UOM '%s'!" % uom)

    def encode(self, value, uom=None, encoding=None):
        """ Encode the output value to its string representation.

            The value is checked to match the defined allowed values
            restriction and the UOM conversion is applied.

            Returns Unicode or byte-string if the encoding is given.
        """
        try:
            _value = self._allowed_values.verify(value)
            _value = self.apply_uom(_value, uom)
            _value = self._dtype.encode(_value)
            return _value.encode(encoding) if encoding else _value
        except (ValueError, TypeError) as exc:
            raise ValueError(
                "Output encoding error: '%s' (value '%s')" % (str(exc), value)
            )

    def parse(self, raw_value, uom=None, encoding="utf-8"):
        """ Parse the input value from its string representation.

            The value is checked to match the defined allowed values
            restriction and the UOM conversion is applied.

            Non-Unicode raw_data are converted to Unicode before parsing.
            Byte strings are decoded using the profited encoding (utf8 by
            default).
        """

        try:
            if isinstance(raw_value, text_type):
                _value = raw_value
            elif isinstance(raw_value, str):
                _value = smart_str(raw_value, encoding)
            else:
                _value = smart_str(raw_value)
            _value = self._dtype.parse(raw_value)
            _value = self.strip_uom(_value, uom or self.default_uom)
            _value = self._allowed_values.verify(_value)

            return _value
        except (ValueError, TypeError) as exc:

            raise ValueError(
                "Input parsing error: '%s' (raw value '%s')" % (exc, raw_value)
            )
