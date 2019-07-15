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


class LayerNotDefined(Exception):
    def __init__(self, layer):
        super(LayerNotDefined, self).__init__("No such layer '%s'." % layer)

    locator = "layers"
    code = "LayerNotDefined"


class InvalidCRS(Exception):
    def __init__(self, value, crs_param_name):
        super(InvalidCRS, self).__init__(
            "Invalid '%s' parameter value: '%s'"
            % (crs_param_name.upper(), value)
        )
        self.locator = crs_param_name
    code = "InvalidCRS"


class InvalidFormat(Exception):
    def __init__(self, value):
        super(InvalidFormat, self).__init__(
            "Unknown format name '%s'" % value
        )
    locator = "format"
    code = "InvalidFormat"
