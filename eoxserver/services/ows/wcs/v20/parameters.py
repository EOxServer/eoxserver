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

from eoxserver.core.util.timetools import isoformat
from eoxserver.services.subset import Slice
from eoxserver.services.ows.wcs.parameters import (
    CoverageRenderParams, CoverageDescriptionRenderParams,
    WCSCapabilitiesRenderParams
)


class WCS20CapabilitiesRenderParams(WCSCapabilitiesRenderParams):
    def __init__(self, coverages, dataset_series=None, sections=None,
                 accept_languages=None, accept_formats=None,
                 updatesequence=None, request=None):
        super(WCS20CapabilitiesRenderParams, self).__init__(
            coverages, "2.0.1", sections, accept_languages, accept_formats,
            updatesequence, request
        )
        self._dataset_series = dataset_series

    dataset_series = property(lambda self: self._dataset_series)


class WCS20CoverageDescriptionRenderParams(CoverageDescriptionRenderParams):
    coverage_ids_key_name = "coverageid"

    def __init__(self, coverages):
        super(WCS20CoverageDescriptionRenderParams, self).__init__(
            coverages, "2.0.1"
        )


class WCS20CoverageRenderParams(CoverageRenderParams):
    def __init__(self, coverage, subsets=None, rangesubset=None, format=None,
                 outputcrs=None, mediatype=None, interpolation=None,
                 scalefactor=None, scales=None, encoding_params=None,
                 http_request=None):

        super(WCS20CoverageRenderParams, self).__init__(coverage, "2.0.1")
        self._subsets = subsets
        self._rangesubset = rangesubset or ()
        self._scalefactor = scalefactor
        self._scales = scales or ()
        self._format = format
        self._outputcrs = outputcrs
        self._mediatype = mediatype
        self._interpolation = interpolation
        self._encoding_params = encoding_params or {}
        self._http_request = http_request


    coverage_id_key_name = "coverageid"

    subsets       = property(lambda self: self._subsets)
    rangesubset   = property(lambda self: self._rangesubset)
    scalefactor   = property(lambda self: self._scalefactor)
    scales        = property(lambda self: self._scales)
    format        = property(lambda self: self._format)
    outputcrs     = property(lambda self: self._outputcrs)
    mediatype     = property(lambda self: self._mediatype)
    interpolation = property(lambda self: self._interpolation)
    encoding_params = property(lambda self: self._encoding_params)
    http_request  = property(lambda self: self._http_request)


    def __iter__(self):
        for k, v in super(WCS20CoverageRenderParams, self).__iter__():
            yield k, v

        for subset in self.subsets:
            yield self.subset_to_kvp(subset)

        if self.format:
            yield ("format", self.format)

        if self.outputcrs:
            yield ("outputcrs", self.outputcrs)

        if self.mediatype:
            yield ("mediatype", self.mediatype)

        if self.interpolation:
            yield ("interpolation", self.interpolation)


    def subset_to_kvp(self, subset):
        temporal_format = lambda v: ('"%s"' % isoformat(v) if v else "*")
        spatial_format = lambda v: (str(v) if v is not None else "*")

        frmt = temporal_format if subset.is_temporal else spatial_format

        if isinstance(subset, Slice):
            value = frmt(subset.value)
        else:
            value = "%s,%s" % (frmt(subset.low), frmt(subset.high))

        crs = self.subsets.crs
        if crs:
            return "subset", "%s,%s(%s)" % (subset.axis, crs, value)
        else:
            return "subset", "%s(%s)" % (subset.axis, value)
