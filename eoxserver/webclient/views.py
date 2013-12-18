#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Fabian Schindler <fabian.schindler@eox.at>
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

import logging

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.http import Http404
from django.conf import settings
from django.template import RequestContext

from eoxserver import get_version
from eoxserver.core.config import get_eoxserver_config
from eoxserver.core.decoders import config, enum
from eoxserver.core.util.timetools import isoformat
from eoxserver.resources.coverages import models
from eoxserver.services.ows.common.config import CapabilitiesConfigReader


logger = logging.getLogger(__name__)

def index(request):
    dataset_series_ids = models.DatasetSeries.objects.values_list(
        "identifier", flat=True
    )
    stitched_mosaic_ids = models.RectifiedStitchedMosaic.objects.values_list(
        "identifier", flat=True
    )
    return render_to_response(
        'webclient/index.html', {
            "datasetseries_eoids": dataset_series_ids,
            "stitchedmosaic_eoids": stitched_mosaic_ids,
            "path": request.path,
            "version": get_version(),
        },
        context_instance=RequestContext(request)
    )

def webclient(request, identifier):
    """
    View for webclient interface.
    
    Uses `webclient.preview_service`, `webclient.outline_service`,
    `webclient.preview_url`
    """
    
    try:
        eo_object = models.Collection.objects.get(identifier=identifier)
    
    except models.Collection.DoesNotExist:
        raise Http404("No such collection.")
    
    begin = eo_object.begin_time
    end = eo_object.end_time
    
    extent = eo_object.extent_wgs84
    # zoom to Europe if we don't have a proper extent
    if extent == (0,0,1,1):
        extent = (-10,30,34,72)
    reader = WebclientConfigReader(get_eoxserver_config())

    return render_to_response(
        'webclient/webclient.html', {
            "eoid": identifier,
            "ows_url": reverse("eoxserver.services.views.ows"), #reader.http_service_url,
            "preview_service": reader.preview_service,
            "outline_service": reader.outline_service,
            "preview_url": reader.preview_url or reader.http_service_url,
            "outline_url": reader.outline_url or reader.http_service_url,
            #"begin": {"date": begin.strftime("%Y-%m-%d"),
            #          "time": begin.strftime("%H:%M")},
            #"end": {"date": end.strftime("%Y-%m-%d"),
            #        "time": end.strftime("%H:%M")},
            "begin": isoformat(begin),
            "end": isoformat(end),
            "extent": "%f,%f,%f,%f" % extent,
            "debug": settings.DEBUG
        },
        context_instance=RequestContext(request)
    )


class WebclientConfigReader(CapabilitiesConfigReader):
    section = "webclient"

    preview_service = config.Option(type=enum(("wms", "wmts")), default="wms")
    outline_service = config.Option(type=enum(("wms", "wmts")), default="wms")

    preview_url = config.Option(default=None)
    outline_url = config.Option(default=None)

