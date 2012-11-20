#-------------------------------------------------------------------------------
# $Id$
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

from django.shortcuts import render_to_response
from django.http import Http404
from django.conf import settings
from django.template import RequestContext

from eoxserver.core.system import System
from eoxserver import get_version


logger = logging.getLogger(__name__)

def index(request):
    System.init()
    dss_factory = System.getRegistry().bind("resources.coverages.wrappers.DatasetSeriesFactory")
    dataset_series_ids = [obj.getEOID() for obj in dss_factory.find()] 
    
    mosaic_factory = System.getRegistry().bind("resources.coverages.wrappers.EOCoverageFactory")
    stitched_mosaic_ids = [obj.getEOID() for obj in mosaic_factory.find(
                           impl_ids=["resources.coverages.wrappers.RectifiedStitchedMosaicWrapper"]
                           )]
    
    
    
    return render_to_response(
        'webclient/index.html', {
            "datasetseries_eoids": dataset_series_ids,
            "stitchedmosaic_eoids": stitched_mosaic_ids,
            "path": request.path,
            "version": get_version(),
        },
        context_instance=RequestContext(request)
    )

def webclient(request, eoid):
    """
    View for webclient interface.
    
    Uses `webclient.preview_service`, `webclient.outline_service`,
    `webclient.preview_url`
    """
    
    
    System.init()
    eo_obj = System.getRegistry().getFromFactory(
        "resources.coverages.wrappers.DatasetSeriesFactory",
        {"obj_id": eoid}
    )
    if eo_obj is None:
        eo_obj = System.getRegistry().getFromFactory(
            "resources.coverages.wrappers.EOCoverageFactory",
            {"obj_id": eoid}
        )
        if eo_obj is None:
            raise Http404
    
    begin = eo_obj.getBeginTime()
    end = eo_obj.getEndTime()
    
    # TODO: remove center and add initial extent
    extent = eo_obj.getFootprint().extent
    
    # TODO set static resources
    http_ows_url = System.getConfig().getConfigValue(
        "services.owscommon", "http_service_url"
    )
    
    preview_service = System.getConfig().getConfigValue(
        "webclient", "preview_service"
    ) or "wms"
    
    outline_service = System.getConfig().getConfigValue(
        "webclient", "outline_service"
    ) or "wms"
    
    if preview_service not in ("wms", "wmts"): 
        logger.error("Unsupported service type '%s'" % preview_service)
        preview_service = "wms"
    if outline_service not in ("wms", "wmts"):
        logger.error("Unsupported service type '%s'" % outline_service)
        outline_service = "wms"
    
    preview_url = System.getConfig().getConfigValue(
        "webclient", "preview_url"
    ) or http_ows_url
    
    outline_url = System.getConfig().getConfigValue(
        "webclient", "outline_url"
    ) or http_ows_url
    
    return render_to_response(
        'webclient/webclient.html', {
            "eoid": eoid,
            "ows_url": http_ows_url,
            "preview_service": preview_service,
            "outline_service": outline_service,
            "preview_url": preview_url,
            "outline_url": outline_url,
            "begin": {"date": begin.strftime("%Y-%m-%d"),
                      "time": begin.strftime("%H:%M")},
            "end": {"date": end.strftime("%Y-%m-%d"),
                    "time": end.strftime("%H:%M")},
            "extent": "%f,%f,%f,%f" % extent,
            "debug": settings.DEBUG
        },
        context_instance=RequestContext(request)
    )



