#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

""" This module provides base functionality for any other decoder class.
"""


from eoxserver.core.decoders import (
    ZERO_OR_ONE, ONE_OR_MORE, ANY, SINGLE_VALUES, WrongMultiplicityException,
    InvalidParameterException, MissingParameterException,
    MissingParameterMultipleException
)


class BaseParameter(property):
    """ Abstract base class for XML, KVP or any other kind of parameter.
    """

    def __init__(self, type=None, num=1, default=None):
        super(BaseParameter, self).__init__(self.fget)
        self.type = type or str
        self.num = num
        self.default = default

    def select(self, decoder):
        """ Interface method.
        """
        raise NotImplementedError

    @property
    def locator(self):
        return ""

    def fget(self, decoder):
        """ Property getter function.
        """

        results = self.select(decoder)
        count = len(results)

        locator = self.locator
        multiple = self.num not in SINGLE_VALUES

        # check the correct count of the result
        if not multiple and count > 1:
            raise WrongMultiplicityException(locator, "at most one", count)

        elif self.num == 1 and count == 0:
            raise MissingParameterException(locator)

        elif self.num == ONE_OR_MORE and count == 0:
            raise MissingParameterMultipleException(locator)

        elif isinstance(self.num, int) and count != self.num:
            raise WrongMultiplicityException(locator, self.num, count)

        # parse the value/values, or return the defaults
        if multiple:
            if count == 0 and self.num == ANY and self.default is not None:
                return self.default

            try:
                return [self.type(v) for v in results]
            except Exception as e:
                # let some more sophisticated exceptions pass
                if hasattr(e, "locator") or hasattr(e, "code"):
                    raise
                raise InvalidParameterException(str(e), locator)

        elif self.num == ZERO_OR_ONE and count == 0:
            return self.default

        elif self.type:
            try:
                return self.type(results[0])
            except Exception as e:
                # let some more sophisticated exceptions pass
                if hasattr(e, "locator") or hasattr(e, "code"):
                    raise
                raise InvalidParameterException(str(e), locator)

        return results[0]
