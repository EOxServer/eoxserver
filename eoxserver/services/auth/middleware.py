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


import functools

from django.http import HttpResponse

from eoxserver.services.auth.base import getPDP
from eoxserver.services.auth.exceptions import AuthorisationException
from eoxserver.services.ows.common.v20.encoders import OWS20ExceptionXMLEncoder


class PDPMiddleware(object):
    """ Middleware to allow authorization agains a Policy Decision Point. This
        middleware will be used for *all* requests and *all* configured views.
        If you only want to provide PDP authorization for a single view, use the
        `pdp_protect`.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        pdp = getPDP()
        if pdp:
            try:
                authorized = pdp.authorize(request)
                message = "Not authorized"
                code = "AccessForbidden"
            except AuthorisationException as e:
                authorized = False
                message = str(e)
                code = e.code

            if not authorized:
                encoder = OWS20ExceptionXMLEncoder()
                return HttpResponse(
                    encoder.serialize(
                        encoder.encode_exception(message, "2.0.0", code)
                    ),
                    encoder.content_type, status=403
                )


def pdp_protect(view):
    """ Wrapper function for views that shall be protected by PDP authorization.
        This function can be used as a decorator of a view function, or as a
        modifier to be used in the url configuration file.
        e.g:
        ::

            urlpatterns = patterns('',
                ...
                url(r'^ows', pdp_protect(ows)),
                ...
            )
    """

    @functools.wraps(view)
    def wrapped(request, *args, **kwargs):
        pdp = getPDP()
        if pdp:
            try:
                authorized = pdp.authorize(request)
                message = "Not authorized"
                code = "NotAuthorized"
            except AuthorisationException as e:
                authorized = False
                message = str(e)
                code = e.code

            if not authorized:
                encoder = OWS20ExceptionXMLEncoder()
                return HttpResponse(
                    encoder.serialize(
                        encoder.encode_exception(message, "2.0.0", code)
                    ),
                    encoder.content_type, status=403
                )

        return view(request, *args, **kwargs)

    return wrapped
