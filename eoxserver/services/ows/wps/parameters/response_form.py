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

from .base import ParamMetadata

#-------------------------------------------------------------------------------

class Output(ParamMetadata):
    """ Output request."""

    def __init__(self, identifier, title=None, abstract=None, uom=None,
                    crs=None, mime_type=None, encoding=None, schema=None,
                    as_reference=False):
        ParamMetadata.__init__(self, identifier, title, abstract, uom, crs,
                                                   mime_type, encoding, schema)
        self.as_reference = as_reference


class ResponseForm(OrderedDict):
    """ Response form defined as an ordered dict. of the output definitions."""

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
    """ Object representation of the response document."""
    raw = False

    def __init__(self, lineage=False, status=False, store_response=False):
        super(ResponseDocument, self).__init__()
        self.lineage = lineage
        self.status = status
        self.store_response = store_response


class RawDataOutput(ResponseForm):
    raw = True

    def __init__(self, output):
        super(RawDataOutput, self).__init__()
        self.set_output(output)
