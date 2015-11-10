#-------------------------------------------------------------------------------
#
#  WPS Complex Data type
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

import os
import os.path
import json
from lxml import etree
from copy import deepcopy
from StringIO import StringIO

try:
    from cStringIO import StringIO as FastStringIO
except ImportError:
    FastStringIO = StringIO

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from .base import Parameter
from .formats import Format

#-------------------------------------------------------------------------------
# complex data - data containers

class CDBase(object):
    """ Base class of the complex data container. """
    def __init__(self, mime_type=None, encoding=None, schema=None, format=None,
                 filename=None):
        if isinstance(format, Format):
            self.mime_type = format.mime_type
            self.encoding = format.encoding
            self.schema = format.schema
        else:
            self.mime_type = mime_type
            self.encoding = encoding
            self.schema = schema
        self.filename = filename

class CDObject(CDBase):
    """ Complex data wraper arround an arbitraty python object.

        To be used to set custom format attributes for the XML
        and JSON payload.

        NOTE: CDObject is not used for the input JSON and XML.
    """
    def __init__(self, data, mime_type=None, encoding=None, schema=None,
                 format=None, **kwargs):
        CDBase.__init__(self, mime_type, encoding, schema, format, **kwargs)
        self.data = data

class CDByteBuffer(StringIO, CDBase):
    """ Complex data binary in-memory buffer (StringIO).

        To be used to hold a generic binary (byte-stream) payload.
    """
    def __init__(self, data='', mime_type=None, encoding=None, schema=None,
                 format=None, **kwargs):
        StringIO.__init__(self, str(data))
        CDBase.__init__(self, mime_type, encoding, schema, format, **kwargs)

    def write(self, data):
        StringIO.write(self, str(data))

    @property
    def data(self):
        self.seek(0)
        return self.read()


class CDTextBuffer(StringIO, CDBase):
    """ Complex data text (unicode) in-memory buffer (StringIO).

        To be used to hold generic text. The the text payload
        is stored as a unicode-stream.

        Set the 'text_encoding' parameter is unicode encoding/decoding
        shall be applied.
    """
    def __init__(self, data=u'', mime_type=None, encoding=None, schema=None,
                 format=None, text_encoding=None, **kwargs):
        StringIO.__init__(self, unicode(data))
        CDBase.__init__(self, mime_type, encoding, schema, format, **kwargs)
        self.text_encoding = text_encoding

    @property
    def data(self):
        self.seek(0)
        return self.read()

    def write(self, data):
        if self.text_encoding is None:
            return StringIO.write(self, unicode(data))
        else:
            return StringIO.write(self, unicode(data, self.text_encoding))

    def read(self, size=None):
        if size is None:
            data = StringIO.read(self)
        else:
            data = StringIO.read(self, size)
        if self.text_encoding is None:
            return data
        else:
            return data.encode(self.text_encoding)


class CDAsciiTextBuffer(CDByteBuffer):
    """ Complex data text (ascii) in-memory buffer (StringIO).

        To be used to hold generic ascii text. The the text payload
        is stored as a byte-stream and this class cannot hold
        characters outside of the 7-bit ascii characters' range.
    """
    def __init__(self, data='', mime_type=None, encoding=None, schema=None,
                 format=None, text_encoding=None, **kwargs):
        CDByteBuffer.__init__(
            self, data, mime_type, encoding, schema, format, **kwargs
        )
        self.text_encoding = text_encoding

    def write(self, data):
        if not isinstance(data, basestring):
            data = str(data)
        StringIO.write(self, data.encode('ascii'))

    def read(self, size=None):
        if size is None:
            data = StringIO.read(self)
        else:
            data = StringIO.read(self, size)
        if self.text_encoding is None:
            return data
        else:
            return data.encode(self.text_encoding)


class CDFile(CDBase):
    """ Complex data binary file.

        To be used to hold a generic binary (byte-stream) payload.

        NOTE: The file allows you to specify whether the file is
              temporary (will be atomatically removed - by default)
              or permanent (preserverved after object destruction).
    """

    def __init__(self, name, mode='r', buffering=-1,
                 mime_type=None, encoding=None, schema=None, format=None,
                 remove_file=True, **kwargs):
        CDBase.__init__(self, mime_type, encoding, schema, format, **kwargs)
        self._file = file(name, mode, buffering)
        self._remove_file = remove_file

    def __del__(self):
        name = self.name
        self.close()
        if self._remove_file:
            os.remove(name)

    @property
    def data(self):
        self.seek(0)
        return self.read()

    def __getattr__(self, attr):
        return getattr(self._file, attr)


class CDPermanentFile(CDFile):
    """ Complex data permanent binary file.

        To be used to hold a generic binary (byte-stream) payload.

        NOTE: This class preserves the actual file.
    """

    def __init__(self, remove_file, name, mode='r', buffering=-1,
                 mime_type=None, encoding=None, schema=None, format=None,
                 **kwargs):
        CDFile.__init__(name, mode, buffering, mime_type, encoding, schema,
                        format, False, **kwargs)

#-------------------------------------------------------------------------------

class ComplexData(Parameter):
    """ complex-data parameter class """

    def __init__(self, identifier, formats, *args, **kwargs):
        """ Object constructor.

            Parameters:
                identifier  identifier of the parameter.
                title       optional human-readable name (defaults to identifier).
                abstract    optional human-readable verbose description.
                metadata    optional metadata (title/URL dictionary).
                optional    optional boolean flag indicating whether the input
                            parameter is optional or not.
                formats     List of supported formats.
        """
        super(ComplexData, self).__init__(identifier, *args, **kwargs)
        self.formats = OrderedDict()
        if isinstance(formats, Format):
            formats = (formats,)
        for frm in formats:
            self.formats[(frm.mime_type, frm.encoding, frm.schema)] = frm

    @property
    def default_format(self):
        return self.formats.itervalues().next()

    def get_format(self, mime_type, encoding=None, schema=None):
        if mime_type is None:
            return self.default_format
        else:
            return self.formats.get((mime_type, encoding, schema))

#    def verify_format(self, format):
#        """ Returns valid format or rise value error exception."""
#        if format is None:
#            return self.default_format
#        tmp = (format.mime_type, format.encoding, format.schema)
#        if tmp in self.formats:
#            return format
#        raise ValueError("Invalid format %r"%format)

    def parse(self, data, mime_type, schema, encoding, **opt):
        """ parse input complex data """
        format_ = self.get_format(mime_type, encoding, schema)
        if format_ is None:
            raise ValueError("Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r"%(mime_type, encoding, schema))
        text_encoding = getattr(format_, 'text_encoding', 'utf-8')
        fattr = {
            'mime_type': format_.mime_type,
            'encoding': format_.encoding,
            'schema': format_.schema
        }
        if format_.is_xml:
            parsed_data = CDObject(etree.fromstring(data), **fattr)
        elif format_.is_json:
            parsed_data = CDObject(
                json.loads(_unicode(data, text_encoding)), **fattr
            )
        elif format_.is_text:
            parsed_data = CDTextBuffer(_unicode(data, text_encoding), **fattr)
            parsed_data.seek(0)
        else: # generic binary byte-stream
            parsed_data = CDByteBuffer(data, **fattr)
            if format_.encoding is not None:
                data_out = FastStringIO()
                for chunk in format_.decode(parsed_data, **opt):
                    data_out.write(chunk)
                parsed_data = data_out
            parsed_data.seek(0)
        return parsed_data

    def encode_xml(self, data):
        """ encode complex data to be embedded to an XML document"""
        mime_type = getattr(data, 'mime_type', None)
        encoding = getattr(data, 'encoding', None)
        schema = getattr(data, 'schema', None)
        format_ = self.get_format(mime_type, encoding, schema)
        if format_ is None:
            raise ValueError("Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r"%(mime_type, encoding, schema))
        if not format_.allows_xml_embedding:
            raise ValueError("Selected format does not allows XML embedding! "
                                "mime_type=%r, encoding=%r, schema=%r"%(
                                mime_type, encoding, schema))
        if isinstance(data, CDObject):
            data = data.data
        if format_.is_xml:
            if isinstance(data, etree._ElementTree):
                data = data.getroot()
            return deepcopy(data)
        elif format_.is_json:
            return json.dumps(data, ensure_ascii=False)
        elif format_.is_text:
            if not isinstance(data, basestring):
                data.seek(0)
                data = data.read()
            return data
        else: # generic binary byte-stream
            if format_.encoding is not None:
                data.seek(0)
                data_out = FastStringIO()
                for chunk in format_.encode(data):
                    data_out.write(chunk)
                data = data_out
            data.seek(0)
            return data.read()

    def encode_raw(self, data):
        """ encode complex data for raw output """
        def _rewind(fid):
            if hasattr(fid, 'seek'):
                fid.seek(0)
            return data
        mime_type = getattr(data, 'mime_type', None)
        encoding = getattr(data, 'encoding', None)
        schema = getattr(data, 'schema', None)
        format_ = self.get_format(mime_type, encoding, schema)
        text_encoding = getattr(format_, 'text_encoding', 'utf-8')
        if format_ is None:
            raise ValueError("Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r"%(mime_type, encoding, schema))
        if isinstance(data, CDObject):
            data = data.data
        if format_.is_xml:
            data = FastStringIO(etree.tostring(data, pretty_print=False,
                                xml_declaration=True, encoding=text_encoding))
            content_type = "%s; charset=%s"%(format_.mime_type, text_encoding)
        elif format_.is_json:
            data = FastStringIO(
                json.dumps(data, ensure_ascii=False).encode(text_encoding)
            )
            content_type = "%s; charset=%s"%(format_.mime_type, text_encoding)
        elif format_.is_text:
            if isinstance(data, (CDTextBuffer, CDAsciiTextBuffer)):
                data.text_encoding = text_encoding
            else:
                data = FastStringIO(_rewind(data).read().encode(text_encoding))
            content_type = "%s; charset=%s"%(format_.mime_type, text_encoding)
        else: # generic binary byte-stream
            if format_.encoding is not None:
                data_out = FastStringIO()
                for chunk in format_.encode(_rewind(data)):
                    data_out.write(chunk)
                data = data_out
            content_type = format_.mime_type
        return _rewind(data), content_type


def _bytestring(data):
    if isinstance(data, str):
        return data
    raise TypeError("Byte string expected, %s received!"%type(data))

def _unicode(data, encoding):
    if isinstance(data, unicode):
        return data
    elif isinstance(data, str):
        return unicode(data, encoding)
    raise TypeError("Byte od unicode string expected, %s received!"%type(data))
