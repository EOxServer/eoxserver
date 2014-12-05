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


class WCSCapabilitiesRendererInterface(object):
    """ Interface for WCS Capabilities renderers.
    """

    def render(self, params):
        """ Render the capabilities including information about the given 
            coverages.
        """

    def supports(self, params):
        """ Returns a boolean value to indicate whether or not the renderer is 
            able to render the capabilities with the given parameters.
        """


class WCSCoverageDescriptionRendererInterface(object):
    """ Interface for coverage description renderers.
    """

    def render(self, params):
        """ Render the description of the given coverages.
        """

    def supports(self, params):
        """ Returns a boolean value to indicate whether or not the renderer is 
            able to render the coverage and the given WCS version.
        """


class WCSCoverageRendererInterface(object):
    """ Interface for coverage renderers.
    """

    def render(self, params):
        """ Render the coverage with the given parameters.
        """

    def supports(self, params):
        """ Returns a boolean value to indicate whether or not the renderer is 
            able to render the coverage with the given parameters.
        """


class PackageWriterInterface(object):
    """ Interface for package writers.
    """

    def supports(self, format, params):
        """ Return a boolen value, whether or not a writer supports a given 
            format.
        """

    def create_package(self, filename, format, params):
        """ Create a package, which the encoder can later add items to with the 
            `cleanup` and `add_to_package` method.
        """

    def cleanup(self, package):
        """ Perform any necessary cleanups, like closing files, etc.
        """

    def add_to_package(self, package, file_obj, size, location):
        """ Add the file object to the package, that is returned by the 
            `create_package` method.
        """

    def get_mime_type(self, package, format, params):
        """ Retrieve the output mime type for the given package and/or format
            specifier.
        """

    def get_file_extension(self, package, format, params):
        """ Retrieve the file extension for the given package and format 
            specifier.
        """


class EncodingExtensionInterface(object):
    def supports(self, format, options):
        """ Return a boolen value, whether or not an encoding extension 
            supports a given format.
        """

    def parse_encoding_params(self, request):
        """ Return a dict, containing all additional encoding parameters from a 
            given request.
        """
