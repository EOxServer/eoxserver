from lxml import etree
from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap


ns_ows = NameSpace("http://www.opengis.net/ows/2.0", "ows")

nsmap = NameSpaceMap(ns_ows)
OWS = ElementMaker(namespace=ns_ows.uri, nsmap=nsmap)

class OWS20ExceptionXMLEncoder(object):
    def encode(self, message, version, code, locator=None):

        exception_attributes = {
            "exceptionCode": code
        }

        if locator:
            exception_attributes["locator"] = locator

        exception_text = (OWS("ExceptionText", message),) if message else ()

        root = OWS("ExceptionReport", 
            OWS("Exception", *exception_text, **exception_attributes
            ), lang="en", version=version
        )
        return etree.tostring(root, pretty_print=True, encoding='iso-8859-1'), "text/xml"
