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
# pylint: disable=too-few-public-methods,

import json
from os import remove
from copy import deepcopy

try:
    from StringIO import StringIO
    from cStringIO import StringIO as FastStringIO
    BytesIO = StringIO
except ImportError:
    from io import BytesIO
    from io import StringIO
    from io import StringIO as FastStringIO

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict

from lxml import etree
from .base import Parameter
from .formats import Format
from django.utils.encoding import smart_str
from django.utils.six import string_types, text_type, itervalues, binary_type

#-------------------------------------------------------------------------------
# complex data - data containers

class CDBase(object):
    """ Base class of the complex data container.

    Constructor parameters (all optional and all defaulting to None):
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        headers    additional raw output HTTP headers encoded as a list
                   of <key>, <value> pairs (tuples).
    """
    def __init__(self, mime_type=None, encoding=None, schema=None, format=None,
                 filename=None, headers=None, **kwargs):
        # pylint: disable=redefined-builtin, unused-argument, too-many-arguments
        if isinstance(format, Format):
            self.mime_type = format.mime_type
            self._encoding = format.encoding
            self.schema = format.schema
        else:
            self.mime_type = mime_type
            self._encoding = encoding
            self.schema = schema
        self.filename = filename
        self.headers = headers or []

    @property
    def encoding(self):
        return self._encoding

    @property
    def data(self):
        """ Get the payload data. """
        raise NotImplementedError


class CDObject(CDBase):
    """ Complex data wrapper around an arbitrary python object.
        To be used to set custom format attributes for the XML and JSON payload.
        NOTE: CDObject is not used for the input JSON and XML.

    Constructor parameters:
        data       mandatory object holding the payload data
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        headers    additional raw output HTTP headers encoded as a list
                   of <key>, <value> pairs (tuples).
    """
    def __init__(self, data, *args, **kwargs):
        CDBase.__init__(self, *args, **kwargs)
        self._data = data

    @property
    def data(self):
        return self._data


class CDByteBuffer(BytesIO, CDBase):
    """ Complex data binary in-memory buffer (StringIO).
        To be used to hold a generic binary (byte-stream) payload.

    Constructor parameters:
        data       optional initial payload byte string
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        headers    additional raw output HTTP headers encoded as a list
                   of <key>, <value> pairs (tuples).
    """
    def __init__(self, data=b'', *args, **kwargs):
        # NOTE: StringIO is an old-style class and super cannot be used!
        BytesIO.__init__(self, data)
        CDBase.__init__(self, *args, **kwargs)

    def write(self, data):
        BytesIO.write(self, data)

    @property
    def data(self):
        self.seek(0)
        return self.read()


class CDTextBuffer(StringIO, CDBase):
    """ Complex data text (Unicode) in-memory buffer (StringIO).
        To be used to hold generic text. The text payload is stored as
        a Unicode-stream.

    Constructor parameters:
        data       optional initial payload Unicode string
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        headers    additional raw output HTTP headers encoded as a list
                   of <key>, <value> pairs (tuples).
        text_encoding   optional keyword parameter defining the input text
                   encoding. By default UTF-8 is assumed.
    """
    def __init__(self, data=u'', *args, **kwargs):
        # NOTE: StringIO is an old-style class and super cannot be used!
        StringIO.__init__(self, smart_str(data))
        CDBase.__init__(self, *args, **kwargs)
        self.text_encoding = kwargs.get('text_encoding', None)

    @property
    def data(self):
        self.seek(0)
        return self.read()

    def write(self, data):
        if self.text_encoding is None:
            return StringIO.write(self, smart_str(data))
        else:
            return StringIO.write(self, smart_str(data, self.text_encoding))

    def read(self, size=None):
        if size is None:
            data = StringIO.read(self)
        else:
            data = StringIO.read(self, size)
        if self.text_encoding is not None:
            data = data.encode(self.text_encoding)
        return data


class CDAsciiTextBuffer(CDByteBuffer):
    """ Complex data text (ASCII) in-memory buffer (StringIO).
        To be used to hold generic ASCII text. The text payload
        is stored as a byte-stream and this class cannot hold
        characters outside of the 7-bit ASCII characters' range.

    Constructor parameters:
        data       optional initial payload ASCII string
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        headers    additional raw output HTTP headers encoded as a list
                   of <key>, <value> pairs (tuples).
        text_encoding   optional keyword parameter defining the input text
                   encoding. By default ASCII is assumed.
    """
    def __init__(self, data='', *args, **kwargs):
        CDByteBuffer.__init__(self, data.encode('ascii'), *args, **kwargs)
        self.text_encoding = kwargs.get('text_encoding', None)

    def write(self, data):
        if not isinstance(data, string_types):
            data = str(data)
        CDByteBuffer.write(self, data.encode('ascii'))

    def read(self, size=None):
        if size is None:
            data = CDByteBuffer.read(self)
        else:
            data = CDByteBuffer.read(self, size)
        if self.text_encoding not in ('ascii', 'utf-8'): # ASCII is a subset of UTF-8
            data = data.decode('ascii')
            if self.text_encoding is not None:
                data = data.encode(self.text_encoding)
        return data


class CDFileWrapper(CDBase):
    """ Complex data file (or file-like) object wrapper.

    Constructor parameters:
        file_object  mandatory seekable Python file or file-like object.
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        text_encoding optional source text file encoding
    """

    def __init__(self, file_object, *args, **kwargs):
        CDBase.__init__(self, *args, **kwargs)
        self._file = file_object
        self.text_encoding = kwargs.get('text_encoding', None)

    def __del__(self):
        if hasattr(self, "_file"):
            self.close()

    @property
    def data(self):
        self.seek(0)
        return self.read()

    def __getattr__(self, attr):
        if attr == "_file":
            raise AttributeError("Instance has no attribute '_file'")
        else:
            # Allow object to behave like a file.
            return getattr(self._file, attr)


class CDFile(CDFileWrapper):
    """ Complex data file.
        To be used to hold a generic (binary or text) byte-stream payload.
        NOTE: The file allows you to specify whether the file is
              temporary (will be automatically removed - by default)
              or permanent (preserved after object destruction).

    Constructor parameters:
        name       mandatory file-name
        mode       opening mode (passed to `open`, 'r' by default)
        buffering  buffering mode (passed to `open`, -1 by default)
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
        remove_file  optional  keyword argument defining whether the file
                   should be removed or not. Set to True by default.
    """

    def __init__(self, name, mode='rb', buffering=-1, *args, **kwargs):
        CDFileWrapper.__init__(
            self, open(name, mode, buffering), *args, **kwargs
        )
        self._remove_file = kwargs.get('remove_file', True)

    def __del__(self):
        if hasattr(self, "_file"):
            name = self.name
            self.close()
            if self._remove_file:
                remove(name)


class CDPermanentFile(CDFile):
    """ Complex data permanent file.
        To be used to hold a generic (binary or text) byte-stream payload.
        NOTE: This class preserves the actual file.

    Constructor parameters:
        name       mandatory file-name
        mode       opening mode (passed to `open`, 'r' by default)
        buffering  buffering mode (passed to `open`, -1 by default)
        mime_type  ComplexData mime-type
        encoding   ComplexData encoding
        schema     ComplexData XML schema (applicable XML only)
        format     an alternative format object defining the ComplexData
                   mime_type, encoding, and XML schema
        filename   optional raw output file-name set in the Content-Disposition
                   HTTP header.
    """

    def __init__(self, *args, **kwargs):
        kwargs['remove_file'] = False
        CDFile.__init__(self, *args, **kwargs)

#-------------------------------------------------------------------------------

class ComplexData(Parameter):
    """ Complex-data parameter class

    Constructor parameters:
        identifier  identifier of the parameter.
        title       optional human-readable name (defaults to identifier).
        abstract    optional human-readable verbose description.
        metadata    optional metadata (title/URL dictionary).
        optional    optional boolean flag indicating whether the input
                    parameter is optional or not.
        formats     List of supported formats.
        resolve_input_references Set this option to False not to resolve
                    input references. By default the references are
                    resolved (downloaded and parsed) transparently.
                    If set to False the references must be handled
                    by the process.
    """

    def __init__(self, identifier, formats, *args, **kwargs):
        super(ComplexData, self).__init__(identifier, *args, **kwargs)
        self.formats = OrderedDict()
        if isinstance(formats, Format):
            formats = (formats,)
        for frm in formats:
            self.formats[(frm.mime_type, frm.encoding, frm.schema)] = frm

    @property
    def default_format(self):
        """ Get default the default format. """
        return next(itervalues(self.formats))

    def get_format(self, mime_type, encoding=None, schema=None):
        """ Get format definition for the given mime-type and the optional
        encoding and schema.
        """
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
#        raise ValueError("Invalid format %r" % format)

    def parse(self, data, mime_type, schema, encoding, **opt):
        """ parse input complex data """
        format_ = self.get_format(mime_type, encoding, schema)
        if format_ is None:
            raise ValueError(
                "Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r" % (mime_type, encoding, schema)
            )
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
            # pylint: disable=redefined-variable-type
            parsed_data = CDTextBuffer(_unicode(data, text_encoding), **fattr)
            parsed_data.seek(0)
        else: # generic binary byte-stream
            parsed_data = CDByteBuffer(data, **fattr)
            if format_.encoding is not None:
                data_out = BytesIO()
                for chunk in format_.decode(parsed_data, **opt):
                    if isinstance(chunk, binary_type):
                        chunk = chunk.decode('utf-8')
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
            raise ValueError(
                "Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r" % (mime_type, encoding, schema)
            )
        if not format_.allows_xml_embedding:
            raise ValueError(
                "Selected format does not allows XML embedding! mime_type=%r, "
                "encoding=%r, schema=%r" % (mime_type, encoding, schema)
            )
        if isinstance(data, CDObject):
            data = data.data
        if format_.is_xml:
            if isinstance(data, etree._ElementTree):
                data = data.getroot()
            return deepcopy(data)
        elif format_.is_json:
            return json.dumps(data, ensure_ascii=False)
        elif format_.is_text:
            if not isinstance(data, string_types):
                data.seek(0)
                data = data.read()
            return data
        else: # generic binary byte-stream
            if format_.encoding is not None:
                data.seek(0)
                data_out = FastStringIO()
                # data_out.write(str(data.data,'utf-8'))
                for chunk in format_.encode(data):
                    if isinstance(chunk, binary_type):
                        chunk = chunk.decode('utf-8')

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
            raise ValueError(
                "Invalid format specification! mime_type=%r, "
                "encoding=%r, schema=%r" % (mime_type, encoding, schema)
            )
        if isinstance(data, CDObject):
            data = data.data
        if format_.is_xml:
            data = BytesIO(etree.tostring(
                data, pretty_print=False, xml_declaration=True,
                encoding=text_encoding
            ))
            content_type = "%s; charset=%s" % (
                format_.mime_type, text_encoding
            )
        elif format_.is_json:
            data = BytesIO(
                json.dumps(data, ensure_ascii=False).encode(text_encoding)
            )
            content_type = "%s; charset=%s" % (
                format_.mime_type, text_encoding
            )
        elif format_.is_text:
            if isinstance(data, (CDTextBuffer, CDAsciiTextBuffer)):
                data.text_encoding = text_encoding
            else:
                source_text_encoding = getattr(data, 'text_encoding', None)
                if source_text_encoding != text_encoding:
                    data = _rewind(data).read()
                    if source_text_encoding is not None:
                        data = data.decode(source_text_encoding)
                    data = BytesIO(data.encode(text_encoding))
            content_type = "%s; charset=%s" % (
                format_.mime_type, text_encoding
            )
        else:  # generic binary byte-stream
            if format_.encoding is not None:
                data_out = BytesIO()
                for chunk in format_.encode(_rewind(data)):
                    # if isinstance(chunk, binary_type):
                    #     chunk = str(chunk,'utf-8')
                    data_out.write(chunk)
                data = data_out
            content_type = format_.mime_type
        return _rewind(data), content_type


def _bytestring(data):
    if isinstance(data, str):
        return data
    raise TypeError("Byte string expected, %s received!" % type(data))


def _unicode(data, encoding):

    if isinstance(data, text_type):
        return data
    elif isinstance(data, bytes):
        return smart_str(data, encoding)
    raise TypeError(
        "Byte or Unicode string expected, %s received!" % type(data)
    )
