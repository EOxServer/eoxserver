import re

from decimal import Decimal

valid_mime_type = re.compile(r'^(\*|[a-zA-Z0-9._-]+)(/(\*|[a-zA-Z0-9._-]+))?$')


class AcceptableType:
    mime_type = None
    weight = Decimal(1)
    pattern = None

    def __init__(self, raw_mime_type):
        bits = raw_mime_type.split(';', 1)

        mime_type = bits[0]
        if not valid_mime_type.match(mime_type):
            raise ValueError('"%s" is not a valid mime type' % mime_type)

        tail = ''
        if len(bits) > 1:
            tail = bits[1]

        parameters = dict(
            parameter.split('=', 1)
            for parameter in tail.split(';')
        )

        self.mime_type = mime_type
        self.weight = get_weight(tail)
        self.pattern = get_pattern(mime_type)
        self.parameters = parameters

    def matches(self, mime_type):
        return self.pattern.match(mime_type)

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        display = self.mime_type
        if self.weight != Decimal(1):
            display += '; q=%0.2f' % self.weight

        return display

    def __repr__(self):
        return '<AcceptableType {0}>'.format(self)


def get_best_match(header, available_types):
    acceptable_types = parse_header(header)

    for acceptable_type in acceptable_types:
        for available_type in available_types:
            if acceptable_type.matches(available_type):
                return available_type

    return None


def get_best_acceptable_type(header, available_types):
    acceptable_types = parse_header(header)

    for acceptable_type in acceptable_types:
        for available_type in available_types:
            if acceptable_type.matches(available_type):
                return acceptable_type

    return None



def parse_header(header):
    raw_mime_types = header.split(',')
    mime_types = []
    for raw_mime_type in raw_mime_types:
        try:
            mime_types.append(AcceptableType(raw_mime_type.strip()))
        except ValueError:
            pass

    mime_types.sort(key=lambda x: x.weight, reverse=True)
    return mime_types


def get_weight(tail):
    match = re.search(q_match, tail)
    if match:
        try:
            return Decimal(match.group(1))
        except ValueError:
            pass

    # Default weight is 1
    return Decimal(1)
q_match = re.compile(r'(?:^|;)\s*q=([0-9.-]+)(?:$|;)')


def get_pattern(mime_type):
    return re.compile('^' + mime_type.replace('*', '[a-zA-Z0-9_.$#!%^*-]+') + '$')
