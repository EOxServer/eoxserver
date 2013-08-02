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
