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

# TODO: Review standard compliance of the duration parsing and encoding.

from .base import Parameter
from .data_types import BaseType, String, DTYPES
from .allowed_values import BaseAllowed, AllowedAny, AllowedEnum

class LiteralData(Parameter):
    """ literal-data parameter class """

    def __init__(self, identifier, dtype=String, uoms=None, default=None,
                 allowed_values=None, *args, **kwargs):
        """ Object constructor.

            Parameters:
                identifier  idetnfier of the parameter.
                title       optional human-raedable name (defaults to idetfier).
                description optional human-redable verbose description.
                metadata    optional metadata (title/URL dictionary).
                optional    optional boolean flag indicating whether the input
                            parameter is optional or not.
                dtype       optional data type of the parameter. String type
                            ``str`` is set by default. For list of supported
                            types see ``LiteralData.SUPPORTED_TYPES``).
                uoms        optional sequence of the supported units.
                defalt      optional default input value. Presence of the
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

        self.uoms = uoms or () # the first uom is the default one

        if default is None:
            self.default = None
        else:
            self.default = self.parse(default)
            self.is_optional = True

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

    def encode(self, value):
        """Encode the given value to its string representation."""
        return self._dtype.encode(value)

    def parse(self, raw_value):
        """Encode the given value to its string representation."""
        try:
            return self._allowed_values.verify(self._dtype.parse(raw_value))
        except (ValueError, TypeError) as exc:
            raise Exception("%s: Input parsing error: '%s' (raw value '%s')"
                            "" % (self.identifier, str(exc), raw_value))

