#-------------------------------------------------------------------------------
#
#  Response form objects.
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

try:
    # available in Python 2.7+
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict
from django.utils.six import iteritems

from .base import ParamMetadata


class Output(ParamMetadata):
    # pylint: disable=too-few-public-methods,too-many-arguments
    """ Requested output definition.

    Constructor parameters:
        identifier   output identifier
        title        output title (human-readable name)
        abstract     output abstract (human-readable description)
        uom          output LiteralData UOM
        crs          output BoundingBox CRS
        mime_type    output ComplexData mime-type
        encoding     output ComplexData encoding
        schema       output ComplexData schema
        as_reference  boolean flag indicating whether the output should
                     passed as a reference op directly in the response.
    """
    def __init__(self, identifier, title=None, abstract=None, uom=None,
                 crs=None, mime_type=None, encoding=None, schema=None,
                 as_reference=False):
        ParamMetadata.__init__(
            self, identifier, title, abstract, uom, crs,
            mime_type, encoding, schema
        )
        self.as_reference = as_reference


class ResponseForm(OrderedDict):
    """ Response form defined as an ordered dictionary of the output
    definitions.
    """

    def __init__(self):
        super(ResponseForm, self).__init__()

    def set_output(self, output):
        """ Set (insert) a new definition output."""
        self[output.identifier] = output

    def get_output(self, identifier):
        """ Get an output for the given output identifier.
            An instance of the Output object is always returned.
        """
        output = self.get(identifier, None)
        if not output:
            output = Output(identifier)
        return output


class ResponseDocument(ResponseForm):
    """ Object representation of the (WPS Execute) response document.

    Constructor parameters (meaning described in  OGC 05-007r7, Table 50):
        lineage         boolean flag, set to True to print the lineage
        status          boolean flag, set to True to update status
        store_response  boolean flag, set to True to store execute response
    """
    raw = False

    def __init__(self, lineage=False, status=False, store_response=False):
        super(ResponseDocument, self).__init__()
        self.lineage = lineage
        self.status = status
        self.store_response = store_response

    def __reduce__(self): # NOTE: needed for correct async-WPS request pickling
        return (
            self.__class__, (self.lineage, self.status, self.store_response),
            None, None, iteritems(self)
        )

    def __str__(self):
        return (
            "ResponseDocument(lineage=%s, status=%s, store_response=%s)[%s]" %
            (self.lineage, self.status, self.store_response, " ,".join(
                repr(k) for k in self.keys()
            ))
        )


class RawDataOutput(ResponseForm):
    """ Object representation of the raw output response.

    Constructor parameters:
        output      name of the requested output parameter
    """
    raw = True
    lineage = False
    status = False
    store_response = False

    def __init__(self, output):
        super(RawDataOutput, self).__init__()
        self.set_output(output)

    def __str__(self):
        return (
            "RawDataOutput()[%s]" % " ,".join(repr(k) for k in self.keys())
        )
