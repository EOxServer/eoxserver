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
    def identifier(self):
        """ The identifier, the process shall be identified with.
        """

    @property
    def title(self):
        """ The title of the process. Optional.
        """

    @property
    def description(self):
        """ A detailed description of the process. Optional.
        """

    @property
    def profiles(self):
        """ An iterable of URNs of any profiles this process adheres to. 
            Optional.
        """

    @property
    def metadata(self):
        """ An iterable of URLs of any additional metadata associated with the 
            process. Optional.
        """

    @property
    def version(self):
        """ The version of the process, if applicable. Optional.
        """

    @property
    def inputs(self):
        """ An iterable of key-value pairs, mapping the input identifiers to 
            their respective types.
        """

    @property
    def outputs(self):
        """ TODO: for process description only.
        """

    def execute(self, **kwargs):
        """ The main execution function for the process.
        """

