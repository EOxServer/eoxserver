



class Parameter(object):
    def __init__(self, identifier=None, title=None, description=None, 
                 metadata=None):
        self.identifier = identifier
        self.title = title
        self.description = description
        self.metadata = metadata or ()


class LiteralData(Parameter):

    def __init__(self, identifier=None, type=str, uoms=None, default=None, 
                 allowed_values=None, values_reference=None, *args, **kwargs):
        super(LiteralData, self).__init__(identifier, *args, **kwargs)
        self.type = type
        self.uoms = uoms or ()
        self.default = default
        self.allowed_values = allowed_values or ()
        self.values_reference = values_reference


class ComplexData(Parameter):
    def __init__(self, identifier=None, format=None, *args, **kwargs):
        super(ComplexData, self).__init__(identifier, *args, **kwargs)
        self.format = format


class BoundingBoxData(Parameter):
    def __init__(self, identifier, *args, **kwargs):
        super(BoundingBoxData, self).__init__(identifier, *args, **kwargs)
        # TODO: CRSs


class Format(object):
    def __init__(self, mime_type, encoding=None, schema=None):
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema
