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


from django.conf import settings

from eoxserver.core import Component, implements
from eoxserver.services.result import ResultBuffer
from eoxserver.services.ows.version import Version
from eoxserver.services.ows.wcs.interfaces import (
    WCSCapabilitiesRendererInterface
)
from eoxserver.services.ows.wcs.v20.encoders import WCS20CapabilitiesXMLEncoder


class NativeWCS20CapabilitiesRenderer(Component):
    implements(WCSCapabilitiesRendererInterface)

    versions = (Version(2, 0),)

    def supports(self, params):
        if params.version not in self.versions:
            return False

        if params.accept_formats and "text/xml" not in params.accept_formats:
            return False

        # TODO: accept_languages?
        return True

    def render(self, params):
        encoder = WCS20CapabilitiesXMLEncoder()
        return [
            ResultBuffer(
                encoder.serialize(
                    encoder.encode_capabilities(
                        params.sections or ("all"),
                        None,
                        params.coverages,
                        params.dataset_series,
                        params.http_request
                    ), pretty_print=settings.DEBUG
                ),
                encoder.content_type
            )
        ]
