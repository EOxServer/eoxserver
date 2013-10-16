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


from lxml.builder import ElementMaker

from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap


ns_xlink = NameSpace("http://www.w3.org/1999/xlink", "xlink")
ns_ows = NameSpace("http://www.opengis.net/ows/2.0", "ows")

nsmap = NameSpaceMap(ns_ows)
OWS = ElementMaker(namespace=ns_ows.uri, nsmap=nsmap)


class OWS20Encoder(XMLEncoder):
    def encode_reference(self, node_name, href, reftype="simple"):
        return OWS(node_name, 
            **{ns_xlink("href"): href, ns_xlink("type"): reftype}
        )


class OWS20ExceptionXMLEncoder(XMLEncoder):
    def encode_exception(self, message, version, code, locator=None):

        exception_attributes = {
            "exceptionCode": code
        }

        if locator:
            exception_attributes["locator"] = locator

        exception_text = (OWS("ExceptionText", message),) if message else ()

        return OWS("ExceptionReport", 
            OWS("Exception", *exception_text, **exception_attributes
            ), lang="en", version=version
        )
