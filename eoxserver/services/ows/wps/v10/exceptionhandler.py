#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

from eoxserver.core import Component, implements
from eoxserver.services.ows.interfaces import ExceptionHandlerInterface
from eoxserver.services.ows.common.v11.encoders import OWS11ExceptionXMLEncoder


class WPS10ExceptionHandler(Component):
    """ WPS 1.0 exception handler. """
    implements(ExceptionHandlerInterface)

    service = "WPS"
    versions = ("1.0.0", "1.0")
    request = None

    def handle_exception(self, request, exception):
        """ Handle exception. """
        # pylint: disable=unused-argument, no-self-use

        code = getattr(exception, "code", None)
        locator = getattr(exception, "locator", None)
        http_status_code = getattr(exception, "http_status_code", 400)

        if not code:
            code = "NoApplicableCode"
            locator = type(exception).__name__

        encoder = OWS11ExceptionXMLEncoder()

        return (
            encoder.serialize(
                encoder.encode_exception(
                    str(exception), "1.1.0", code, locator
                )
            ),
            encoder.content_type, http_status_code
        )
