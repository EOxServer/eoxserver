import sys

ZERO_OR_ONE = "?"
ONE_OR_MORE = "+"
ANY = "*"

SINGLE_VALUES = (ZERO_OR_ONE, 1)


class DecodingException(Exception):
    pass


class WrongMultiplicity(DecodingException):
    pass


class NoChoiceResultException(DecodingException):
    pass


class ExclusiveException(DecodingException):
    pass


# Compound fields


class Choice(object):
    """ Tries all given choices until one does return something.
    """

    def __init__(self, *choices):
        self.choices = choices


    def __get__(self, decoder, decoder_class=None):
        for choice in self.choices:
            try: 
                return choice.__get__(decoder, decoder_class)
            except:
                continue
        raise


class Exclusive(object):
    """ For mutual exclusive Parameters.
    """

    def __init__(self, *choices):
        self.choices = choices


    def __get__(self, decoder, decoder_class=None):
        result = None
        num = 0
        for choice in self.choices:
            try: 
                result = choice.__get__(decoder, decoder_class)
                num += 1
            except:
                continue

        if num != 1:
            raise ExclusiveException

        return result


class Concatenate(object):
    def __init__(self, *choices, **kwargs):
        self.choices = choices
        self.allow_errors = kwargs.get("allow_errors", True)
        

    def __get__(self, decoder, decoder_class=None):
        result = []
        for choice in self.choices:
            try: 
                value = choice.__get__(decoder, decoder_class)
                if isinstance(value, (list, tuple)):
                    result.extend(value)
                else:
                    result.append(value)
            except Exception, e:
                if self.allow_errors:
                    # swallow exception
                    continue

                exc_info = sys.exc_info()
                raise exc_info[0], exc_info[1], exc_info[2]

        return result


# Type conversion helpers


class typelist(object):
    """ Helper for XMLDecoder schemas that expect a string that represents a 
        list of a type separated by some separator.
    """
    
    def __init__(self, typ, separator=" "):
        self.typ = typ
        self.separator = separator
        
    
    def __call__(self, value):
        return map(self.typ, value.split(self.separator))


class fixed(object):
    """ Helper for parameters that are expected to be have a fixed value and 
        raises a ValueError if not.
    """

    def __init__(self, value, case_sensitive=True):
        self.value = value if case_sensitive else value.lower()
        self.case_sensitive = case_sensitive


    def __call__(self, value):
        compare = value if self.case_sensitive else value.lower()
        if self.value != compare:
            raise ValueError("Value mismatch, expected %s, got %s." %
                (self.value, value)
            )

        return value


def lower(value):
    return value.lower()


def upper(value):
    return value.upper()
