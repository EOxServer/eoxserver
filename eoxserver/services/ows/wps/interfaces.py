#-------------------------------------------------------------------------------
# $Id$
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


class ProcessInterface(object):
    """ Interface class for processes, advertised, described and executed by
        the WPS.
    """

    @property
    def version(self):
        """ The version of the process, if applicable. Optional.
            When omitted it defaults to '1.0.0'.
        """

    @property
    def identifier(self):
        """ An identifier (URI) of the process. Optional.
            When omitted it defaults to the process' class-name.
        """

    @property
    def title(self):
        """ A human-readable title of the process. Optional. When omitted it
            defaults to the process identifier.
        """

    @property
    def description(self):
        """ A human-readable detailed description of the process. Optional.
        """

    @property
    def profiles(self):
        """ A iterable of URNs of WPS application profiles this process
            adheres to. Optional.
        """

    @property
    def metadata(self):
        """ A dict of title/URL meta-data pairs associated with the process.
            Optional.
        """

    @property
    def wsdl(self):
        """ A URL of WSDL document describing this process. Optional.
        """

    @property
    def inputs(self):
        """ A dict mapping the inputs' identifiers to their respective types.
            The type can be either one of the supported python types
            (automatically converted to ``LiterData`` type) or an instance
            of ``LiterData``, ``BoundingBoxData``, or ``ComplexData``.
            Mandatory.
        """

    @property
    def outputs(self):
        """ A dict mapping the outputs' identifiers to their respective types.
            The type can be either one of the supported python types
            (automatically converted to ``LiterData`` type) or an instance
            of ``LiterData``, ``BoundingBoxData``, or ``ComplexData``.
            Mandatory.
        """


    def execute(self, **kwargs):
        """ The main execution function for the process. The ``kwargs`` are the
            parsed input inputs, as names by the ``inputs`` property. The
            function must return a dict, mapping the output identifiers to the
            actual outputs.
            TODO: allow direct returning of single values when only one output?
        """

# TODO: sync/async processes
# TODO: complex data handling

#    def decode_complex_input(self, identifier, raw_value, mime_type, encoding, schema):
#        """ Decodes a complex input before it is passed to the execution
#            function.
#        """
#
#    def encode_complex_output(self, identifier, value, mime_type, encoding, schema):
#        """ Encode a complex output in a format specified by a mime-type.
#            The function must be able to handle all complex outputs with all
#            formats as stated in the `outputs` property.
#        """
