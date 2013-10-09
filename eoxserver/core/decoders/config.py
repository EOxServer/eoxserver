#-------------------------------------------------------------------------------
# $Id$
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


import sys
from ConfigParser import NoOptionError, NoSectionError


def section(name):
    frame = sys._getframe(1)
    locals_ = frame.f_locals

    # Some sanity checks
    assert locals_ is not frame.f_globals and '__module__' in locals_, \
           'implements() can only be used in a class definition'

    locals_["section"] = name


class Option(object):

    def __init__(self, key=None, type=None, separator=None, required=False, default=None, section=None):
        self.key = key # needs to be set by the reader metaclass
        self.type = type
        self.separator = separator
        self.required = required
        self.default = default

        if section is None:
            frame = sys._getframe(1)
            section = frame.f_locals.get("section")

        self.section = section


    def __get__(self, reader, objtype=None):
        section = self.section or reader.section
        try:
            if self.type is bool:
                raw_value = reader._config.getboolean(section, self.key)
            else:
                raw_value = reader._config.get(section, self.key)
        except (NoOptionError, NoSectionError), e:
            if not self.required:
                return self.default
            raise e
        
        if self.separator is not None:
            return map(self.type, raw_value.split(self.separator))

        elif self.type:
            return self.type(raw_value)

        else:
            return raw_value


    def check(self, reader):
        # TODO: perform checking of config
        #  - required option?
        #  - can parse type?
        pass


class ReaderMetaclass(type):
    def __init__(cls, name, bases, dct):
        for key, value in dct.items():
            if isinstance(value, Option) and value.key is None:
                value.key = key

        return super(ReaderMetaclass, cls).__init__(name, bases, dct)


class Reader(object):
    __metaclass__ = ReaderMetaclass

    section = None

    def __init__(self, config):
        self._config = config
