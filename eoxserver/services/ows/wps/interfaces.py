#-------------------------------------------------------------------------------
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

class AsyncBackendInterface(object):
    """ Interface class for asynchronous WPS backends.
        NOTE: Only one async. backend at time is allowed to be configured.
    """

    @property
    def supported_versions(self):
        """ A list of versions of the WPS standard supported by the backend.
        """

    def enqueue(self, identifier, raw_inputs, response_document, version):
        """ Enqueue the WPS request for asynchronous processing.

            Once enqued the process shall be managed exclusively by the async.
            backend.

            The request is defined by the process's ``identifier``,
            ``raw_inputs`` (before the decoding and resolution
            of the references), and the ``response_document`` (holding
            the outputs' parameters).  The ``version`` of the WPS standard
            to be used.  The method returns a URL (string) of the asynchronous
            execute response.
        """


class ProcessInterface(object):
    """ Interface class for processes offered, described and executed by
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
            (Content of the the abstract in the WPS process description.)
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
            The type can be either one of the supported native python types
            (automatically converted to a ``LiteralData`` object) or an instance
            of one of the data-specification classes (``LiteralData``,
            ``BoundingBoxData``, or ``ComplexData``).  Mandatory.
        """

    @property
    def outputs(self):
        """ A dict mapping the outputs' identifiers to their respective types.
            The type can be either one of the supported native python types
            (automatically converted to a ``LiterData`` object) or an instance
            of one of the data-specification classes (``LiterData``,
            ``BoundingBoxData``, or ``ComplexData``).  Mandatory.
        """

    def execute(self, **kwargs):
        """ The main execution function for the process. The ``kwargs`` are the
            parsed input inputs (using the keys as defined by the ``inputs``)
            and the Complex Data format requests (using the keys as defined by
            the ``outputs``).
            The method is expected to return a dictionary of the output values
            (using the keys as defined by the ``outputs``). In case of only
            one output item defined by the ``outputs``, one output value
            is allowed to be returned directly.
        """
