from eoxserver.core.decoders import (
    ZERO_OR_ONE, ONE_OR_MORE, ANY, SINGLE_VALUES, WrongMultiplicityException, 
    InvalidParameterException, MissingParameterException
)


class Parameter(object):
    key = None

    def __init__(self, key=None, type=None, separator=None, num=1, default=None,
                 locator=None):
        self.key = key
        self.type = type
        self.separator = separator
        self.num = num
        self.default = default
        self.locator = locator

    def __get__(self, decoder, decoder_class=None):
        multiple = self.num not in SINGLE_VALUES
        locator = self.locator or self.key

        # TODO: allow simple dicts aswell
        results = decoder._query_dict.getlist(self.key)
        
        count = len(results)

        if not multiple and count > 1:
            raise WrongMultiplicityException(
                "Expected at most one, got %d." % count, locator
            )

        elif self.num == 1 and count == 0:
            raise MissingParameterException(
                "Expected exactly one, got none.", locator
            )

        elif self.num == ONE_OR_MORE and count == 0:
            raise MissingParameterException(
                "Expected at least one, got none.", locator
            )

        elif isinstance(self.num, int) and count != self.num:
            raise WrongMultiplicityException(
                "Expected %d, got %d." % (self.num, count), locator
            )

        if multiple:
            try:
                return map(self.type, results)
            except Exception, e:
                raise InvalidParameterException(str(e), locator)

        elif self.num == ZERO_OR_ONE and count == 0:
            return self.default

        elif self.type:
            try:
                return self.type(results[0])
            except Exception, e:
                raise InvalidParameterException(str(e), locator)

        return results[0]


class DecoderMetaclass(type):
    def __init__(cls, name, bases, dct):
        for key, value in dct.items():
            if isinstance(value, Parameter) and value.key is None:
                value.key = key

        return super(DecoderMetaclass, cls).__init__(name, bases, dct)


class Decoder(object):
    __metaclass__ = DecoderMetaclass
    
    def __init__(self, query_dict):
        self._query_dict = query_dict
