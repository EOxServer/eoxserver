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

class Band(object):
    """\
    Band represents a band configuration.
    
    The ``gdal_interpretation`` parameter contains the GDAL
    BandInterpretation value which may be assigned to a band. It may
    be set to one of the following constants defined in
    :mod:`osgeo.gdalconst`:
    
    * ``GCI_Undefined``
    * ``GCI_GrayIndex``
    * ``GCI_PaletteIndex``
    * ``GCI_RedBand``
    * ``GCI_GreenBand``
    * ``GCI_BlueBand``
    * ``GCI_AlphaBand``
    * ``GCI_HueBand``
    * ``GCI_SaturationBand``
    * ``GCI_LightnessBand``
    * ``GCI_CyanBand``
    * ``GCI_MagentaBand``
    * ``GCI_YellowBand``
    * ``GCI_BlackBand``
    
    It defaults to ``GCI_Undefined``.
    """

    def __init__(self,
        name,
        identifier='',
        description='',
        definition='http://opengis.net/def/property/OGC/0/Radiance',
        nil_values=None,
        uom='W.m-2.sr-1.nm-1',
        gdal_interpretation=gdal.GCI_Undefined
    ):
        self.name = name
        self.identifier = identifier
        self.description = description
        self.definition = definition
        if nil_values is None:
            self.nil_values = []
        else:
            self.nil_values = nil_values
        self.uom = uom
        self.gdal_interpretation = gdal_interpretation
    
    def __eq__(self, other):
        if (self.name != other.name
            or self.identifier != other.identifier
            or self.description != other.description
            or self.definition != other.definition
            or self.nil_values != other.nil_values
            or self.uom != other.uom
            or self.gdal_interpretation != other.gdal_interpretation):
            return False
        return True

class NilValue(object):
    """
    This class represents nil values of a coverage band.
    
    The constructor accepts the nil value itself and a reason. The
    reason shall be one of:
    
    * ``http://www.opengis.net/def/nil/OGC/0/inapplicable``
    * ``http://www.opengis.net/def/nil/OGC/0/missing``
    * ``http://www.opengis.net/def/nil/OGC/0/template``
    * ``http://www.opengis.net/def/nil/OGC/0/unknown``
    * ``http://www.opengis.net/def/nil/OGC/0/withheld``
    * ``http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange``
    * ``http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange``
    
    See http://www.opengis.net/def/nil/ for the official description
    of the meanings of these values.
    """
    
    def __init__(self, reason, value):
        self.reason = reason
        self.value = value
        
    def __eq__(self, other):
        if self.reason != other.reason or self.value != other.value:
            return False
        return True

class RangeType(object):
    """
    RangeType contains range type information of a coverage. The
    constructor accepts the mandatory ``name`` and ``data_type``
    parameters as well as an optional ``bands`` parameter. If no bands
    are specified they shall be added with :meth:`addBands`.
    
    The ``data_type`` parameter may be set to one of the following
    constants defined in :mod:`osgeo.gdalconst`:
    
    * ``GDT_Byte``
    * ``GDT_UInt16``
    * ``GDT_Int16``
    * ``GDT_UInt32``
    * ``GDT_Int32``
    * ``GDT_Float32``
    * ``GDT_Float64``
    * ``GDT_CInt16``
    * ``GDT_CInt32``
    * ``GDT_CFloat32``
    * ``GDT_CFloat64``
    """
    
    def __init__(self, name, data_type, bands=None):
        self.name = name
        self.data_type = data_type
        if bands is None:
            self.bands = []
        else:
            self.bands = bands
    
    def __eq__(self, other):
        if (self.name != other.name
            or self.data_type != other.data_type 
            or self.bands != other.bands):
            return False
        return True
    
    def __ne__(self, other):
        return not (self == other)
    
    def addBand(self, band):
        self.bands.append(band)
        
    def getSignificantFigures(self):
        dt = self.data_type
        if dt == gdal.GDT_Byte:
            return 3
        elif dt == gdal.GDT_UInt16 or dt == gdal.GDT_Int16:
            return 5
        elif dt == gdal.GDT_UInt32 or dt == gdal.GDT_Int32:
            return 10
        elif dt == gdal.GDT_Float32:
            return 38
        else:
            raise NotImplemented
        
    def getAllowedValues(self):
        dt = self.data_type
        if dt == gdal.GDT_Byte:
            return (0, 255)
        elif dt == gdal.GDT_UInt16:
            return (0, 65535)
        elif dt == gdal.GDT_Int16:
            return (-32768, 32767)
        elif dt == gdal.GDT_UInt32:
            return (0, 4294967295)
        elif dt == gdal.GDT_Int32:
            return (-2147483648, 2147483647)
        elif dt == gdal.GDT_Float32:
            return (-3.40282e+38, 3.40282e+38)
        else:
            raise NotImplemented
    

# TODO: rewrite this function according to new RangeType definition
def getRangeTypeFromFile(filename):
    ds = gdal.Open(str(filename))
    
    range_type = RangeType("", ds.GetRasterBand(1).DataType)
    
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

        range_type.addBand(Band(
            name, name, description, 
            nil_values=[
                    NilValue(
                        value=band.GetNoDataValue(),
                        reason="http://www.opengis.net/def/nil/OGC/1.0/unknown"
                    )
                ],
                gdal_interpretation = color_intp
            )
        )
         
    return range_type
