#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
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

"""This model contains Django views for the EOxServer software. Its main
function is ows() which handles all incoming OWS requests"""

from django.http import HttpResponse
from django.conf import settings

import os.path
import logging


from eoxserver.core.system import System
from eoxserver.services.owscommon import OWSCommonHandler
from eoxserver.services.requests import OWSRequest
from eoxserver.services.auth.base import getPDP

def ows(request):
    """
    This function handles all incoming OWS requests. It configures basic
    settings e.g. for the logging module, triggers reading of the config
    file and passes on the request to eoxserver.services.owscommon.OWSCommonHandler.
    
    @param  request     A django.http.HttpRequest object containing the
                        request parameters and data
    
    @return             A django.http.HttpResponse object containing the
                        response content, headers and status
    
    @see                eoxserver.services.owscommon.OWSCommonHandler
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

    System.init()
    
    pdp = getPDP()
    
    if pdp:
        auth_resp = pdp.authorize(ows_req)
    
    if not pdp or auth_resp.authorized:
        
        handler = OWSCommonHandler()

        ows_resp = handler.handle(ows_req)

        response = HttpResponse(
            content=ows_resp.getContent(),
            content_type=ows_resp.getContentType(),
            status=ows_resp.getStatus()
        )
        for header_name, header_value in ows_resp.headers.items():
            response[header_name] = header_value

    else:
        response = HttpResponse(
            content=auth_resp.getContent(),
            content_type=auth_resp.getContentType(),
            status=auth_resp.getStatus()
        )
        for header_name, header_value in ows_resp.headers.items():
            response[header_name] = header_value

    return response
