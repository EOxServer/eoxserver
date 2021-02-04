#-------------------------------------------------------------------------------
#
#  WPS Complex Data codecs (encoders/decoders)
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Martin Paces <martin.paces@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2014 EOX IT Services GmbH
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

from base64 import (
    standard_b64encode, standard_b64decode, urlsafe_b64encode, urlsafe_b64decode,
)


class Codec(object):
    """ Base complex data codec."""
    encoding = None

    @staticmethod
    def encode(file_in, **opt):
        """ Encoding generator."""
        raise NotImplementedError

    @staticmethod
    def decode(file_in, **opt):
        """ Encoding generator."""
        raise NotImplementedError


class CodecBase64(Codec):
    """ Base64 codec """
    encoding = 'base64'

    @staticmethod
    def encode(file_in, urlsafe=False, **opt):
        """ Encoding generator."""
        b64encode = urlsafe_b64encode if urlsafe else standard_b64encode
        dlm = b""

        for data in iter(lambda: file_in.read(57), b''):
            yield dlm
            yield b64encode(data)
            dlm = b"\r\n"

    @staticmethod
    def decode(file_in, urlsafe=False, **opt):
        """ Decoding generator."""
        b64decode = urlsafe_b64decode if urlsafe else standard_b64decode
        for data in file_in:
            yield b64decode(data)


class CodecRaw(Codec):
    """ Data encoder class."""
    encoding = None

    @staticmethod
    def encode(file_in, **opt):
        """ Encoding generator."""
        for data in iter(lambda: file_in.read(65536), ''):
            yield data

    @staticmethod
    def decode(file_in, **opt):
        """ Decoding generator."""
        for data in iter(lambda: file_in.read(65536), ''):
            yield data
