#-------------------------------------------------------------------------------
#
#  WPS input and output parameters' base class
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

# NOTE: Currently, the inputs parameters are not allowed to be present
#       more that once (maxOccurs=1) per request. These input parameters
#       are, by default, mandatory (minOccur=1). Unpon explicit requests
#       the parameters can be made optional (minOccur=0).
#
#       Although not explicitely mentioned by the WPS 1.0.0 standard
#       it is a common practice that the outputs do not appear more than
#       once per output (maxOccurs=1). When the exlicit specification
#       of the outputs is omitted in the request all process output are
#       contained in the default respose.

class BaseParamMetadata(object):
    """ Common metadata base of all parameter classes."""

    def __init__(self, identifier, title=None, abstract=None):
        self.identifier = identifier
        self.title = title
        self.abstract = abstract


class ParamMetadata(BaseParamMetadata):
    """ Common metadata of the execute request parameters."""
    
    def __init__(self, identifier, title=None, abstract=None, uom=None,
                 crs=None, mime_type=None, encoding=None, schema=None):
        super(ParamMetadata, self).__init__(identifier, title, abstract)
        self.uom = uom
        self.crs = crs
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema


class Parameter(BaseParamMetadata):
    """ Base parameter class used by the process definition."""

    def __init__(self, identifier=None, title=None, abstract=None,
                 metadata=None, optional=False):
        """ Object constructor.

            Parameters:
                identifier  idetnfier of the parameter.
                title       optional human-readable name (defaults to idetfier).
                abstract    optional human-readable verbose description.
                metadata    optional metadata (title/URL dictionary).
                optional    optional boolean flag indicating whether the input
                            parameter is optional or not.
        """
        super(Parameter, self).__init__(identifier, title, abstract)
        self.metadata = metadata or {}
        self.is_optional = optional
