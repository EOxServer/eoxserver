#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Stephan Krause <stephan.krause@eox.at>
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

import logging
import traceback

from django.http import HttpResponse
try:
    from django.http import StreamingHttpResponse
except:
    class StreamingHttpResponse(object):
        pass
from django.conf import settings

from eoxserver.services.ows.component import ServiceComponent, env


logger = logging.getLogger(__name__)

def ows(request):
    """ Main entry point for OWS requests against EOxServer. It uses the OWS 
        component to dynamically determine the handler for this request. 
        If an exception occurs during the handling of the request, an exception
        handler is determined and dispatched.

        Any response of the service handler and exception handler is transformed
        to a django HttpResponse to adhere the required interface.
    """

    component = ServiceComponent(env)

    try:
        handler = component.query_service_handler(request)
        result = handler.handle(request)
        default_status = 200
    except Exception, e:
        logger.debug(traceback.format_exc())
        handler = component.query_exception_handler(request)
        result = handler.handle_exception(request, e)
        default_status = 400

    # try to return a django compatible response
    if isinstance(result, (HttpResponse, StreamingHttpResponse)):
        return result

    elif isinstance(result, basestring):
        return HttpResponse(result)

    # convert result to a django response
    try:
        content, content_type, status = result
        return HttpResponse(
            content=content, content_type=content_type, status=status
        )
    except ValueError:
        pass
        
    try:
        content, content_type = result
        return HttpResponse(
            content=content, content_type=content_type, status=default_status
        )
    except ValueError:
        pass
