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


from eoxserver.core import env, Component, implements, ExtensionPoint
from eoxserver.core.decoders import kvp, xml, upper
from eoxserver.services.interfaces import *


class OWSServiceComponent(Component):
    service_handlers = ExtensionPoint(OWSServiceHandlerInterface)
    exception_handlers = ExtensionPoint(OWSExceptionHandlerInterface)

    get_service_handlers = ExtensionPoint(OWSGetServiceHandlerInterface)
    post_service_handlers = ExtensionPoint(OWSPostServiceHandlerInterface)


    def __init__(self, *args, **kwargs):
        super(OWSServiceComponent, self).__init__(*args, **kwargs)


    def get_decoder(self, request):
        if request.method == "GET":
            return OWSCommonKVPDecoder(request.GET)
        elif request.method == "POST":
            return OWSCommonXMLDecoder(request.body)


    def query_service_handler(self, request):
        """ Tries to find the correct service handler
        """
        decoder = self.get_decoder(request)
        handlers = self.service_handlers

        # TODO: version negotiation

        # TODO: improve. a lot.
        for handler in handlers:
            if (decoder.service == handler.service.upper()
                and decoder.version in handler.versions 
                and decoder.request == handler.request.upper()):
                
                # TODO: also take request method into account

                return handler

        return None


    def query_service_handlers(self, service=None, versions=None, request=None, method=None):
        service = service.upper() if service is not None else None
        request = request.upper() if request is not None else None
        method = method.upper() if method is not None else None

        if method == "GET":
            handlers = self.get_service_handlers
        elif method == "POST":
            handlers = self.post_service_handlers
        elif method is None:
            handlers = self.service_handlers
        else:
            return []

        if service:
            handlers = filter(lambda h: h.service == service, handlers)

        if versions:
            handlers = filter(
                lambda h: len(set(h.versions) & set(versions)) > 0, handlers
            )

        if request:
            handlers = filter(lambda h: h.request.upper() == request, handlers)

        return handlers


    def query_exception_handler(self, request):
        decoder = self.get_decoder(request)
        handlers = self.exception_handlers

        # TODO: improve. a lot.
        for handler in handlers:
            if (decoder.service == handler.service 
                and decoder.version in handler.versions):
                
                return handler

        return None


class MapServerComponent(Component):
    connectors = ExtensionPoint(MapServerConnectorInterface)
    layer_factories = ExtensionPoint(MapServerLayerFactoryInterface)
    style_applicators = ExtensionPoint(MapServerStyleApplicatorInterface)

    def get_connector(self, data_items):
        for connector in self.connectors:
            if connector.supports(data_items):
                return connector

        return None

    def get_layer_factory(self, coverage_type, suffix=None):
        result = None
        for factory in self.layer_factories:
            if (issubclass(coverage_type, factory.handles)
                and suffix == factory.suffix):
                if result:
                    pass # TODO
                    #raise Exception("Found")
                result = factory
                return result
        return result


class OWSCommonKVPDecoder(kvp.Decoder):
    service = kvp.Parameter("service", type=upper)
    version = kvp.Parameter("version", num="?")
    request = kvp.Parameter("request", type=upper)


class OWSCommonXMLDecoder(kvp.Decoder):
    service = xml.Parameter("@service", type=upper)
    version = xml.Parameter("@version", num="?")
    request = xml.Parameter("local-name()", type=upper)
