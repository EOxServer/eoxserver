# ------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
# ------------------------------------------------------------------------------
# Copyright (C) 2016 EOX IT Services GmbH
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
# ------------------------------------------------------------------------------
# pylint: disable=missing-docstring, too-few-public-methods

from eoxserver.core import Component, implements
from eoxserver.services.ows.wps.interfaces import ProcessInterface
from eoxserver.services.ows.wps.parameters import LiteralData, RequestParameter


def get_header(header_name):
    """ Second order function extracting user defined HTTP request header. """
    cgi_header_name = "HTTP_" + header_name.upper().replace("-", "_")
    def _get_header(request):
        return request.META.get(cgi_header_name)
    return _get_header


class Test07RequestParameterTest(Component):
    """ RequestParameters WPS test. """
    implements(ProcessInterface)

    identifier = "TC07:request-parameter"
    title = "Test Case 07: Request parameter."
    description = (
        "This test process demonstrates use of the RequestParameters "
        "input. The request parameter is a special input which passes "
        "meta-data extracted from the Django HTTPRequest object to the "
        "executed process."
    )

    inputs = [
        ("test_header", RequestParameter(get_header('X-Test-Header'))),
        ("input", LiteralData(
            'TC07:input01', str, optional=True,
            abstract="Optional simple string input.",
        )),
    ]

    outputs = [
        ("output", LiteralData(
            'TC07:output01', str,
            abstract="Simple string input.",
        )),
    ]

    @staticmethod
    def execute(test_header, **kwarg):
        return test_header or ""
