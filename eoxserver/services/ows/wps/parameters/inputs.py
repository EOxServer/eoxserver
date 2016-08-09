#-------------------------------------------------------------------------------
#
#  Input objects used by the execute requests and responses
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

from .base import ParamMetadata

class InputReference(ParamMetadata):
    # pylint: disable=too-few-public-methods, too-many-arguments
    """ Input data reference class.

    Constructor parameters:
        href         input reference URL
        identifier   input item identifier
        title        user defined title
        abstract     user defined abstract
        headers      additional HTTP request headers
        body         optional HTTP/POST request payload
        method       reference method ('GET' or 'POST')
        mime_type    reference ComplexData mime-type
        encoding     reference ComplexData encoding
        schema       reference ComplexData schema
        body_href    optional HTTP/POST request payload reference URL
    """

    def __init__(self, href, identifier, title=None, abstract=None,
                 headers=None, body=None, method=None, mime_type=None,
                 encoding=None, schema=None, body_href=None):
        ParamMetadata.__init__(
            self, identifier, title, abstract, None, None,
            mime_type, encoding, schema
        )
        self.href = href
        self.headers = headers or ()
        self.body = body
        self.body_href = body_href
        self.method = method


class InputData(ParamMetadata):
    # pylint: disable=too-few-public-methods, too-many-arguments
    """ Generic container for the raw data inputs.  An instances of this class
    holds the inputs as decoded from various WPS requests before their
    validation and conversion to their configured data-type.

    Constructor parameters:
        data         unparsed (raw) data payload (byte string)
        identifier   input item identifier
        title        user defined title
        abstract     user defined abstract
        uom          input LiteralData UOM
        crs          input BoundingBoxData CRS
        mime_type    input ComplexData mime-type
        encoding     input ComplexData encoding
        schema       input ComplexData schema
        asurl        indicates whether the decoded input comes from
                     a URL encoded request (KVP) or not.
    """
    def __init__(self, data, identifier, title=None, abstract=None,
                 uom=None, crs=None, mime_type=None,
                 encoding=None, schema=None, asurl=False):
        ParamMetadata.__init__(
            self, identifier, title, abstract, uom, crs,
            mime_type, encoding, schema
        )
        self.data = data
        self.asurl = asurl
