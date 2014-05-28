#-------------------------------------------------------------------------------
#
# WPS 1.0 execute response raw encoder
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

from eoxserver.services.result import (
    to_http_response, ResultItem, ResultBuffer
)

class WPS10ExecuteResponseRawEncoder(object):

    def __init__(self, results):
        self.results = results

    @staticmethod
    def encode_execute_response(process, inputs, results, lineage=False):
        """Pack the raw execute response."""
        return [ResultBuffer(v, identifier=k) for k,v in results.iteritems()]

    @staticmethod
    def serialize(result_items):
        return to_http_response(result_items)

    @property
    def content_type(self):
        if len(self.results) > 1:
            return "multipart/related"
        return getattr(self.results.values()[0], "mime_type", "text/plain")

