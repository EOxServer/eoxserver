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


try:
    from io import StringIO 
except ImportError:
    from cStringIO import StringIO

try:
    from PIL import Image, ImageFont, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
from lxml.builder import ElementMaker

from eoxserver.core import Component, implements
from eoxserver.core.decoders import kvp, lower
from eoxserver.core.util.xmltools import XMLEncoder, NameSpace, NameSpaceMap
from eoxserver.services.ows.interfaces import ExceptionHandlerInterface

try:
    # Python 2
    xrange
except NameError:
    # Python 3, xrange is now named range
    xrange = range

class WMS13ExceptionHandler(Component):
    implements(ExceptionHandlerInterface)

    service = "WMS"
    versions = ("1.3.0", "1.3")
    request = None

    def get_encoder(self, request):
        decoder = WMS13Decoder(request.GET)
        exceptions = decoder.exceptions
        if exceptions in ("xml", "application/vnd.ogc.se_xml") or not HAS_PIL:
            return WMS13ExceptionXMLEncoder()
        elif exceptions in ("inimage", "blank"):
            return WMS13ExceptionImageEncoder(
                decoder.width, decoder.height, decoder.format, decoder.bgcolor,
                exceptions=="blank"
            )
        print (decoder.exceptions)

    def handle_exception(self, request, exception):
        encoder = self.get_encoder(request)

        locator = getattr(exception, "locator", None)
        code = getattr(exception, "code", None) or type(exception).__name__

        return (
            encoder.serialize(
                encoder.encode_exception(
                    str(exception), code, locator
                ),
            ), 
            encoder.content_type, 
            400
        )


class WMS13Decoder(kvp.Decoder):
    width = kvp.Parameter(type=int, num="?")
    height = kvp.Parameter(type=int, num="?")
    format = kvp.Parameter(num="?")
    bgcolor = kvp.Parameter(num="?")
    exceptions = kvp.Parameter(num="?", type=lower, default="xml")


ns_ogc = NameSpace("http://www.opengis.net/ogc", "ogc")
nsmap = NameSpaceMap(ns_ogc)
OGC = ElementMaker(namespace=ns_ogc.uri, nsmap=nsmap)

class WMS13ExceptionXMLEncoder(XMLEncoder):
    def encode_exception(self, message, code, locator=None):
        attributes = {
            "code": code
        }
        if locator:
            attributes["locator"] = locator

        return OGC("ServiceExceptionReport",
            OGC("ServiceException",
                str(message),
                **attributes
            ),
            version="1.3.0"
        )

    @property
    def content_type(self):
        return "application/vnd.ogc.se_xml"

    def get_schema_locations(self):
        return {
            "http://www.opengis.net/ogc": "http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd"
        }


class WMS13ExceptionImageEncoder(object):
    def __init__(self, width=None, height=None, format=None, bgcolor=None, blank=False):
        self.width = width if width > 0 else 256
        self.height = height if height > 0 else 256
        if "/" in format:
            format = format[format.find("/") + 1:]
        self.format = format or "jpeg"
        self.bgcolor = bgcolor or "white"
        self.blank = blank

    @property
    def content_type(self):
        return "image/%s" % self.format

    def encode_exception(self, message, code, locator=None):
        width, height = self.width, self.height
        image = Image.new("RGB", (width, height), self.bgcolor)

        # if requested draw the exception string in the image
        if not self.blank:
            font = ImageFont.load_default()
            draw = ImageDraw.Draw(image)
            yoffset = 0
            while len(message):
                for i in xrange(len(message)):
                    part = message if i == 0 else message[:-i]
                    xsize, ysize = font.getsize(part)
                    print (i, xsize, ysize, part)
                    if xsize < width:
                        break
                draw.text((0, yoffset), part, font=font, fill="red")
                yoffset += ysize
                message = message[-i:]
                if i == 0:
                    break
        return image

    def serialize(self, image):
        f = StringIO()
        try:
            image.save(f, self.format)
        except (IOError, KeyError):
            image.save(f, "jpeg") # Fallback solution
        return f.getvalue()
