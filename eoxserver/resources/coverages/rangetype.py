#-------------------------------------------------------------------------------
# $Id$
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#
#-------------------------------------------------------------------------------
# Copyright (C) 2011 EOX IT Services GmbH
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

from osgeo import gdal

class Channel(object):
    """\
    Channel represents a channel or band configuration.
    
    The fields of EOxSChannel correspond to a subset of the elements of
    the swe:Quantity class of SWE Common 2.0. Notably, the 'optional',
    'updatable', 'referenceFrame' and 'axisID' elements of swe:Quantity
    have been left out; in conformance to SWE Common 2.0, 'optional' and
    'updatable' are considered to be 'false'; 'referenceFrame' and
    'axisID' are not applicable to EO coverages (they would allow to
    interpret the values of the coverage as coordinates w.r.t. a given
    CRS).
    """

    def __init__(self,
        name,
        identifier='',
        description='',
        definition='http://opengis.net/def/property/OGC/0/Radiance',
        quality=None,
        nil_values=[],
        uom='W/cm2',
        allowed_values_start=0,
        allowed_values_end=255,
        allowed_values_significant_figures=3
    ):
        super(Channel, self).__init__()
        self.name = name
        self.identifier = identifier
        self.description = description
        self.definition = definition
        self.quality = quality # currently unused
        self.nil_values = nil_values # an array of EOxSNilValue objects
        self.uom = uom
        self.allowed_values_start = allowed_values_start
        self.allowed_values_end = allowed_values_end
        self.allowed_values_significant_figures = allowed_values_significant_figures

class NilValue(object):
    def __init__(self, reason, value):
        super(EOxSNilValue, self).__init__()
        self.reason = reason
        self.value = value

def getRangeTypeFromFile(filename):
    ds = gdal.Open(str(filename))
    
    range_type = []
    
    for i in range(1, ds.RasterCount + 1):
        band = ds.GetRasterBand(i)
        color_intp = band.GetRasterColorInterpretation()
        if color_intp == gdal.GCI_RedBand:
            name = "red"
            description = "Red Band"
        elif color_intp == gdal.GCI_GreenBand:
            name = "green"
            description = "Green Band"
        elif color_intp == gdal.GCI_BlueBand:
            name = "blue"
            description = "Blue Band"
        else:
            name = "unknown_band_%d" % i
            description = "Unknown Band"

        no_data_value = band.GetNoDataValue()
        nil_values = [EOxSNilValue(
            reason="http://www.opengis.net/def/nil/OGC/1.0/unknown",
            value=no_data_value
        )]

        #allowed_values_start = band.GetMinimum()
        #allowed_values_end = band.GetMaximum()
        #allowed_values_significant_figures = int(math.log10(allowed_values_end)) + 1

        range_type.append(
            Channel(
                name=name,
                description=description,
                nil_values=nil_values#,
                #allowed_values_start=allowed_values_start,
                #allowed_values_end=allowed_values_end,
                #allowed_values_significant_figures=allowed_values_significant_figures
            )
        )
    
    return range_type
