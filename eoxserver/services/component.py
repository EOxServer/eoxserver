from eoxserver.core import env, Component, implements, ExtensionPoint
from eoxserver.core.decoders import kvp, xml
from eoxserver.services.interfaces import *


class OWSServiceComponent(Component):
    service_handlers = ExtensionPoint(OWSServiceHandlerInterface)
    exception_handlers = ExtensionPoint(OWSExceptionHandlerInterface)

    get_service_handlers = ExtensionPoint(OWSGetServiceHandlerInterface)
    post_service_handlers = ExtensionPoint(OWSPostServiceHandlerInterface)


    def __init__(self, *args, **kwargs):
        super(OWSServiceComponent, self).__init__(*args, **kwargs)
        #self.service_handlers = None
        #self.exception_handlers = None

    def get_decoder(self, request):
        if request.method == "GET":
            return OWSCommonKVPDecoder(request.GET)
        elif request.method == "POST":
            return OWSCommonXMLDecoder(request.body)


    def query_service_handler(self, request):
        decoder = self.get_decoder(request)
        handlers = self.service_handlers

        # TODO: improve. a lot.
        for handler in handlers:
            if (decoder.service == handler.service 
                and decoder.version in handler.versions 
                and decoder.request == handler.request):
                
                # TODO: also take request method into account

                return handler

        return None


    def query_service_handlers(self, service=None, versions=None, request=None, method=None):
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
            handlers = filter(lambda h: h.request == request, handlers)

        return handlers


    def get_exception_handler(self, request):
        decoder = self.get_decoder(request)


class OWSCommonKVPDecoder(kvp.Decoder):
    service = kvp.Parameter("service")
    version = kvp.Parameter("version", num="?")
    request = kvp.Parameter("request")


class OWSCommonXMLDecoder(kvp.Decoder):
    service = xml.Parameter("@service")
    version = xml.Parameter("@version", num="?")
    request = xml.Parameter("local-name()")
