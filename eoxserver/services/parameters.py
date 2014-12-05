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


class RenderParameters(object):
    """ Abstract base class for render parameters
    """

    def __iter__(self):
        """ Yields all kvps as key-value pairs (string, string).
        """


class VersionedParams(object):
    def __init__(self, version):
        self._version = version

    @property
    def version(self):
        return self._version

    def __iter__(self):
        yield ("version", self.version)


class CapabilitiesRenderParams(object):
    def __init__(self, coverages, version, sections=None, accept_languages=None,
                 accept_formats=None, updatesequence=None, request=None):
        self._coverages = coverages
        self._version = version
        self._sections = sections or ()
        self._accept_languages = accept_languages or ()
        self._accept_formats = accept_formats or ()
        self._updatesequence = updatesequence
        self._request = request

    coverages        = property(lambda self: self._coverages)
    version          = property(lambda self: self._version)
    sections         = property(lambda self: self._sections)
    accept_languages = property(lambda self: self._accept_languages)
    accept_formats   = property(lambda self: self._accept_formats)
    updatesequence   = property(lambda self: self._updatesequence)

    @property
    def request(self):
        return self._request

    @request.setter
    def request(self, value):
        self._request = value

    def __iter__(self):
        yield "request", "GetCapabilities"

        if self.sections:
            yield "sections", ",".join(self.sections)

        if self.accept_languages:
            yield "acceptlanguages", ",".join(self.accept_languages)

        if self.accept_formats:
            yield "acceptformats", ",".join(self.accept_formats)

        if self.updatesequence:
            yield "updatesequence", self.updatesequence
