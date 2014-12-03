#-------------------------------------------------------------------------------
#
# Project: EOxServer <http://eoxserver.org>
# Authors: Stephan Krause <stephan.krause@eox.at>
#          Stephan Meissl <stephan.meissl@eox.at>
#          Martin Paces <martin.paces@eox.at>
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

from django.db import transaction
from eoxserver.contrib import gdal

#TODO: get rid of the W* wrapper classes 
#class WRangeType(object):
#    """
#    RangeType contains range type information of a coverage. The
#    constructor accepts the mandatory ``name`` and ``data_type``
#    parameters as well as an optional ``bands`` parameter. If no bands
#    are specified they shall be added with :meth:`addBands`.
#    """
#    
#    def __init__(self, name, bands=[] ):
#        self.name = name
#        self.bands = bands
#    
#    def __eq__(self, other):
#        if (self.name != other.name
#            or self.bands != other.bands):
#            return False
#        return True
#    
#    def addBand(self, band):
#        "Append a new band to the band list."
#        self.bands.append(band)
#        
#    def asDict( self ):
#        """ return object as a tupe to be passed to JSON serializer """

#        bands = [ band.asDict() for band in self.bands ] 

#        return {    
#            "name" : self.name,
#            "bands" : bands
#        }


#class WBand(object):
#    """\
#    Band represents a band configuration.
#    
#    The ``data_type`` parameter may be set to one of the following
#    constants defined in :mod:`osgeo.gdalconst`:
#    
#    * ``GDT_Byte``
#    * ``GDT_UInt16``
#    * ``GDT_Int16``
#    * ``GDT_UInt32``
#    * ``GDT_Int32``
#    * ``GDT_Float32``
#    * ``GDT_Float64``
#    * ``GDT_CInt16``
#    * ``GDT_CInt32``
#    * ``GDT_CFloat32``
#    * ``GDT_CFloat64``
#    
#    The ``color_interpretation`` parameter contains the GDAL
#    BandInterpretation value which may be assigned to a band. It may
#    be set to one of the following constants defined in
#    :mod:`osgeo.gdalconst`:
#    
#    * ``GCI_Undefined``
#    * ``GCI_GrayIndex``
#    * ``GCI_PaletteIndex``
#    * ``GCI_RedBand``
#    * ``GCI_GreenBand``
#    * ``GCI_BlueBand``
#    * ``GCI_AlphaBand``
#    * ``GCI_HueBand``
#    * ``GCI_SaturationBand``
#    * ``GCI_LightnessBand``
#    * ``GCI_CyanBand``
#    * ``GCI_MagentaBand``
#    * ``GCI_YellowBand``
#    * ``GCI_BlackBand``
#    
#    It defaults to ``GCI_Undefined``.
#    """

#    def __init__(self,
#        name,
#        data_type, 
#        identifier='',
#        description='',
#        definition='http://opengis.net/def/property/OGC/0/Radiance',
#        nil_values=[],
#        uom='W.m-2.sr-1.nm-1',
#        color_interpretation=gdal.GCI_Undefined
#    ):
#        self.name = name
#        self.data_type = data_type
#        self.identifier = identifier
#        self.description = description
#        self.definition = definition
#        self.nil_values = nil_values
#        self.uom = uom
#        self.color_interpretation = color_interpretation

#    def __eq__(self, other):
#        if (self.name != other.name
#            or self.data_type != data_type
#            or self.identifier != other.identifier
#            or self.description != other.description
#            or self.definition != other.definition
#            or self.nil_values != other.nil_values
#            or self.uom != other.uom
#            or self.color_interpretation != other.color_interpretation):
#            return False
#        return True

#    def addNilValue(self, nil_value ):
#        "Append a new nil-value to the band list."
#        self.nil_values.append(nil_value)

#    def asDict( self ):
#        """
#        Return object's data as a dictionary to be passed to a JSON serializer.
#        """

#        return {    
#            "name" : self.name,
#            "data_type" : self.getDataTypeAsString(), 
#            "identifier" : self.identifier,
#            "description" : self.description,
#            "definition" : self.definition,
#            "uom" : self.uom,
#            "nil_values" : [ nv.asDict() for nv in self.nil_values ],
#            "color_interpretation" : self.getColorInterpretationAsString() 
#        }
#    
#    def getDataTypeAsString( self ) : 
#        "Return string representation of the ``data_type``."
#        return gdal.GDT_TO_NAME.get( self.data_type, "Invalid" ) 
#    
#    def getColorInterpretationAsString( self ) : 
#        "Return string representation of the ``color_interpretation``."
#        return gdal.GCI_TO_NAME.get( self.color_interpretation , "Invalid" ) 

#    def getSignificantFigures(self):
#        "Get significant figures of the currently used type."
#        dt = self.data_type
#        if dt == gdal.GDT_Byte:
#            return 3
#        elif dt in ( gdal.GDT_UInt16 , gdal.GDT_Int16 , gdal.GDT_CInt16 ) : 
#            return 5
#        elif dt in ( gdal.GDT_UInt32 , gdal.GDT_Int32 , gdal.GDT_CInt32 ) : 
#            return 10
#        elif dt in ( gdal.GDT_Float32 , gdal.GDT_CFloat32 ) : 
#            return 38
#        elif dt in ( gdal.GDT_Float64 , gdal.GDT_CFloat64 ) : 
#            return 308
#        else: 
#            raise NotImplementedError()
#        
#    def getAllowedValues(self):
#        "Get interval bounds of the currently used type."
#        dt = self.data_type
#        if dt == gdal.GDT_Byte:
#            return (0, 255)
#        elif dt == gdal.GDT_UInt16:
#            return (0, 65535)
#        elif dt in ( gdal.GDT_Int16 , gdal.GDT_CInt32 ) :
#            return (-32768, 32767)
#        elif dt == gdal.GDT_UInt32:
#            return (0, 4294967295)
#        elif dt in ( gdal.GDT_Int32 , gdal.GDT_CInt32 ) :
#            return (-2147483648, 2147483647)
#        elif dt in ( gdal.GDT_Float32 , gdal.GDT_CFloat32 ) : 
#            return (-3.40282e+38, 3.40282e+38)
#        elif dt in ( gdal.GDT_Float64 , gdal.GDT_CFloat64 ) : 
#            return (-1.7976931348623157e+308, 1.7976931348623157e+308)
#        else:
#            raise NotImplementedError()


#class WNilValue(object):
#    """
#    This class represents nil values of a coverage band.
#    
#    The constructor accepts the nil value itself and a reason. The
#    reason shall be one of:
#    
#    * ``http://www.opengis.net/def/nil/OGC/0/inapplicable``
#    * ``http://www.opengis.net/def/nil/OGC/0/missing``
#    * ``http://www.opengis.net/def/nil/OGC/0/template``
#    * ``http://www.opengis.net/def/nil/OGC/0/unknown``
#    * ``http://www.opengis.net/def/nil/OGC/0/withheld``
#    * ``http://www.opengis.net/def/nil/OGC/0/AboveDetectionRange``
#    * ``http://www.opengis.net/def/nil/OGC/0/BelowDetectionRange``
#    
#    See http://www.opengis.net/def/nil/ for the official description
#    of the meanings of these values.

#    Note: the type of the nill value is assumed to be the same 
#    as the one of the associated band.
#    """
#    
#    def __init__(self, reason, value):
#        self.reason = reason
#        self.value = value
#        
#    def __eq__(self, other):
#        if self.reason != other.reason or self.value != other.value:
#            return False
#        return True

#    def asDict( self ):
#        """
#        Return object's data as a dictionary to be passed to a JSON serializer.
#        """

#        return { "reason" : self.reason , "value" : self.value } 


## TODO: rewrite this function according to new RangeType definition
#def getRangeTypeFromFile(filename):
#    """Get range type from the file given by the ``filename``."""
#    ds = gdal.Open(str(filename))
#    
#    range_type = RangeType("", ds.GetRasterBand(1).DataType)
#    
#    for i in range(1, ds.RasterCount + 1):
#        band = ds.GetRasterBand(i)
#        color_intp = band.GetRasterColorInterpretation()
#        if color_intp == gdal.GCI_RedBand:
#            name = "red"
#            description = "Red Band"
#        elif color_intp == gdal.GCI_GreenBand:
#            name = "green"
#            description = "Green Band"
#        elif color_intp == gdal.GCI_BlueBand:
#            name = "blue"
#            description = "Blue Band"
#        else:
#            name = "unknown_band_%d" % i
#            description = "Unknown Band"

#        range_type.addBand(Band(
#            name, name, description, 
#            nil_values=[
#                    NilValue(
#                        value=band.GetNoDataValue(),
#                        reason="http://www.opengis.net/def/nil/OGC/1.0/unknown"
#                    )
#                ],
#                color_interpretation = color_intp
#            )
#        )
#         
#    return range_type

#==============================================================================

from eoxserver.resources.coverages.models import RangeType
from eoxserver.resources.coverages.models import Band
from eoxserver.resources.coverages.models import NilValueSet
from eoxserver.resources.coverages.models import NilValue


def getAllRangeTypeNames() : 
    """Return a list of identifiers of all registered range-types."""

    return [ rec.name for rec in RangeType.objects.all() ] 

def isRangeTypeName( name ) : 
    """
    Check whether there is (``True``) or is not (``False``) a registered 
    range-type with given identifier``name``.
    """

    return ( 0 < RangeType.objects.filter(name=name).count() ) 


def getRangeType( name ) : 
    """ 
    Return range type ``name`` as JSON serializable dictionary. 
    The values are loaded from the DB. If there is no ``RangeType``
    record corresponding to the given name ``None`` is returned.
    """ 

    try: 

        # get range-type record 
        rt = RangeType.objects.get(name=name)

        bands = [] 

        # loop over band records (ordering set in model) 
        for b in rt.bands.all() : 

            nil_values=[]

            if b.nil_value_set:
                # loop over nil values 
                for n in b.nil_value_set.nil_values.all() : 

                    # append created nil-value dictionary
                    nil_values.append( { 'reason': n.reason, 'value': n.raw_value } ) 


            band = { 
                'name'        : b.name,
                'data_type'   : gdal.GDT_TO_NAME.get(b.data_type,'Invalid'), 
                'identifier'  : b.identifier,
                'description' : b.description, 
                'definition'  : b.definition,
                'uom'         : b.uom, 
                'nil_values'  : nil_values,
                'color_interpretation' :
                    gdal.GCI_TO_NAME.get(b.color_interpretation,'Invalid'),
            }
            
            if b.raw_value_min is not None:
                band["value_min"] = b.raw_value_min
            if b.raw_value_max is not None:
                band["value_max"] = b.raw_value_max

            # append created band dictionary
            bands.append(band)

        # return JSON serializable dictionary 
        return { 'name': rt.name, 'bands': bands } 
                
    except RangeType.DoesNotExist : 

        return None 


def setRangeType( rtype ) : 
    """ 
    Insert range type to the DB. The range type record is
    defined by the ``rtype`` which is a dictionaty as returned by 
    ``getRangeType()`` or parsed form JSON.
    """

    # check the input's data type 
    if not isinstance( rtype , dict ) : 

        raise ValueError("Invalid input object type!") 

    # create record 

    with transaction.commit_on_success():

        rt = RangeType.objects.create( name = rtype['name'] )

        # compatibility with old range-type json format
        dtype_global = rtype.get('data_type',None)  

        for idx,band in enumerate(rtype['bands']) : 

            # compatibility with old range-type json format
            dtype = dtype_global if dtype_global else band['data_type']
            cint  = band['gdal_interpretation'] if 'gdal_interpretation' in \
                                    band else band['color_interpretation']
            
            # convert string to gdal code 
            dtype = gdal.NAME_TO_GDT[dtype.lower()]
            cint  = gdal.NAME_TO_GCI[cint.lower()]

            # prepare nil-value set 
            if band['nil_values']:
                nvset = NilValueSet.objects.create( 
                        name = "__%s_%2.2d__"%(rtype['name'],idx),
                        data_type = dtype )  
        
                for nval in band['nil_values'] : 

                    nv = NilValue.objects.create( 
                        reason = nval['reason'],
                        raw_value = str(nval['value']),
                        nil_value_set = nvset )
    
                    # cheking value 
                    tmp = nv.value 
            else:
                nvset = None
    
            bn = Band.objects.create( 
                    index = idx, 
                    name = band['name'],
                    identifier = band['identifier'],
                    data_type = dtype,
                    description = band['description'],
                    definition = band['definition'],
                    uom = band['uom'],
                    color_interpretation = cint,
                    range_type = rt,
                    nil_value_set = nvset,
                    raw_value_min = band.get("value_min"),
                    raw_value_max = band.get("value_max")
                    )
