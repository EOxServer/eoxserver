#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""\
This module contains a set of handler base classes which shall help to implement
a specific handler. Interface methods need to be overridden in order to work, 
default methods can be overidden.
"""

from eoxserver.core import UniqueExtensionPoint
from eoxserver.resources.coverages import models
from eoxserver.services.ows.wms.interfaces import (
    WMSCapabilitiesRendererInterface
)
from eoxserver.services.result import to_http_response


class WMSGetCapabilitiesHandlerBase(object):
    """ Base for WMS capabilities handlers.
    """

    service = "WMS"
    request = "GetCapabilities"

    renderer = UniqueExtensionPoint(WMSCapabilitiesRendererInterface)

    def handle(self, request):
        collections_qs = models.Collection.objects \
            .order_by("identifier") \
            .exclude(
                footprint__isnull=True, begin_time__isnull=True, 
                end_time__isnull=True
            )
        coverages = [
            coverage for coverage in models.Coverage.objects \
                .filter(visible=True)
            if not issubclass(coverage.real_type, models.Collection)
        ]

        result, _ = self.renderer.render(
            collections_qs, coverages, request.GET.items()
        )
        return to_http_response(result)
