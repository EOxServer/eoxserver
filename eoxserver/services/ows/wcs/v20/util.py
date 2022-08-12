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


import re
from datetime import datetime

from lxml.builder import ElementMaker
from django.utils.six import string_types

from eoxserver.core.util.xmltools import NameSpace, NameSpaceMap, ns_xsi
from eoxserver.core.util.timetools import parse_iso8601
from eoxserver.services.subset import Trim, Slice, is_temporal, all_axes
from eoxserver.services.gml.v32.encoders import (
    ns_gml, ns_gmlcov, ns_om, ns_eop, GML, GMLCOV, OM, EOP
)
from eoxserver.services.ows.common.v20.encoders import ns_xlink, ns_ows, OWS
from eoxserver.services.exceptions import (
    InvalidSubsettingException, InvalidAxisLabelException,
    NoSuchFieldException, InvalidFieldSequenceException,
    InterpolationMethodNotSupportedException, InvalidScaleFactorException,
    InvalidScaleExtentException, ScaleAxisUndefinedException
)


# namespace declarations
ns_ogc = NameSpace("http://www.opengis.net/ogc", "ogc")
ns_wcs = NameSpace("http://www.opengis.net/wcs/2.0", "wcs")
ns_crs = NameSpace("http://www.opengis.net/wcs/crs/1.0", "crs")
ns_rsub = NameSpace("http://www.opengis.net/wcs/range-subsetting/1.0", "rsub")
ns_eowcs = NameSpace("http://www.opengis.net/wcs/wcseo/1.0", "wcseo",
                     "http://schemas.opengis.net/wcs/wcseo/1.0/wcsEOAll.xsd")
ns_wcseo11 = NameSpace("http://www.opengis.net/wcs/wcseo/1.1", "wcseo11",
                       "http://schemas.opengis.net/wcs/wcseo/1.1/wcsEOAll.xsd")
ns_swe = NameSpace("http://www.opengis.net/swe/2.0", "swe")
ns_int = NameSpace("http://www.opengis.net/wcs/interpolation/1.0", "int")
ns_scal = NameSpace("http://www.opengis.net/wcs/scaling/1.0", "scal")

# namespace map
nsmap = NameSpaceMap(
    ns_xlink, ns_ogc, ns_ows, ns_gml, ns_gmlcov, ns_wcs, ns_crs, ns_rsub,
    ns_eowcs, ns_om, ns_eop, ns_swe, ns_int, ns_scal,
)
nsmapGetEoCoverageSet = NameSpaceMap(
    ns_wcs, ns_crs, ns_int, ns_scal, ns_wcseo11
)

# Element factories

WCS = ElementMaker(namespace=ns_wcs.uri, nsmap=nsmap)
CRS = ElementMaker(namespace=ns_crs.uri, nsmap=nsmap)
EOWCS = ElementMaker(namespace=ns_eowcs.uri, nsmap=nsmap)
SWE = ElementMaker(namespace=ns_swe.uri, nsmap=nsmap)
INT = ElementMaker(namespace=ns_int.uri, nsmap=nsmap)


SUBSET_RE = re.compile(r'(\w+)\(([^,]*)(,([^)]*))?\)')
SCALEAXIS_RE = re.compile(r'(\w+)\(([^)]*)\)')
SCALESIZE_RE = SCALEAXIS_RE
SCALEEXTENT_RE = re.compile(r'(\w+)\(([^:]*):([^)]*)\)')


class RangeSubset(list):
    def get_band_indices(self, range_type, offset=0):
        current_idx = -1
        all_bands = range_type[:]

        for subset in self:
            if isinstance(subset, string_types):
                # slice, i.e single band
                start = stop = subset

            else:
                start, stop = subset

            start_idx = self._find(all_bands, start)
            if start != stop:
                stop_idx = self._find(all_bands, stop)
                if stop_idx <= start_idx:
                    raise IllegalFieldSequenceException(
                        "Invalid interval '%s:%s'." % (start, stop), start
                    )

                # expand interval to indices
                for i in range(start_idx, stop_idx+1):
                    yield i + offset

            else:
                # return the item
                yield start_idx + offset


    def _find(self, all_bands, name):
        for i, band in enumerate(all_bands):
            if band.identifier == name:
                return i
        raise NoSuchFieldException("Field '%s' does not exist." % name, name)


class Scale(object):
    """ Abstract base class for all Scaling operations.
    """
    def __init__(self, axis):
        self.axis = axis


class ScaleAxis(Scale):
    """ Scale a single axis by a specific value.
    """
    def __init__(self, axis, scale):
        super(ScaleAxis, self).__init__(axis)
        self.scale = scale


class ScaleSize(Scale):
    """ Scale a single axis to a specific size.
    """
    def __init__(self, axis, size):
        super(ScaleSize, self).__init__(axis)
        self.size = size


class ScaleExtent(Scale):
    """ Scale a single axis to a specific extent.
    """
    def __init__(self, axis, low, high):
        super(ScaleExtent, self).__init__(axis)
        self.low = low
        self.high = high


class SectionsMixIn(object):
    """ Mix-in for request decoders that use sections.
    """

    def section_included(self, *sections):
        """ See if one of the sections is requested.
        """
        if not self.sections:
            return True

        requested_sections = [s.lower() for s in self.sections]

        for section in map(lambda s: s.lower(), sections):
            section = section.lower()
            if "all" in requested_sections or section in requested_sections:
                return True

        return False


def parse_subset_kvp(string):
    """ Parse one subset from the WCS 2.0 KVP notation.
    """

    try:
        match = SUBSET_RE.match(string)
        if not match:
            raise Exception("Could not parse input subset string.")

        axis = match.group(1)
        parser = get_parser_for_axis(axis)

        if match.group(4) is not None:
            return Trim(
                axis, parser(match.group(2)), parser(match.group(4))
            )
        else:
            return Slice(axis, parser(match.group(2)))
    except InvalidAxisLabelException:
        raise
    except Exception as e:
        raise InvalidSubsettingException(str(e))


def parse_range_subset_kvp(string):
    """ Parse a rangesubset structure from the WCS 2.0 KVP notation.
    """

    rangesubset = RangeSubset()
    for item in string.split(","):
        if ":" in item:
            rangesubset.append(item.split(":"))
        else:
            rangesubset.append(item)

    return rangesubset


def parse_scaleaxis_kvp(string):
    """ Parses the KVP notation of a single scale axis.
    """

    match = SCALEAXIS_RE.match(string)
    if not match:
        raise Exception("Could not parse input scale axis string.")

    axis = match.group(1)
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        value = float(match.group(2))
    except ValueError:
        raise InvalidScaleFactorException(match.group(2))

    return ScaleAxis(axis, value)


def parse_scalesize_kvp(string):
    """ Parses the KVP notation of a single scale size.
    """

    match = SCALESIZE_RE.match(string)
    if not match:
        raise Exception("Could not parse input scale size string.")

    axis = match.group(1)
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        value = int(match.group(2))
    except ValueError:
        raise InvalidScaleFactorException(match.group(2))

    return ScaleSize(axis, value)


def parse_scaleextent_kvp(string):
    """ Parses the KVP notation of a single scale extent.
    """

    match = SCALEEXTENT_RE.match(string)
    if not match:
        raise Exception("Could not parse input scale extent string.")

    axis = match.group(1)
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        low = int(match.group(2))
        high = int(match.group(3))
    except ValueError:
        raise InvalidScaleFactorException(match.group(3))

    if low >= high:
        raise InvalidScaleExtentException(low, high)

    return ScaleExtent(axis, low, high)


def parse_subset_xml(elem):
    """ Parse one subset from the WCS 2.0 XML notation. Expects an lxml.etree
        Element as parameter.
    """

    try:
        dimension = elem.findtext(ns_wcs("Dimension"))
        parser = get_parser_for_axis(dimension)
        if elem.tag == ns_wcs("DimensionTrim"):
            return Trim(
                dimension,
                parser(elem.findtext(ns_wcs("TrimLow"))),
                parser(elem.findtext(ns_wcs("TrimHigh")))
            )
        elif elem.tag == ns_wcs("DimensionSlice"):
            return Slice(
                dimension,
                parser(elem.findtext(ns_wcs("SlicePoint")))
            )
    except Exception as e:
        raise InvalidSubsettingException(str(e))


SUPPORTED_INTERPOLATIONS = (
    "average", "nearest-neighbour", "bilinear", "cubic", "cubic-spline",
    "lanczos", "mode"
)

def parse_interpolation(raw):
    """ Returns a unified string denoting the interpolation method used.
    """
    if raw.startswith("http://www.opengis.net/def/interpolation/OGC/1/"):
        raw = raw[len("http://www.opengis.net/def/interpolation/OGC/1/"):]
        value = raw.lower()
    else:
        value = raw.lower()

    if value not in SUPPORTED_INTERPOLATIONS:
        raise InterpolationMethodNotSupportedException(
            "Interpolation method '%s' is not supported." % raw
        )
    return value


def parse_range_subset_xml(elem):
    """ Parse a rangesubset structure from the WCS 2.0 XML notation.
    """

    rangesubset = RangeSubset()

    for child in elem:
        item = child[0]
        if item.tag == ns_rsub("RangeComponent"):
            rangesubset.append(item.text)
        elif item.tag == ns_rsub("RangeInterval"):
            rangesubset.append((
                item.findtext(ns_rsub("startComponent")),
                item.findtext(ns_rsub("endComponent"))
            ))

    return rangesubset


def parse_scaleaxis_xml(elem):
    """ Parses the XML notation of a single scale axis.
    """

    axis = elem.findtext(ns_scal("axis"))
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        raw = elem.findtext(ns_scal("scaleFactor"))
        value = float(raw)
    except ValueError:
        InvalidScaleFactorException(raw)

    return ScaleAxis(axis, value)


def parse_scalesize_xml(elem):
    """ Parses the XML notation of a single scale size.
    """

    axis = elem.findtext(ns_scal("axis"))
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        raw = elem.findtext(ns_scal("targetSize"))
        value = int(raw)
    except ValueError:
        InvalidScaleFactorException(raw)

    return ScaleSize(axis, value)


def parse_scaleextent_xml(elem):
    """ Parses the XML notation of a single scale extent.
    """

    axis = elem.findtext(ns_scal("axis"))
    if axis not in all_axes:
        raise ScaleAxisUndefinedException(axis)
    try:
        raw_low = elem.findtext(ns_scal("low"))
        raw_high = elem.findtext(ns_scal("high"))
        low = int(raw_low)
        high = int(raw_high)
    except ValueError:
        InvalidScaleFactorException(raw_high)

    if low >= high:
        raise InvalidScaleExtentException(low, high)

    return ScaleExtent(axis, low, high)


def float_or_star(value):
    """ Parses a string value that is either a floating point value or the '*'
        character. Raises a `ValueError` if no float could be parsed.
    """

    if value == "*":
        return None
    try:
        return float(value)
    except ValueError:
        raise ValueError("could not convert string to float: '%s'" % value)


def parse_quoted_temporal(value):
    """ Parses a quoted temporal value.
    """

    if value == "*":
        return None

    if not value[0] == '"' and not value[-1] == '"':
        raise ValueError(
            "Temporal value needs to be quoted with double quotes."
        )

    return parse_iso8601(value[1:-1])


def get_parser_for_axis(axis):
    """ Returns the correct parsing function for the given axis.
    """

    if is_temporal(axis):
        return parse_quoted_temporal
    else:
        return float_or_star
