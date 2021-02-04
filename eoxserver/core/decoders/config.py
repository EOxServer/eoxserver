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

""" This module contains facilities to help decoding configuration files.
It relies on the :mod:`ConfigParser` module for actually reading the file.
"""

import sys

try:
    from ConfigParser import NoOptionError, NoSectionError
except ImportError:
    from configparser import NoOptionError, NoSectionError

from django.utils.six import with_metaclass


def section(name):
    """ Helper to set the section of a :class:`Reader`.
    """
    frame = sys._getframe(1)
    locals_ = frame.f_locals

    # Some sanity checks
    assert locals_ is not frame.f_globals and '__module__' in locals_, \
        'implements() can only be used in a class definition'

    locals_["section"] = name


class Option(property):
    """ The :class:`Option` is used as a :class:`property` for :class:`Reader`
        subclasses.

        :param key: the lookup key; defaults to the property name of the
                    :class:`Reader`.
        :param type: the type to parse the raw value; by default the raw
                     string is returned
        :param separator: the separator for list options; by default no list
                          is assumed
        :param required: if ``True`` raise an error if the option does not
                         exist
        :param default: the default value
        :param section: override the section for this option
    """

    def __init__(self, key=None, type=None, separator=None, required=False,
                 default=None, section=None, doc=None):

        super(Option, self).__init__(self.fget)

        self.key = key  # needs to be set by the reader metaclass
        self.type = type
        self.separator = separator
        self.required = required
        self.default = default

        if section is None:
            frame = sys._getframe(1)
            section = frame.f_locals.get("section")

        self.section = section

    def fget(self, reader):
        
        section = self.section or reader.section
        try:
            if self.type is bool:
                raw_value = reader._config.getboolean(section, self.key)
            else:
                raw_value = reader._config.get(section, self.key)
        except (NoOptionError, NoSectionError) as e:
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

                value.__doc__ = "%s.%s" % (value.section, value.key)

        super(ReaderMetaclass, cls).__init__(name, bases, dct)


class Reader(with_metaclass(ReaderMetaclass, object)):
    """ Base class for config readers.

    :param config: an instance of :class:`ConfigParser.RawConfigParser`

    Readers should be used as such:
    ::

        from ConfigParser import RawConfigParser
        try:
            from cStringIO import StringIO
        except ImportError:
            from io import StringIO
        from textwrap import dedent
        from eoxserver.core.decoders import config

        class ExampleReader(config.Reader):
            section = "example_section"
            string_opt = config.Option()
            string_list_opt = config.Option(separator=",")
            integer_opt = config.Option(type=int)

            section = "other_section"
            mandatory_opt = config.Option(required=True)
            optional_opt = config.Option(default="some_default")

            special_section_opt = config.Option(section="special_section")

        f = StringIO(dedent('''
            [example_section]
            string_opt = mystring
            string_list_opt = my,string,list
            integer_opt = 123456
            [other_section]
            mandatory_opt = mandatory_value
            # optional_opt = no value

            [special_section]
            special_section_opt = special_value
        '''))

        parser = RawConfigParser()
        parser.readfp(f)
        reader = ExampleReader(parser)

        print reader.string_opt
        print reader.string_list_opt
        print reader.integer_opt
        print reader.mandatory_opt
        print reader.optional_opt
        ...
    """

    __metaclass__ = ReaderMetaclass

    section = None

    def __init__(self, config):
        self._config = config
