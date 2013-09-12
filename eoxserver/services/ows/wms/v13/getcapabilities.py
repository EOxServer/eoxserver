#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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


from eoxserver.core import Component, implements, ExtensionPoint
from eoxserver.services.component import OWSServiceComponent, env
from eoxserver.services.wms.renderer import WMSCapabilitiesRenderer


class WMS13GetCapabilitiesHandler(Component):
    implements(OWSServiceHandlerInterface)
    implements(OWSGetServiceHandlerInterface)
    #implements(OWSPostServiceHandlerInterface) # TODO: ?
    
    service = "WMS"
    versions = ("1.3", "1.3.0",)
    request = "GetCapabilities"

    def get_decoder(self, request):
        pass

    def handle(self, request):
        decoder = self.get_decoder(request)
        if "text/xml" not in decoder.acceptformats:
            raise InvalidRequestException()

        coverages_qs = models.Coverage.objects.order_by("identifier")

        dataset_series_qs = models.DatasetSeries.objects \
            .order_by("identifier") \
            .exclude(
                footprint__isnull=True, begin_time__isnull=True, 
                end_time__isnull=True
            )

        renderer = WMSCapabilitiesRenderer()
        return renderer.render(decoder.sections, coverages_qs, dataset_series_qs)

