#-------------------------------------------------------------------------------
#
#  WPS Complex Data formats
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from .codecs import CodecBase64, CodecRaw


class Format(object):
    """ Base complex data format.

    Constructor parameters:
        encoder     format's encoder object (defines the encoding)
        mime_type   mime-type of the format
        schema      optional schema of the document
        is_text     optional boolean flag indicating text-based data
                    format.
        is_xml      optional boolean flag indicating XML-based format.
                    The flag enables is_text flag.
        is_json     optional boolean flag indicating JSON-bases format.
                    The flag enables is_text flag.
    """
    # boolean flag indicating whether the format allows the payload to be
    # embedded to XML response or not. The XML embedding is disabled by default.
    allows_xml_embedding = False

    def __init__(self, encoder, mime_type, schema=None,
                 is_text=False, is_xml=False, is_json=False):
        # pylint: disable=too-many-arguments
        if is_xml or is_json:
            is_text = True
        self.mime_type = mime_type
        self.schema = schema
        self.is_text = is_text or is_xml or is_json
        self.is_xml = is_xml
        self.is_json = is_json
        self._codec = encoder

    @property
    def encoding(self):
        """ Get the format encoding name. """
        return self._codec.encoding

    def encode(self, file_in, **opt):
        """ Encoding generator."""
        return self._codec.encode(file_in, **opt)

    def decode(self, file_in, **opt):
        """ Encoding generator."""
        return self._codec.decode(file_in, **opt)


class FormatText(Format):
    """ Text-based complex data format. """
    allows_xml_embedding = True
    def __init__(self, mime_type="text/plain", schema=None,
                 text_encoding='utf-8'):
        Format.__init__(self, CodecRaw, mime_type, schema, True, False, False)
        self.text_encoding = text_encoding


class FormatXML(Format):
    """ XML-based complex data format. """
    allows_xml_embedding = True
    def __init__(self, mime_type="application/xml", schema=None,
                 text_encoding='utf-8'):
        Format.__init__(self, CodecRaw, mime_type, schema, True, True, False)
        self.text_encoding = text_encoding


class FormatJSON(Format):
    """ JSON-based complex data format. """
    allows_xml_embedding = True
    def __init__(self, mime_type="application/json", schema=None,
                 text_encoding='utf-8'):
        Format.__init__(self, CodecRaw, mime_type, schema, True, False, True)
        self.text_encoding = text_encoding


class FormatBinaryRaw(Format):
    """ Raw binary complex data format. """
    allows_xml_embedding = False
    def __init__(self, mime_type="application/octet-stream"):
        Format.__init__(self, CodecRaw, mime_type, None, False, False, False)


class FormatBinaryBase64(Format):
    """ Base64 encoded binary complex data format. """
    allows_xml_embedding = True
    def __init__(self, mime_type="application/octet-stream"):
        Format.__init__(self, CodecBase64, mime_type, None, False, False, False)
