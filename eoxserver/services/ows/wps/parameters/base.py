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
# pylint: disable=too-few-public-methods, too-many-arguments

# NOTE: Currently, the inputs parameters are not allowed to be present
#       more that once (maxOccurs=1) per request. These input parameters
#       are, by default, mandatory (minOccur=1). The inputs can be configured
#       as optional (minOccur=0).
#
#       Although not explicitly mentioned by the WPS 1.0.0 standard,
#       it is a common practice that the outputs do not appear more than
#       once in the response (maxOccurs=1).
#       When the explicit specification of the outputs is omitted in the request
#       all process outputs are contained in the default response.

class BaseParamMetadata(object):
    """ Common metadata base of all parameter classes.

    Constructor parameters:
        identifier   item identifier
        title        item title (human-readable name)
        abstract     item abstract (human-readable description)
    """
    def __init__(self, identifier, title=None, abstract=None):
        self.identifier = identifier
        self.title = title
        self.abstract = abstract


class ParamMetadata(BaseParamMetadata):
    """ Common metadata of the execute request parameters.

    Constructor parameters:
        identifier   item identifier
        title        item title (human-readable name)
        abstract     item abstract (human-readable description)
        uom          item LiteralData UOM
        crs          item BoundingBox CRS
        mime_type    item ComplexData mime-type
        encoding     item ComplexData encoding
        schema       item ComplexData schema
    """

    def __init__(self, identifier, title=None, abstract=None, uom=None,
                 crs=None, mime_type=None, encoding=None, schema=None):
        super(ParamMetadata, self).__init__(
            identifier=identifier, title=title, abstract=abstract
        )
        self.uom = uom
        self.crs = crs
        self.mime_type = mime_type
        self.encoding = encoding
        self.schema = schema


class Parameter(BaseParamMetadata):
    """ Base parameter class used by the process definition.

    Constructor parameters:
        identifier  identifier of the parameter.
        title       optional human-readable name (defaults to identifier).
        abstract    optional human-readable verbose description.
        metadata    optional metadata (title/URL dictionary).
        optional    optional boolean flag indicating whether the input
                    parameter is optional or not.
        resolve_input_references Set this option to False not to resolve
                    input references. By default the references are
                    resolved (downloaded and parsed) transparently.
                    If set to False the references must be handled
                    by the process.
    """

    def __init__(self, identifier=None, title=None, abstract=None,
                 metadata=None, optional=False, resolve_input_references=True):
        super(Parameter, self).__init__(
            identifier=identifier, title=title, abstract=abstract
        )
        self.metadata = metadata or {}
        self.is_optional = optional
        self.resolve_input_references = resolve_input_references
