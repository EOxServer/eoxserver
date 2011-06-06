#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

"""This model contains Django views for the EOxServer software. Its main
function is ows() which handles all incoming OWS requests"""

from django.http import HttpResponse
from django.conf import settings

import os.path
import logging

from eoxserver.services.owscommon import OWSCommonHandler
from eoxserver.services.requests import OWSRequest
from eoxserver.core.system import System

def ows(request):
    """
    This function handles all incoming OWS requests. It configures basic
    settings e.g. for the logging module, triggers reading of the config
    file and passes on the request to eoxserver.lib.ows.EOxSOWSHandler.
    
    @param  request     A django.http.HttpRequest object containing the
                        request parameters and data
    
    @return             A django.http.HttpResponse object containing the
                        response content, headers and status
    
    @see                eoxserver.lib.ows.EOxSOWSHandler
    """

    if request.method == 'GET':
        ows_req = OWSRequest(
            http_req=request,
            params=request.GET,
            param_type="kvp"
        )
    elif request.method == 'POST':
        ows_req = OWSRequest(
            http_req=request,
            params=request.raw_post_data,
            param_type="xml"
        )
    else:
        raise Exception("Unsupported request method '%s'" % request.method)

    System.startRequest()
    
    handler = OWSCommonHandler()

    ows_resp = handler.handle(ows_req)

    response = HttpResponse(
        content=ows_resp.getContent(),
        content_type=ows_resp.getContentType(),
        status=ows_resp.getStatus()
    )

    return response
