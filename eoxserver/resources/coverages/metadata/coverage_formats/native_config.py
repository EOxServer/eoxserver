#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Fabian Schindler <fabian.schindler@eox.at>
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

import os.path
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser

from eoxserver.core.decoders import config
from django.utils.six import string_types

class NativeConfigFormatReader(object):
    def open_reader(self, obj):
        if isinstance(obj, string_types):
            try:
                parser = RawConfigParser()
                if os.path.exists(obj):
                    parser.read((obj,))
                else:
                    parser.readfp(StringIO(obj))

                return NativeConfigReader(parser)
            except:
                pass
        return None

    def test(self, obj):
        try:
            reader = self.open_reader(obj)
            reader.range_type_name
            return True
        except:
            return False

    def get_format_name(self, obj):
        return "native_config"

    def read(self, obj):
        reader = self.open_reader(obj)
        if reader:
            return {
                "range_type_name": reader.range_type_name
            }


class NativeConfigReader(config.Reader):
    range_type_name = config.Option(section="range_type")
