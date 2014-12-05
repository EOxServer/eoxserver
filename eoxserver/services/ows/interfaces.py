#-------------------------------------------------------------------------------
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


class ServiceHandlerInterface(object):
    """ Interface for OWS Service handlers.
    """

    @property
    def service(self):
        """ The name of the supported service in uppercase letters. This can 
            also be an iterable, if the handler shall support more than one 
            service specifier.
            Some service specifications demand that the service parameter can be
            omitted for certain requests. In this case this property can alse be
            ``None`` or contain ``None``.
        """

    @property
    def versions(self):
        """ An iterable of all supported versions as strings.
        """

    @property
    def request(self):
        """ The supported request method.
        """

    def handle(self, request):
        """ The main handling method. Takes a `django.http.Request` object as 
            single parameter.
        """

    @property
    def constraints(self):
        """ Optional property to return a dict with constraints for default 
            values.
        """

    @property
    def index(self):
        """ Optional. The index this service handler shall have when being 
            reported in a capabilities document.
        """


class ExceptionHandlerInterface(object): 
    """ Interface for OWS exception handlers.
    """

    @property
    def service(self):
        """ The name of the supported service in uppercase letters. This can 
            also be an iterable, if the handler shall support more than one 
            service specifier.
            Some service specifications demand that the service parameter can be
            omitted for certain requests. In this case this property can alse be
            ``None`` or contain ``None``.
        """

    @property
    def versions(self):
        """ An iterable of all supported versions as strings.
        """

    @property
    def request(self):
        """ The supported request method.
        """

    def handle_exception(self, request, exception):
        """ The main exception handling method. Parameters are an object of the 
            `django.http.Request` type and the raised exception.
        """


class GetServiceHandlerInterface(ServiceHandlerInterface):
    """ Interface for service handlers that support HTTP GET requests.
    """


class PostServiceHandlerInterface(ServiceHandlerInterface):
    """ Interface for service handlers that support HTTP POST requests.
    """


class VersionNegotiationInterface(ServiceHandlerInterface):
    """ Interface for handlers that contribute to version negotiation.
    """
