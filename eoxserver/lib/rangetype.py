#-----------------------------------------------------------------------
# $Id$
#
# This software is named EOxServer, a server for Earth Observation data.
#
# Copyright (C) 2011 EOX IT Services GmbH
# Authors: Stephan Krause, Stephan Meissl
#
# This file is part of EOxServer <http://www.eoxserver.org>.
#
#    EOxServer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    EOxServer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with EOxServer. If not, see <http://www.gnu.org/licenses/>.
#
#-----------------------------------------------------------------------

from osgeo import gdal

class EOxSChannel(object):
    """\
    EOxSChannel represents a channel or band configuration.
    
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
        super(EOxSChannel, self).__init__()
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

class EOxSNilValue(object):
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
            EOxSChannel(
                name=name,
                description=description,
                nil_values=nil_values#,
                #allowed_values_start=allowed_values_start,
                #allowed_values_end=allowed_values_end,
                #allowed_values_significant_figures=allowed_values_significant_figures
            )
        )
    
    return range_type
